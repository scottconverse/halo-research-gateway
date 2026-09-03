"""Bounded token application for explicit standalone research challenge widgets.

No form submission, hidden client-state traversal, arbitrary JavaScript input,
cookie export, or universal challenge bypass. The caller owns timeout/cleanup.
"""

from __future__ import annotations

import re
from urllib.parse import urldefrag

from selectolax.parser import HTMLParser


class ChallengeTokenError(RuntimeError):
    pass


CHECK_CALLBACK = r"""v => {
    if (location.href.split('#')[0] !== v.url) return false;
    const nodes = [...document.querySelectorAll(v.selector)];
    if (nodes.length !== 1 || nodes[0].getAttribute('data-sitekey') !== v.key ||
        nodes[0].getAttribute('data-callback') !== v.callback) return false;
    let owner = window;
    const parts = v.callback.split('.');
    for (const part of parts.slice(0, -1)) {
        owner = owner?.[part];
        if (!owner) return false;
    }
    return typeof owner?.[parts.at(-1)] === 'function';
}"""

APPLY_TOKEN = r"""v => { // apply-token
    if (location.href.split('#')[0] !== v.url) return false;
    const nodes = [...document.querySelectorAll(v.selector)];
    if (nodes.length !== 1 || nodes[0].getAttribute('data-sitekey') !== v.key ||
        nodes[0].getAttribute('data-callback') !== v.callback) return false;
    let owner = window;
    const parts = v.callback.split('.');
    for (const part of parts.slice(0, -1)) {
        owner = owner?.[part];
        if (!owner) return false;
    }
    const callback = owner?.[parts.at(-1)];
    if (typeof callback !== 'function') return false;
    const root = nodes[0].closest('form') || document;
    for (const field of root.querySelectorAll('input, textarea')) {
        if (field.name === v.field) field.value = v.token;
    }
    callback.call(owner, v.token);
    return true;
}"""

CHALLENGE_CLEARED = """() => {
    if (document.readyState === 'loading') return false;
    const title = document.title.toLowerCase().trim().replace(/\\s+/g, ' ');
    const titles = ['just a moment...', 'just a moment', 'verify you are human',
        'robot check', 'security verification', 'attention required! | cloudflare'];
    return !titles.includes(title) || !document.querySelector(
        'script[src*="/cdn-cgi/challenge-platform/"], form#challenge-form, #cf-challenge-running, '
        + '#challenge-running, iframe[src*="challenges.cloudflare.com"], .g-recaptcha, .h-captcha, .cf-turnstile');
}"""


def describe_widget(html: str) -> dict:
    tree = HTMLParser(html[:1_000_000])
    # A research gate is not permission to submit login, messaging or other forms.
    if tree.css_first('input[type="password"]') or any(
        form.attributes.get("id") != "challenge-form" for form in tree.css("form")
    ):
        raise ChallengeTokenError("CRAWL_CHALLENGE_UNSUPPORTED")
    nodes = tree.css(".cf-turnstile, .g-recaptcha, .h-captcha")
    if len(nodes) != 1:
        raise ChallengeTokenError("CRAWL_CHALLENGE_UNSUPPORTED")
    attrs = nodes[0].attributes
    kind = "turnstile" if "cf-turnstile" in attrs.get("class", "").split() else "recaptcha"
    if kind == "recaptcha" and "g-recaptcha" not in attrs.get("class", "").split():
        raise ChallengeTokenError("CRAWL_CHALLENGE_UNSUPPORTED")
    key, callback = attrs.get("data-sitekey") or "", attrs.get("data-callback") or ""
    if (
        len(callback) > 256
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", key)
        or not re.fullmatch(r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*){0,8}", callback, re.ASCII)
    ):
        raise ChallengeTokenError("CRAWL_CHALLENGE_UNSUPPORTED")
    if any(part in {"__proto__", "prototype", "constructor"} for part in callback.split(".")):
        raise ChallengeTokenError("CRAWL_CHALLENGE_UNSUPPORTED")
    response_field = (
        attrs.get("data-response-field-name", "cf-turnstile-response")
        if kind == "turnstile"
        else "g-recaptcha-response"
    )
    if (
        not response_field
        or len(response_field) > 256
        or any(ord(char) < 32 or ord(char) == 127 for char in response_field)
    ):
        raise ChallengeTokenError("CRAWL_CHALLENGE_UNSUPPORTED")
    metadata = {}
    for attr, field in (("data-action", "action"), ("data-cdata", "cdata")):
        if attrs.get(attr):
            value = attrs[attr]
            if len(value) > 255 or any(ord(char) < 32 for char in value):
                raise ChallengeTokenError("CRAWL_CHALLENGE_UNSUPPORTED")
            metadata[field] = value
    return {
        "key": key,
        "callback": callback,
        "selector": ".cf-turnstile" if kind == "turnstile" else ".g-recaptcha",
        "field": response_field,
        "task_type": "AntiTurnstileTaskProxyLess" if kind == "turnstile" else "ReCaptchaV2TaskProxyLess",
        "solution_field": "token" if kind == "turnstile" else "gRecaptchaResponse",
        "metadata": metadata if kind == "turnstile" else {},
    }


async def solve_widget(page, registry, validate, challenge_page, response, wait_for=None) -> dict:
    html = await page.content()
    if not challenge_page(html, getattr(response, "headers", None)):
        return {}
    if registry.configs["captcha"].provider != "capsolver":
        raise ChallengeTokenError("OPTIONAL_PROVIDER_ADAPTER_NOT_CONFIGURED")
    url = urldefrag(page.url)[0]
    target = await validate(url)
    widget = describe_widget(html)
    values = {**widget, "url": url}
    if not await page.evaluate(CHECK_CALLBACK, values):
        raise ChallengeTokenError("CRAWL_CHALLENGE_UNSUPPORTED")
    task = {"type": widget["task_type"], "websiteURL": url, "websiteKey": widget["key"]}
    if widget["metadata"]:
        task["metadata"] = widget["metadata"]
    reply = await registry.execute("captcha", target.host, task=task)
    result = reply.get("result") if isinstance(reply, dict) else None
    solution = result.get("solution") if isinstance(result, dict) and result.get("status") == "ready" else None
    token = solution.get(widget["solution_field"]) if isinstance(solution, dict) else None
    if not isinstance(token, str) or not re.fullmatch(r"[\x21-\x7e]{1,32768}", token):
        raise ChallengeTokenError("CRAWL_CHALLENGE_SOLUTION_INVALID")
    # Revalidate after the vendor wait, before giving the page its token.
    await validate(urldefrag(page.url)[0])
    status = getattr(response, "status", 200)

    def navigated(new_response):
        nonlocal status
        request = new_response.request
        if request.is_navigation_request() and request.frame == page.main_frame:
            status = new_response.status

    page.on("response", navigated)
    try:
        if not await page.evaluate(APPLY_TOKEN, {**values, "token": token}):
            raise ChallengeTokenError("CRAWL_CHALLENGE_CHANGED")
        # Outer crawl/page deadlines bound this wait; completion alone is not proof.
        await page.wait_for_function(CHALLENGE_CLEARED, timeout=0)
        if challenge_page(await page.content()):
            raise ChallengeTokenError("CRAWL_CHALLENGE_REQUIRED")
        if wait_for:
            await page.wait_for_selector(wait_for, state="attached", timeout=0)
        final_url = urldefrag(page.url)[0]
        await validate(final_url)
        html = await page.content()
        if challenge_page(html):
            raise ChallengeTokenError("CRAWL_CHALLENGE_REQUIRED")
        return {
            "token": token,
            "status": status,
            "applied": True,
            "html": html.replace(token, "[redacted challenge token]"),
            "url": final_url,
        }
    finally:
        page.remove_listener("response", navigated)
