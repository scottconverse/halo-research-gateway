from halo_research_gateway.operator_ui import render_operator


def test_operator_console_has_narrow_gmail_and_structured_github_connection_paths():
    page = render_operator("csrf-secret", {"status": "ok"})
    assert "Use narrow Gmail compose preset" in page
    assert "https://www.googleapis.com/auth/gmail.compose" in page
    assert "GitHub App (read-only research)" in page
    assert "private_key_pem" in page
    assert "contents:read" in page
    assert "GitHub Actions App (issues only)" in page
    assert "issues:write" in page
    assert "csrf-secret" in page
