"""Read-only GitHub canary using the operator's existing gh keyring sign-in.

Credentials stay in memory and are never printed or saved. Uses public sources;
does not create a Gateway connection, change scopes, or write to GitHub.
"""

import asyncio
import json
import subprocess

from halo_research_gateway.providers.github import GitHubProvider


async def main():
    credential = await asyncio.to_thread(
        subprocess.run, ["gh", "auth", "token", "--hostname", "github.com"], capture_output=True, text=True, check=False
    )
    if credential.returncode or not credential.stdout.strip():
        raise RuntimeError("Existing GitHub sign-in unavailable")
    token = credential.stdout.strip()

    class ExistingConnection:
        def list(self):
            return [{"connection_id": "canary-only", "provider": "GitHub", "status": "ready"}]

        def secret(self, connection_id):
            return {"token": token}

    provider = GitHubProvider(ExistingConnection())
    evidence = {}
    discussions = await provider.research("Crawl4AI", None, ["discussions"], None, 2)
    assert discussions.items, "No discussion evidence returned"
    evidence["discussion_search"] = {
        "provider": discussions.provider,
        "urls": [item.url for item in discussions.items],
        "warnings": discussions.warnings,
    }
    print(json.dumps({"discussion_search": evidence["discussion_search"]}), flush=True)
    selected = discussions.items[0]
    thread = await provider.discussion_thread(selected.metadata["repository"], selected.metadata["number"], 5)
    assert thread.items and thread.items[0].content, "Discussion thread content missing"
    evidence["discussion_thread"] = {
        "items": len(thread.items),
        "urls": [item.url for item in thread.items],
        "warnings": thread.warnings,
    }
    print(json.dumps({"discussion_thread": evidence["discussion_thread"]}), flush=True)
    pinned = await provider.research("README", "microsoft/playwright", ["docs"], "main", 1)
    assert pinned.items and pinned.items[0].content, "Ref-pinned evidence missing"
    item = pinned.items[0]
    assert item.metadata["sha"] in item.url and item.metadata["ref"] == "main"
    evidence["ref_pinned_docs"] = {
        "url": item.url,
        "sha": item.metadata["sha"],
        "chars": len(item.content),
        "warnings": pinned.warnings,
    }
    print(json.dumps({"ref_pinned_docs": evidence["ref_pinned_docs"]}), flush=True)
    print("Authenticated GitHub read-only canary PASS", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
