from httpx import AsyncClient


async def test_security_headers_present_on_api_responses(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["permissions-policy"]
    assert response.headers["content-security-policy"] == (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )


async def test_security_headers_exempt_csp_on_docs(client: AsyncClient) -> None:
    response = await client.get("/api/docs")

    assert response.status_code == 200
    assert "content-security-policy" not in response.headers
    # Still gets the non-CSP headers, just not CSP itself.
    assert response.headers["x-content-type-options"] == "nosniff"
