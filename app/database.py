from sqlmodel import SQLModel, create_engine
from app.models import User, ServiceRequest

# sqlite_file_name = "data/database.db"
sqlite_file_name = "data/dummy_database.db"
# sqlite_file_name = "data/test_db.db"

sqlite_url = f"sqlite:///{sqlite_file_name}"
# echo=False stops the console from showing raw SQL commands (cleaner UI)
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)