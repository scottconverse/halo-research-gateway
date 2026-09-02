from halo_research_gateway.operator_ui import render_operator


def test_operator_console_has_research_connections_without_write_presets():
    page = render_operator("csrf-secret", {"status": "ok"})
    assert "gmailPreset" not in page
    assert "gmail.compose" not in page
    assert "GitHub App (read-only research)" in page
    assert "private_key_pem" in page
    assert "contents:read" in page
    assert "GitHub Actions App" not in page
    assert "issues:write" not in page
    assert "csrf-secret" in page
