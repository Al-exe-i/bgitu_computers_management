from utils.file_responses import secure_file_headers


def test_secure_file_headers_prevent_sniffing_and_header_injection() -> None:
    headers = secure_file_headers('photo"\r\nX-Evil: yes.png')

    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Content-Security-Policy"] == "default-src 'none'; sandbox"
    assert "\r" not in headers["Content-Disposition"]
    assert "\n" not in headers["Content-Disposition"]


def test_secure_file_headers_can_force_download() -> None:
    headers = secure_file_headers("report.html", as_attachment=True)

    assert headers["Content-Disposition"].startswith("attachment;")
