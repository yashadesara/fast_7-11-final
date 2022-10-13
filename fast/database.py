from sqlite3 import connect
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@localhost/project"
DATABASE_URL = "mysql+mysqlconnector://root@localhost/project"

# engine = create_engine(DATABASE_URL, connect_args={"ssl": False})
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, bind=engine)

Base = declarative_base()