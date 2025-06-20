# tests/test_integration_routes.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

transport = ASGITransport(app=app)
BASE_URL = "http://test"

@pytest.mark.asyncio
async def test_home_page():
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        assert "<h1>Home page</h1>" in res.text

@pytest.mark.asyncio
async def test_create_and_get_category():
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        res = await ac.post("/category", json={"name": "Science"})
        assert res.status_code == 201
        category_id = res.json()["id"]

        res_get = await ac.get(f"/category/{category_id}")
        assert res_get.status_code == 200
        assert res_get.json()["name"] == "Science"

@pytest.mark.asyncio
async def test_create_video_and_fetch():
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        await ac.post("/category", json={"name": "Tech"})
        res = await ac.post("/video", json={
            "title": "FastAPI Video",
            "youtube_code": "abc123",
            "category_id": 1
        })
        assert res.status_code == 201
        video_id = res.json()["id"]

        res_get = await ac.get(f"/video/{video_id}")
        assert res_get.status_code == 200
        assert res_get.json()["title"] == "FastAPI Video"

@pytest.mark.asyncio
async def test_get_all_videos():
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        res = await ac.get("/video")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

@pytest.mark.asyncio
async def test_categorized_videos():
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        res = await ac.get("/categorized_video")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
