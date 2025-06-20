import pytest
from sqlmodel import Session, create_engine, SQLModel
from models import Category, Video
from main import is_category_id, is_category_name, is_active_video, count_videos_in_category

# In-memory test DB
test_engine = create_engine("sqlite:///:memory:")

@pytest.fixture(scope="module")
def session():
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session

@pytest.mark.unit
@pytest.mark.asyncio
async def test_is_category_id_true(session):
    category = Category(name="Test")
    session.add(category)
    session.commit()
    assert await is_category_id(category.id, session) is True

@pytest.mark.unit
@pytest.mark.asyncio
async def test_is_category_id_false(session):
    assert await is_category_id(999, session) is False

@pytest.mark.unit
@pytest.mark.asyncio
async def test_is_category_name_true(session):
    category = Category(name="UniqueName")
    session.add(category)
    session.commit()
    assert await is_category_name("UniqueName", session) is True

@pytest.mark.unit
@pytest.mark.asyncio
async def test_is_category_name_false(session):
    assert await is_category_name("DoesNotExist", session) is False

@pytest.mark.unit
@pytest.mark.asyncio
async def test_is_active_video_true(session):
    category = Category(name="WithVideo")
    session.add(category)
    session.commit()
    video = Video(title="Vid", youtube_code="abc123", category_id=category.id)
    session.add(video)
    session.commit()
    assert await is_active_video(video.id, session) is True

@pytest.mark.unit
@pytest.mark.asyncio
async def test_is_active_video_false(session):
    assert await is_active_video(12345, session) is False

@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_videos_in_category(session):
    category = Category(name="CountTest")
    session.add(category)
    session.commit()

    video = Video(title="V1", youtube_code="xyz123", category_id=category.id)
    session.add(video)
    session.commit()

    count = await count_videos_in_category(category.id, session)
    assert count == 1
