from httpx import AsyncClient

from tests.integration.helpers import auth_headers, signup


async def test_get_my_company(client: AsyncClient) -> None:
    data = await signup(client, email="company-test@acme.com", company_name="Widgets Inc")
    response = await client.get("/api/v1/companies/me", headers=auth_headers(data["access_token"]))
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Widgets Inc"
    assert body["slug"] == "widgets-inc"
