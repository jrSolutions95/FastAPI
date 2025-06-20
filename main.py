from datetime import datetime, timezone
from fastapi import FastAPI, Form, Request,status,HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Field, create_engine, Session, select
from models import Category, CategoryBase,VideoBase, Video,CategorizedVideos
from database import engine
from typing import List
import uvicorn
# We need all of the imports above to be able to use the database and the models

#Define main app name and database session name¨
app = FastAPI()
session = Session(bind=engine)#This is a sqlmodel session binds to the engine

#For templating
app.mount('/static',StaticFiles(directory='static'),name='static')#Mounting the static folder to the /static path
templates = Jinja2Templates(directory='templates')#Mounting the templates folder to the /templates path
#Routes
#Root folder (home page)
#Måbruke async fordi fastapi bruker asci servere som er asynkrone
@app.get("/",response_class=HTMLResponse)#Hvis vi vil returnere html, så må vi bruke response_class=HTMLResponse, men stnadard er JSON
async def home():#Funksjonsnavnet her vises i documentasjonen
    return """
    <h1>Home page</h1>
    <a href='http://127.0.0.1:8000/docs'>http://127.0.0.1:8000/docs</a>
    <p>
    <a href='http://127.0.0.1:8000/get_form_video_add'>Add a video</a>
    </p>"""

#region video_routes

#Post a new video
@app.post("/video", status_code=status.HTTP_201_CREATED)#Status code 201 betyr at noe er lagt til, husk importer status
async def post_a_video(video: VideoBase):#Type hint VideoBase, brukes fordi vil se schemaet for videobase i apiet, og ikke video#endregion video_routes
    #new_video = Video.from_orm(video)
    new_video = Video.model_validate(video)
    #Make sure new video has a valid category
    if not await is_category_id(new_video.category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    # Post the video
    with Session(engine) as session:
        session.add(new_video)
        session.commit()
        session.refresh(new_video)
    return new_video
# Delete one vido bu changing is_active to false
@app.delete("/video/{video_id}")
async def delete_a_video(video_id: int):
    if not await is_active_video(video_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    with Session(engine) as session:
        #Get the categegiry ti delete
        video = session.get(Video, video_id)
        # Set is active to false
        video.is_active = False
        video.date_last_changed = datetime.now(timezone.utc)
        session.commit()
    return {"Deleted": video_id}

# UnDelete one video bu changing is_active to true
@app.delete("/undelete/{video_id}")
async def undelete_a_video(video_id: int):
    with Session(engine) as session:
        #Get the categegiry ti delete
        video = session.get(Video, video_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
        # Set is active to True
        video.is_active = True
        video.date_last_changed = datetime.now(timezone.utc)
        session.commit()
    return {"Restored": video_id}


#Get all videos, dette punktet håndterer get requests som kommer inn med /Videos
@app.get("/video",response_model=List[Video])
async def get_all_videos():
    with Session(engine) as session:
        statement = select(Video).where(Video.is_active == True).order_by(Video.title)#Sorterer etter navn fallende A-Å
        result = session.exec(statement)
        all_videos = result.all()
    return all_videos

# Get one video, but onluy if it is active
@app.get("/video/{video_id}",response_model=VideoBase)
async def get_a_video(video_id: int):
    #Return errfor if no acrtive video with that id
    if not await is_active_video(video_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active video with that id")
    with Session(engine) as session:
        video = session.get(Video, video_id)
    return video

# Update one video
@app.put("/video/{video_id}",response_model=VideoBase)
async def update_a_video(video_id: int,updated_video: VideoBase):
    #Return errfor if no acrtive video with that id
    if not await is_active_video(video_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such video")
    if not await is_category_id(updated_video.category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    with Session(engine) as session:
        original_video = session.get(Video, video_id)
        #Loop thorough and update the fields
        video_dict = updated_video.model_dump(exclude_unset=True)#Only values in the model that are passed in are updated, not all values
        for key,value in video_dict.items():
            setattr(original_video,key,value)#Oppdaterer original video med de nye verdiene
        #Loop dosent do date last changes, so we do it here
        original_video.date_last_changed = datetime.now(timezone.utc)
        session.commit()
        #After refresh we can return the updated video
        session.refresh(original_video)
    return original_video


# endregion video_routes
# region category_routes


#Get all categories, dette punktet håndterer get requests som kommer inn med /Category
@app.get("/category",response_model=List[Category])#List[Category] betyr at vi forventer en liste med kategorier, gir brukeren mer info om hva de skal forvente
async def get_all_categories():
    with Session(engine) as session:
        statement = select(Category).order_by(Category.name)#Sorterer etter navn fallende A-Å
        result = session.exec(statement)
        all_categories = result.all()
    return all_categories

#Post a new category 
@app.post("/category", status_code=status.HTTP_201_CREATED)#Status code 201 betyr at noe er lagt til, husk importer status
async def post_a_category(category: CategoryBase):#Type hint CategoryBase, brukes fordi vil se schemaet for categorybase i apiet, og ikke category
    if await is_category_name(category.name):#Sjekker om kategorien allerede eksisterer
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Category already exists")
    new_category = Category(name=category.name)#Vi lager en ny kategori med navnet som kommer inn
    with Session(engine) as session:#With fungerer som en transaction, og lukker automatisk sessionen etter at vi er ferdig
        #See if that category already exists in the table, looking on the serverside
        statement = select(Category).where(Category.name == category.name)#Vi lager en select statement som ser etter en kategori med samme navn
        #reject if name already in use
        session.add(new_category)
        session.commit()#Putter det i databasen
        session.refresh(new_category)#Updaterer objektet med det som er i databasen
    return new_category

#Get a specific category #Also an example of serverside validation
@app.get("/category/{category_id}",response_model=Category)
async def get_a__category(category_id: int):#Type hint
    with Session(engine) as session:
        #Alternative syntax when getting one row by id
        category = session.get(Category, category_id)
        #Return error if no such category
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category    
    
#Update a specific category
@app.put("/category/{category_id}",response_model=Category)
async def update_a_category(category_id: int,category: CategoryBase):
    if not await is_category_id(category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    with Session(engine) as session:
        #Get current category ojbect from table
        current_category = session.get(Category, category_id)
        #Replace current category name with the one that is passed in
        current_category.name = category.name
        session.add(current_category)
        session.commit()
        session.refresh(current_category)
    return current_category


#Delete a specific category hello
@app.delete("/category/{category_id}")
async def delete_a_category(category_id: int):
    if not await is_category_id(category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    #Dont allow them to delete category if it contains active videos
    if await count_videos_in_category(category_id) > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Category contains active videos")
    with Session(engine) as session:
        #Get the categegiry ti delete
        category = session.get(Category, category_id)
        # Delete the category
        session.delete(category)
        session.commit()
    return {"Deleted": category_id}

# endregion category_routes
# region validators

#Returns true if category exists, otherwise return False 
async def is_category_id(category_id: int):
    if not session.get(Category, category_id):
        return False #there is no category id
    return True

# Returns true if category name exists, otherwise return False
async def is_category_name(category_name: str):
    if session.exec(
        select(Category).where(Category.name == category_name)).one_or_none():
        return True #there is no category id
    return False

async def is_active_video(video_id: int):
    if session.exec(
        # Select where video id is valid and id_active is true
        select(Video).where(Video.id == video_id,Video.is_active == True)).one_or_none():
        return True #there is no category id
    return False
async def count_videos_in_category(category_id: int):
    rows=session.exec(
        select(Video.category_id).where(Video.category_id == category_id).where(Video.is_active == True)
    ).all()
    return len(rows)
# endregion validators

# region joins
@app.get("/categorized_video",response_model=List[CategorizedVideos])#Her måtte responsmodellen med for at det skulle fungere
async def get_categorized_video():
    # Get all active videos, and include category name (not the id)
    cat_videos = session.exec(
        select(Video.id,Category.name.label('category'), Video.title, Video.youtube_code).join(Category).where(Video.is_active).order_by(Category.name,Video.title)
    ).all()
    return cat_videos

# endregion joins

# region forms

# Send an HTML table of videos with click-to-edit icon
@app.get('/get_form_video_list', response_class=HTMLResponse)
async def get_form_video_list(request:Request):
    # Get all active videos, along with the category name
    active_videos = session.exec(
        select(
            Video.id, Video.title, Video.youtube_code, Category.name.label('category')
        ).join(Category).where(Video.is_active).order_by(Video.title)
    ).all()
    context = {'request': request, 'videos':active_videos, 'page_title':'Videos'}
    return templates.TemplateResponse('form_list_videos.html', context)

# Send empty form for entering a new video
@app.get("/get_form_video_add",response_class=HTMLResponse)
async def get_form_video_add(request: Request):
    # Get a list of categories for the dropdown list on the form
    categories = session.exec(select(Category)).all()
    context = {"request":request, 'categories':categories}
    return templates.TemplateResponse("form_add_video.html",context)
#Den over passer data inn til templatene med med context slik at den kan brukes inne i html

#Accept data from form_video_add and add to the database

@app.post("/submit_form_video_add")
async def submit_form_video_add(title:str=Form(),youtube_code=Form(),category_id=Form()):
    new_video = Video(title=title,youtube_code=youtube_code,category_id=int(category_id))
    with Session(engine) as session:
        session.add(new_video)
        session.commit()
        session.refresh(new_video)
    #No good option for return, at this point
    return new_video


# endregion forms

# For debugging with breakpoints in Vscode
if __name__ == "__main__":
   uvicorn.run(app, host='0.0.0.0',port=8000)