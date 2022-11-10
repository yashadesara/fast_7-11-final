from sqlalchemy import Column, Integer, String, ForeignKey
from fastapi import FastAPI
from database import Base,engine
from sqlalchemy.orm import relationship

from fastapi import FastAPI

app = FastAPI()


# create category table
class category(Base):
    __tablename__ = "category"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    image = Column(String(250), index=True)

    items = relationship("item", back_populates="cat",passive_deletes=True) #category has relation with item


# create item table
class item(Base):
    __tablename__ = "item"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), unique=True, index=True)
    description = Column(String(250), index=True)
    image = Column(String(250), index=True)
    ingredients = Column(String(550), index=True)
    instruction = Column(String(250), index=True)
    cat_id = Column(Integer, ForeignKey("category.id",ondelete='CASCADE'))

    cat = relationship("category", back_populates="items") #item has relation with category

    feed = relationship("feedback", back_populates="items",passive_deletes=True) #item has relation with feedback


# create user table
class user(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True) 
    email = Column(String(50), unique=True, index=True) 
    password = Column(String(200), index=True) 
    username = Column(String(50), index=True) 
    user_type = Column(String(10), index=True) 

    feed = relationship("feedback", back_populates="users") #user has relation with feedback


# create feedback table
class feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True) 
    r_id = Column(Integer, ForeignKey("item.id", ondelete='CASCADE')) 
    u_id = Column(Integer, ForeignKey("user.id", ondelete='CASCADE')) 
    description = Column(String(500), index=True)
    rating = Column(Integer, index=True)

    users = relationship("user", back_populates="feed")#feedback has relation with user

    items = relationship("item", back_populates="feed")#feedback has relation with item



a = Base.metadata.create_all(bind=engine)
