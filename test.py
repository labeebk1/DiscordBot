
from sqlalchemy import DDL
from sqlalchemy import create_engine
from sqlalchemy.orm import Session



# Load Database
engine = create_engine('sqlite:///gamble.db', echo=False)
session = Session(engine)


add_column = DDL("ALTER TABLE users ADD COLUMN casino int REFERENCES casino")
engine.execute(add_column)