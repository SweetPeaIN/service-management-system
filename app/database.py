from sqlmodel import SQLModel, create_engine

sqlite_file_name = "data/database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# echo=False stops the console from showing raw SQL commands (cleaner UI)
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)