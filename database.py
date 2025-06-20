from sqlmodel import SQLModel, Field, create_engine, Session 

#if you have models in models.py, from which you want to create tables, import them here
import models


#Define the databese file name
sqllite_filename = "database.db"

#Create a sqlite database for development
sqllite_url = f"sqlite:///{sqllite_filename}"

#The name enigne will refer to that database engine.
engine = create_engine(sqllite_url, echo=True)#Echo gir feedback, men kun for bruk i dev ikke prod

#The database.db file wont be created until you actualle execute database.py
if __name__ == "__main__":
    #Creates database.db if it dosent already exist
    SQLModel.metadata.create_all(engine)#Kjører bare denne dersom den ikke eksisterer allerede