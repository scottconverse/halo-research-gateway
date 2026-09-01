"""Operator-only OAuth Authorization Code + PKCE connection flow."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import secrets
import time
import urllib.parse
import uuid

import httpx

from ..providers.http_fetch import PinnedTransport, resolve_public
from ..security import validate_url


class OAuthFlowError(RuntimeError):
    pass


class OAuthManager:
    def __init__(self, connections, timeout_seconds: int = 300, clock=None) -> None:
        self.connections = connections
        self.timeout_seconds = timeout_seconds
        self.clock = clock or time.time
        self._flows: dict[str, dict] = {}
        self._refresh_locks: dict[str, asyncio.Lock] = {}

    async def begin(
        self,
        *,
        provider: str,
        label: str,
        authorization_endpoint: str,
        token_endpoint: str,
        client_id: str,
        scopes: list[str],
        client_secret: str | None = None,
        extra_authorize: dict[str, str] | None = None,
    ) -> dict:
        validate_url(authorization_endpoint)
        validate_url(token_endpoint)
        reserved = {
            "response_type",
            "client_id",
            "redirect_uri",
            "scope",
            "state",
            "code_challenge",
            "code_challenge_method",
        }
        if reserved & set(extra_authorize or {}):
            raise OAuthFlowError("OAUTH_RESERVED_PARAMETER")
        flow_id = str(uuid.uuid4())
        state = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
        future = asyncio.get_running_loop().create_future()

        async def callback(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            try:
                request = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 5)
                first = request.split(b"\r\n", 1)[0].decode("ascii", errors="replace")
                method, target, _ = first.split(" ", 2)
                parsed_target = urllib.parse.urlsplit(target)
                if method != "GET" or parsed_target.path != "/oauth/callback":
                    raise OAuthFlowError("OAUTH_CALLBACK_INVALID")
                query = urllib.parse.parse_qs(parsed_target.query)
                received_state = (query.get("state") or [""])[0]
                if not hmac.compare_digest(received_state, state):
                    raise OAuthFlowError("OAUTH_STATE_MISMATCH")
                code = (query.get("code") or [""])[0]
                error = (query.get("error") or [None])[0]
                if not code and not error:
                    raise OAuthFlowError("OAUTH_CODE_MISSING")
                if not future.done():
                    future.set_result((code, error))
                body = b"Halo Research Gateway received the authorization response. You may close this tab."
                status = b"200 OK"
            except Exception as exc:
                if not future.done():
                    future.set_exception(exc)
                body = b"Halo Research Gateway rejected the authorization response."
                status = b"400 Bad Request"
            writer.write(
                b"HTTP/1.1 "
                + status
                + b"\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: "
                + str(len(body)).encode()
                + b"\r\nConnection: close\r\n\r\n"
                + body
            )
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(callback, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        redirect_uri = f"http://127.0.0.1:{port}/oauth/callback"
        parameters = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            **(extra_authorize or {}),
        }
        authorization_url = (
            authorization_endpoint
            + ("&" if "?" in authorization_endpoint else "?")
            + urllib.parse.urlencode(parameters)
        )
        self._flows[flow_id] = {
            "provider": provider,
            "label": label,
            "token_endpoint": token_endpoint,
            "client_id": client_id,
            "client_secret": client_secret,
            "scopes": sorted(set(scopes)),
            "verifier": verifier,
            "redirect_uri": redirect_uri,
            "future": future,
            "server": server,
            "expires_at": int(self.clock()) + self.timeout_seconds,
        }
        return {
            "flow_id": flow_id,
            "provider": provider,
            "label": label,
            "scopes": sorted(set(scopes)),
            "authorization_url": authorization_url,
            "redirect_uri": redirect_uri,
            "expires_in_seconds": self.timeout_seconds,
        }

    async def complete(self, flow_id: str) -> dict:
        flow = self._flows.pop(flow_id, None)
        if flow is None:
            raise OAuthFlowError("OAUTH_FLOW_NOT_FOUND")
        try:
            code, error = await asyncio.wait_for(flow["future"], max(1, flow["expires_at"] - int(self.clock())))
            if error:
                raise OAuthFlowError(f"OAUTH_PROVIDER_ERROR/{error}")
            payload = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": flow["redirect_uri"],
                "client_id": flow["client_id"],
                "code_verifier": flow["verifier"],
            }
            if flow["client_secret"]:
                payload["client_secret"] = flow["client_secret"]
            tokens = await self._token_request(flow["token_endpoint"], payload)
            if not tokens.get("access_token"):
                raise OAuthFlowError("OAUTH_TOKEN_MISSING")
            secret = {
                "access_token": str(tokens["access_token"]),
                "token_type": str(tokens.get("token_type", "Bearer")),
                "client_id": flow["client_id"],
                "token_endpoint": flow["token_endpoint"],
            }
            for key in ("refresh_token", "expires_in", "scope"):
                if tokens.get(key) is not None:
                    secret[key] = str(tokens[key])
            if flow["client_secret"]:
                secret["client_secret"] = flow["client_secret"]
            return self.connections.create(flow["provider"], flow["label"], "oauth", secret, flow["scopes"])
        finally:
            flow["server"].close()
            await flow["server"].wait_closed()

    async def refresh(self, connection_id: str) -> dict:
        lock = self._refresh_locks.setdefault(connection_id, asyncio.Lock())
        async with lock:
            secret = self.connections.secret(connection_id)
            if not secret.get("refresh_token"):
                raise OAuthFlowError("OAUTH_REFRESH_UNAVAILABLE")
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": secret["refresh_token"],
                "client_id": secret["client_id"],
            }
            if secret.get("client_secret"):
                payload["client_secret"] = secret["client_secret"]
            tokens = await self._token_request(secret["token_endpoint"], payload)
            if not tokens.get("access_token"):
                raise OAuthFlowError("OAUTH_TOKEN_MISSING")
            secret.update({str(k): str(v) for k, v in tokens.items() if v is not None})
            self.connections.replace_secret(connection_id, secret)
            return self.connections.get(connection_id)

    @staticmethod
    async def _token_request(url: str, payload: dict[str, str]) -> dict:
        target = validate_url(url)
        address = await resolve_public(target)
        async with httpx.AsyncClient(
            transport=PinnedTransport(target, address), trust_env=False, follow_redirects=False, timeout=30
        ) as client:
            response = await client.post(url, data=payload, headers={"Accept": "application/json"})
            response.raise_for_status()
            return response.json()
