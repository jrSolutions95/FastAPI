"""  #stort sett samme kodes finnes her: https://sqlmodel.tiangolo.com/#create-a-sqlmodel-model
from typing import Optional

from sqlmodel import Field, SQLModel

# Category class (and Sql table)
class Category(SQLModel, table=True):#Vi bruker dete som en tabell i databasen /vi arver av SQLModel og setter table=True, fordi dette er en database tabell
    id: Optional[int] = Field(default=None, primary_key=True)#På pyhton side er det optinal med int, men i databasen er det en primary key, Field er ting som bare svarer til databasen, default=None vi kan sette den inn uten en key fra python, men jeg tror det fikses av Field
    name: str = Field(min_length=3, max_length=15,index=True)#navn på kategorien, kan deefinere andre parametere, index=True betyr at vi kan søke på det, min_length=3, max_length=15 betyr at det må være mellom 3 og 15 tegn,unique=True betyr at det må være unikt
 """
#This makes the validation work otherwise it will not work
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel 
#Av en eller annen grunn måtte dette til for å fungere ordentlig


#VideoBase (main user fields for Video table)
class VideoBase(SQLModel):
    title: str = Field(min_length=1, max_length=128, index=True)
    youtube_code: str =Field(regex='.{4,11}') #what is regex? #regex er en måte å validere input på, her sier vi at det må være  mellom4-11 tegn, og at det kan være hva som helst
    # Link to Category model
    category_id: int = Field(foreign_key='category.id')#Vi setter foreign key til category.id, fordi vi vil at det skal være en referanse til id feltet i category tabellen

# Video class (and SQL table) inherits from VideoBase
class Video(VideoBase, table=True):#Table tru fordi da lager den tableen når vi kjører
    id: Optional[int] = Field(primary_key=True, default=None)
    # is_active is true for normal rows, False(0) for deleted rows
    is_active: Optional[bool] = Field(default=True)
    # Date this row was created, defaults to utc now
    date_created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)#ellers datetime.utcnow
    # Date this row was last updated, defaults to utc now
    date_last_changed: Optional[datetime] = Field(default=None, nullable=True)
#Categorized videos class
class CategorizedVideos(SQLModel):#Viktig for å få responsen til å bli riktig, den funket ikke uten denne
    id:int
    category: str
    title: str
    youtube_code: str


class CategoryBase(SQLModel):
    name: str = Field(min_length=3, max_length=15, index=True)

# Category class (and SQL table) inherits from CategoryBase arver av CategoryBase, arver alstå det ene fletet
class Category(CategoryBase, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
#Delt i to fordi vi vil bruke CategoryBase i post og put modellene våre, da trenger vi ikke id feltet