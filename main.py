from datetime import datetime, timezone
from fastapi import FastAPI, Form, Request, status, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select, Session
from models import Category, CategoryBase, VideoBase, Video, CategorizedVideos
from database import get_db
from typing import List
import uvicorn

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <h1>Home page</h1>
    <a href='/docs'>/docs</a>
    <p>
    <a href='/get_form_video_add'>Add a video</a>
    </p>
    """
# region validators
async def is_category_id(category_id: int, db: Session):
    return db.get(Category, category_id) is not None

async def is_category_name(category_name: str, db: Session):
    return db.exec(select(Category).where(Category.name == category_name)).one_or_none() is not None

async def is_active_video(video_id: int, db: Session):
    return db.exec(select(Video).where(Video.id == video_id, Video.is_active == True)).one_or_none() is not None

async def count_videos_in_category(category_id: int, db: Session):
    rows = db.exec(select(Video.category_id).where(Video.category_id == category_id, Video.is_active == True)).all()
    return len(rows)
# endregion

# region video_routes
@app.post("/video", status_code=status.HTTP_201_CREATED)
async def post_a_video(video: VideoBase, db: Session = Depends(get_db)):
    new_video = Video.from_orm(video)
    if not await is_category_id(new_video.category_id, db):
        raise HTTPException(status_code=404, detail="Category not found")
    db.add(new_video)
    db.commit()
    db.refresh(new_video)
    return new_video

@app.delete("/video/{video_id}")
async def delete_a_video(video_id: int, db: Session = Depends(get_db)):
    if not await is_active_video(video_id, db):
        raise HTTPException(status_code=404, detail="Video not found")
    video = db.get(Video, video_id)
    video.is_active = False
    video.date_last_changed = datetime.now(timezone.utc)
    db.commit()
    return {"Deleted": video_id}

@app.delete("/undelete/{video_id}")
async def undelete_a_video(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    video.is_active = True
    video.date_last_changed = datetime.now(timezone.utc)
    db.commit()
    return {"Restored": video_id}

@app.get("/video", response_model=List[Video])
async def get_all_videos(db: Session = Depends(get_db)):
    statement = select(Video).where(Video.is_active == True).order_by(Video.title)
    result = db.exec(statement)
    return result.all()

@app.get("/video/{video_id}", response_model=VideoBase)
async def get_a_video(video_id: int, db: Session = Depends(get_db)):
    if not await is_active_video(video_id, db):
        raise HTTPException(status_code=404, detail="No active video with that id")
    video = db.get(Video, video_id)
    return video

@app.put("/video/{video_id}", response_model=VideoBase)
async def update_a_video(video_id: int, updated_video: VideoBase, db: Session = Depends(get_db)):
    if not await is_active_video(video_id, db):
        raise HTTPException(status_code=404, detail="No such video")
    if not await is_category_id(updated_video.category_id, db):
        raise HTTPException(status_code=404, detail="Category not found")
    original_video = db.get(Video, video_id)
    video_dict = updated_video.model_dump(exclude_unset=True)
    for key, value in video_dict.items():
        setattr(original_video, key, value)
    original_video.date_last_changed = datetime.now(timezone.utc)
    db.commit()
    db.refresh(original_video)
    return original_video
# endregion

# region category_routes
@app.get("/category", response_model=List[Category])
async def get_all_categories(db: Session = Depends(get_db)):
    statement = select(Category).order_by(Category.name)
    result = db.exec(statement)
    return result.all()

@app.post("/category", status_code=status.HTTP_201_CREATED)
async def post_a_category(category: CategoryBase, db: Session = Depends(get_db)):
    if await is_category_name(category.name, db):
        raise HTTPException(status_code=403, detail="Category already exists")
    new_category = Category(name=category.name)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@app.get("/category/{category_id}", response_model=Category)
async def get_a_category(category_id: int, db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@app.put("/category/{category_id}", response_model=Category)
async def update_a_category(category_id: int, category: CategoryBase, db: Session = Depends(get_db)):
    if not await is_category_id(category_id, db):
        raise HTTPException(status_code=404, detail="Category not found")
    current_category = db.get(Category, category_id)
    current_category.name = category.name
    db.add(current_category)
    db.commit()
    db.refresh(current_category)
    return current_category

@app.delete("/category/{category_id}")
async def delete_a_category(category_id: int, db: Session = Depends(get_db)):
    if not await is_category_id(category_id, db):
        raise HTTPException(status_code=404, detail="Category not found")
    if await count_videos_in_category(category_id, db) > 0:
        raise HTTPException(status_code=403, detail="Category contains active videos")
    category = db.get(Category, category_id)
    db.delete(category)
    db.commit()
    return {"Deleted": category_id}
# endregion

# region joins
@app.get("/categorized_video", response_model=List[CategorizedVideos])
async def get_categorized_video(db: Session = Depends(get_db)):
    cat_videos = db.exec(
        select(Video.id, Category.name.label('category'), Video.title, Video.youtube_code)
        .join(Category)
        .where(Video.is_active)
        .order_by(Category.name, Video.title)
    ).all()
    return cat_videos
# endregion

# region forms
@app.get('/get_form_video_list', response_class=HTMLResponse)
async def get_form_video_list(request: Request, db: Session = Depends(get_db)):
    active_videos = db.exec(
        select(
            Video.id, Video.title, Video.youtube_code, Category.name.label('category')
        ).join(Category).where(Video.is_active).order_by(Video.title)
    ).all()
    context = {'request': request, 'videos': active_videos, 'page_title': 'Videos'}
    return templates.TemplateResponse('form_list_videos.html', context)

@app.get("/get_form_video_add", response_class=HTMLResponse)
async def get_form_video_add(request: Request, db: Session = Depends(get_db)):
    categories = db.exec(select(Category)).all()
    context = {"request": request, 'categories': categories}
    return templates.TemplateResponse("form_add_video.html", context)

@app.post("/submit_form_video_add")
async def submit_form_video_add(
    title: str = Form(), youtube_code: str = Form(), category_id: int = Form(), db: Session = Depends(get_db)):
    new_video = Video(title=title, youtube_code=youtube_code, category_id=int(category_id))
    db.add(new_video)
    db.commit()
    db.refresh(new_video)
    return new_video
# endregion

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)