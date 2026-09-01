# Source selection

Use the least expensive tool that can produce the required evidence.

| Need | Tool |
|---|---|
| Find current public sources | `web_search` |
| Read a known ordinary page | `web_fetch` |
| Render JavaScript, interact, or traverse bounded pages | `web_crawl` |
| Search or read Reddit | `reddit_search`, `reddit_thread` |
| Extract a PDF or supported document | `document_extract` |
| Collect a bounded multi-source packet | `deep_research` or `research_job` |
| Find GitHub repositories, code, issues, or releases | `github_research` |
| Retrieve captions/transcripts | `transcript_fetch` |
| Search/read technical discussions | `community_search`, `community_thread` |
| Read an exact operator-allowed local service | `local_fetch`, `local_crawl` |
| Prepare/execute a consequential action | `web_action_prepare`, then operator approval, then `web_action_execute` |

Prefer official documentation, standards, first-party repositories, original papers, and direct records for factual claims. Use multiple independent sources for disputed, time-sensitive, high-stakes, or consequential conclusions. Search results are discovery leads; fetch or crawl the selected source before relying on its content.

Use `web_crawl` when direct fetch lacks rendered text or an ordinary interaction is required. Use a managed profile only when the operator has deliberately configured it. Route Reddit through its dedicated queue instead of general search/fetch.
