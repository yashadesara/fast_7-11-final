import shutil
from unittest import skip
from fastapi.security import OAuth2PasswordBearer
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, Depends, UploadFile, File, Form
from collections import defaultdict
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from matplotlib.pyplot import title
from pydantic import BaseModel
from requests import request
from sqlalchemy import true
from create_db import category as c
from create_db import item as i
from create_db import user as u
from create_db import feedback as f
from typing import List, Union, Optional
from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from fastapi import FastAPI, Depends, HTTPException, status
from passlib.hash import bcrypt


app = FastAPI()

JWT_SECRET = "myjwtsecret"

app.mount("/static", StaticFiles(directory="static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class userForFeed(BaseModel):
    username: str
    email: str

    class Config:
        orm_mode = True


class itemForFeed(BaseModel):
    title: str

    class Config:
        orm_mode = True


class categoryForItem(BaseModel):
    name: Optional[str]

    class Config:
        orm_mode = True


class categoryForBodyAdd(BaseModel):
    name: Union[str, None] = None
    image: UploadFile

    class Config:
        orm_mode = True


class categoryForAdd(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class feed_user_name(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True


class feedback(BaseModel):
    id: Optional[int]
    r_id: Union[int, None] = None
    u_id: Union[int, None] = None
    description: Union[str, None] = None
    rating: Union[int, None] = None
    users: Optional[userForFeed]
    items: Optional[itemForFeed]

    class Config:
        orm_mode = True


class item(BaseModel):
    id: Optional[int]
    title: Union[str, None] = None
    description: Union[str, None] = None
    image: Union[str, None] = None
    cat_id: Union[int, None] = None
    cat: Optional[categoryForItem]
    ingredients: Union[str, None] = None
    instruction: Union[str, None] = None
    feed: List[feedback] = []

    class Config:
        orm_mode = True


class category(BaseModel):
    id: Optional[int]
    name: Union[str, None] = None
    image: Union[str, None] = None
    items: List[item] = []

    class Config:
        orm_mode = True


class User(BaseModel):
    id: Optional[int]
    email: Optional[str]
    password: Optional[str]
    feed: List[feedback] = []

    class Config:
        orm_mode = True


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@app.exception_handler(RequestValidationError)
async def custom_form_validation_error(request, exc):
    reformatted_message = defaultdict(list)
    for pydantic_error in exc.errors():
        loc, msg = pydantic_error["loc"], pydantic_error["msg"]
        filtered_loc = loc[1:] if loc[0] in ("body", "query", "path") else loc
        # nested fields with dot-notation
        field_string = ".".join(filtered_loc)
        reformatted_message[field_string].append(msg)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"errors": reformatted_message}),
    )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return payload


# @app.post("/login",status_code=status.HTTP_202_ACCEPTED)
# async def generate_token(
#     request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
# ):

#     user = db.query(u).filter(u.email == request.username).first()
#     if not user:
#         raise HTTPException(
#             status_code=404, detail="Invalid username or password / not Authenticated"
#         )
#     item_dict = user.__dict__
#     # return item_dict["password"]
#     user = (
#         db.query(u)
#         .filter(bcrypt.verify(request.password, item_dict["password"]))
#         .first()
#     )

#     if not user:
#         raise HTTPException(
#             status_code=404, detail="Invalid username or password / not Authenticated"
#         )
#     token = jwt.encode({"username": request.username}, JWT_SECRET, algorithm="HS256")
#     return {"access_token": token, "token_type": "bearer",'user_id': user.id,'username': user.username,'user_email': user.email,'user_type': user.user_type,}


# hello world
@app.post("/login", status_code=status.HTTP_202_ACCEPTED)
async def generate_token(
    request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(u).filter(u.email == request.username).first()

    if user:
        item_dict = user.__dict__
        if bcrypt.verify(request.password, item_dict["password"]):
            token = jwt.encode({"username": request.username},
                               JWT_SECRET, algorithm="HS256")
            return {"msg":"Logged In Successfully","access_token": token, "token_type": "bearer", 'user_id': user.id, 'username': user.username, 'user_email': user.email, 'user_type': user.user_type}

    raise HTTPException(
        status_code=404, detail="Invalid username or password / not Authenticated"
    )


# CRUD of category with all Relations


@app.post("/create-category/", status_code=status.HTTP_201_CREATED)
def add_category(
    name: str = Form(...), image: UploadFile = File(...), db: Session = Depends(get_db), User=Depends(get_current_user)
):

    if (image.content_type == "image/jpg") or (image.content_type == "image/jpeg") or (image.content_type == "image/png"):
        i = image.filename[-10:]

    else:
        raise HTTPException(
            status_code=422, detail="image has not a valid type"
        )

    if db.query(c).filter(c.name == name).first():
        raise HTTPException(
            status_code=422, detail="category is already exists"
        )

    # i = image.filename[-10:]
    cat = c(name=name, image=i)
    db.add(cat)
    db.commit()
    db.refresh(cat)

    with open(f"static/{i}", "wb") as f:
        shutil.copyfileobj(image.file, f)

    return {"msg": "Category Created Successfully"}


@app.delete("/category/{id}", status_code=status.HTTP_200_OK)
def delete_category_by_id(id: int, db: Session = Depends(get_db), User=Depends(get_current_user)):
    cat = db.query(c).filter(c.id == id)

    if not cat.first():
        raise HTTPException(status_code=404, detail="not found")
    cat.delete(synchronize_session=False)
    db.commit()
    return {"msg": "Category Deleted Successfully"}


@app.get("/category/{id}", status_code=status.HTTP_200_OK)
def read_category_by_id(id: int, db: Session = Depends(get_db)):
    cat = db.query(c).get(id)

    if not cat:
        raise HTTPException(status_code=404, detail="not found")
    return cat


@app.get("/category/", response_model=List[category], status_code=status.HTTP_200_OK)
def read_all_category(limit: bool = False, db: Session = Depends(get_db)):
    cat = db.query(c).all()
    return cat


@app.get("/all-category/", response_model=List[categoryForAdd], status_code=status.HTTP_200_OK)
def read_all_category_for_add(db: Session = Depends(get_db)):
    cat = db.query(c).all()
    return cat


@app.put("/category/{id}", status_code=status.HTTP_200_OK)
def update_category_by_id(

    id: int,
    name: str = Form(...),
    image: Optional[UploadFile] = None,
    db: Session = Depends(get_db),
    User=Depends(get_current_user)
):

    # return image.

    cat = db.query(c).get(id)

    # try:
    if not cat:
        raise HTTPException(status_code=404, detail="not found")

    if name:
        if db.query(c).filter(c.name == name, c.id != id).first():
            raise HTTPException(
                status_code=422, detail="category is already exists"
            )

        cat.name = name

    if image:
        if (image.content_type == "image/jpg") or (image.content_type == "image/jpeg") or (image.content_type == "image/png"):
            i = image.filename[-10:]

        else:
            raise HTTPException(
                status_code=422, detail="image has not a valid type"
            )

        # i = image.filename[-10:]
        cat.image = i

        with open(f"static/{i}", "wb") as f:
            shutil.copyfileobj(image.file, f)

    db.commit()

    return {"msg": "Category Updated Successfully"}

    # except Exception as e:
    #     raise HTTPException(status_code=400, detail="something went wrong")


# CRUD of item with all Relations


@app.post("/create-item/", status_code=status.HTTP_201_CREATED)
def add_item(
    cat_id: int = Form(...),
    title: str = Form(...),
    image: UploadFile = File(...),
    description: str = Form(...),
    ingredients: str = Form(...),
    instruction: str = Form(...),
    db: Session = Depends(get_db),
    User=Depends(get_current_user)
):

    if (image.content_type == "image/jpg") or (image.content_type == "image/jpeg") or (image.content_type == "image/png"):
        it = image.filename[-10:]

    else:
        raise HTTPException(
            status_code=422, detail="image has not a valid type"
        )

    if title:
        if db.query(i).filter(i.title == title).first():
            raise HTTPException(
                status_code=422, detail="item is already exists"
            )

    # try:
    item = i(
        cat_id=cat_id,
        title=title,
        image=it,
        description=description,
        ingredients=ingredients,
        instruction=instruction,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    with open(f"static/{it}", "wb") as f:
        shutil.copyfileobj(image.file, f)

    # return {"created with id": item.id}``
    return {"msg": "Item Created Successfully"}

    # except Exception as e:
    #     raise HTTPException(status_code=400, detail="something went wrong")


@app.delete("/item/{id}", status_code=status.HTTP_200_OK)
def delete_item_by_id(id: int, db: Session = Depends(get_db), User=Depends(get_current_user)):
    item = db.query(i).filter(i.id == id)
    if not item.first():
        return {"error": "not deleted"}
    item.delete(synchronize_session=False)
    db.commit()
    return {"msg": "Item Deleted Successfully"}


# @app.get("/item/{id}",response_model=item,status_code=status.HTTP_200_OK)
# def read_item_by_id(id: int,db: Session = Depends(get_db)):
#     # it = db.query(i).get(id)
#     item = db.query(i).filter(i.id == id).first()
#     # if not it:
#     #     return {"error": "There is an error"}

#     # feedback_chk = db.query(f).filter(f.r_id==id, f.u_id==user_id).first()
#     # reviewable = False
#     # if not feedback_chk:
#     #     reviewable = True

#     # # new_dict = {"it":it, "new key": reviewable}
#     # item_dict = it.__dict__
#     # print(item_dict['description'])
#     return item
#     # return a["title"]


@app.get("/item/{id}", status_code=status.HTTP_200_OK)
def read_item_by_id(id: int, u_id: int = 0, db: Session = Depends(get_db)):
    it = db.query(i).filter(i.id == id).first()
    if not it:
        return {"error": "There is an error"}

    feedback_get = db.query(f).filter(f.r_id == id).all()
    feedlist = []
    for data in feedback_get:

        feedback_user = db.query(u).filter(u.id == data.u_id).first()
        a = data.__dict__
        a['username'] = feedback_user.username
        feedlist.append(a)

    feedback_chk = db.query(f).filter(f.r_id == id, f.u_id == u_id).first()

    if not feedback_chk:
        new_dict = {"item_data": it, "feedbacks": feedlist, "can_rev": True}
        return new_dict

    new_dict = {"item_data": it, "feedbacks": feedlist, "can_rev": False}
    return new_dict


@app.get("/item/", response_model=List[item], status_code=status.HTTP_200_OK)
def read_all_item(limit: bool = False, db: Session = Depends(get_db)):
    if limit:
        item = db.query(i).limit(3).all()
        return item
    else:
        item = db.query(i).all()
        return item


@app.put("/item/{id}", status_code=status.HTTP_200_OK)
def update_item_by_id(
    id: int,
    cat_id: int = Form(...),
    title: str = Form(...),
    image: Optional[UploadFile] = None,
    description: str = Form(...),
    ingredients: str = Form(...),
    instruction: str = Form(...),
    db: Session = Depends(get_db),
    User=Depends(get_current_user)
):
    it = db.query(i).get(id)

    if not it:
        raise HTTPException(status_code=404, detail="not found")

    # try:

    if title:
        if db.query(i).filter(i.title == title, i.id != id).first():
            raise HTTPException(
                status_code=422, detail="item is already exists"
            )

        it.title = title

    if cat_id:
        it.cat_id = cat_id

    if image:
        if (image.content_type == "image/jpg") or (image.content_type == "image/jpeg") or (image.content_type == "image/png"):
            im = image.filename[-10:]

        else:
            raise HTTPException(
                status_code=422, detail="image has not a valid type"
            )

        # im = image.filename[-10:]
        it.image = im
        with open(f"static/{im}", "wb") as f:
            shutil.copyfileobj(image.file, f)

    if description:
        it.description = description

    if ingredients:
        it.ingredients = ingredients

    if instruction:
        it.instruction = instruction

    db.commit()
    return {"msg": "Item Updated Successfully"}

    # except Exception as e:
    #     raise HTTPException(status_code=400, detail="something went wrong")


# CRUD of users with all Relations


@app.post("/create-user/", status_code=status.HTTP_201_CREATED)
def add_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    user_type: Optional[str] = "user",
    db: Session = Depends(get_db)
):
    # try:

        if db.query(u).filter(u.email == email).first():
            raise HTTPException(
                status_code=422, detail="email is already exists"
            )

        user = u(
            username=username,
            email=email,
            password=bcrypt.hash(password),
            user_type=user_type,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        
        user_dict = user.__dict__
        user_dict["msg"]="You have been Registered"
        return user_dict

    # except Exception as e:
    #     raise HTTPException(status_code=400, detail="something went wrong")


@app.delete("/user/{id}", status_code=status.HTTP_200_OK)
def delete_user_by_id(id: int, db: Session = Depends(get_db), User=Depends(get_current_user)):
    user = db.query(u).filter(u.id == id)
    if not user.first():
        raise HTTPException(status_code=404, detail="not found")
    user.delete(synchronize_session=False)
    db.commit()
    return {"msg": "You have been Deleted Successfully"}


@app.get("/user/{id}", status_code=status.HTTP_200_OK)
def read_user_by_id(id: int, db: Session = Depends(get_db)):
    user = db.query(u).get(id)
    if not user:
        return {"error": "not found"}
    return user


@app.get("/user/", response_model=List[User], status_code=status.HTTP_200_OK)
def read_all_user(db: Session = Depends(get_db)):
    user = db.query(u).all()
    return user


@app.put("/user/{id}", status_code=status.HTTP_200_OK)
def update_user_by_id(
    id: int,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    User=Depends(get_current_user)
):

    us = db.query(u).get(id)

    if not us:
        raise HTTPException(status_code=404, detail="not found")

    try:
        us.username = username
        us.email = email
        us.password = bcrypt.hash(password)

        db.commit()
        return {"msg": "You have been Updated Successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail="something went wrong")


# CRUD of feedback with all Relations


@app.post("/create-feedback/", status_code=status.HTTP_201_CREATED)
def add_feedback(
    r_id: int = Form(...),
    u_id: int = Form(...),
    description: str = Form(...),
    rating: str = Form(...),
    db: Session = Depends(get_db),
    User=Depends(get_current_user)
):
    feedback = f(
        r_id=r_id,
        u_id=u_id,
        description=description,
        rating=rating,
    )

    if db.query(f).filter(f.r_id == r_id, f.u_id == u_id).first():
        raise HTTPException(
            status_code=422, detail="Feddback has already been submmited"
        )

    try:
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return {"msg":"Feedback Created Successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail="something went wrong")


@app.delete("/feedback/{id}", status_code=status.HTTP_200_OK)
def delete_feedback_by_id(id: int, db: Session = Depends(get_db), User=Depends(get_current_user)):

    feedback = db.query(f).filter(f.id == id)

    if not feedback.first():
        raise HTTPException(
            status_code=404,
            detail="not found"
        )

    feedback.delete(synchronize_session=False)
    db.commit()
    return {"msg":"Feedback Deleted Successfully"}


@app.get("/feedback/{id}", status_code=status.HTTP_200_OK)
def read_feedback_by_id(id: int, db: Session = Depends(get_db)):
    feedback = db.query(f).get(id)
    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="not found"
        )
    return feedback


@app.get("/feedback/", response_model=List[feedback], status_code=status.HTTP_200_OK)
def read_all_feedback(db: Session = Depends(get_db)):
    feedback = db.query(f).all()
    return feedback


@app.put("/feedback/{id}", status_code=status.HTTP_200_OK)
def update_feedback_by_id(
    id: int,
    r_id: int = Form(...),
    u_id: int = Form(...),
    description: str = Form(...),
    rating: str = Form(...),
    db: Session = Depends(get_db),
    User=Depends(get_current_user)
):
    feed = db.query(f).get(id)

    if not feed:
        raise HTTPException(
            status_code=404,
            detail="not found"
        )

    try:
        feed.r_id = r_id
        feed.u_id = u_id
        feed.description = description
        feed.rating = rating

        db.commit()
        return {"msg":"Feedback Updated Successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail="something went wrong")


@app.get("/get-count-all/", status_code=status.HTTP_200_OK)
def get_count_all(db: Session = Depends(get_db)):
    category = db.query(c).all()
    item = db.query(i).all()
    user = db.query(u).all()
    feedback = db.query(f).all()
    return {"Total category":len(category), "Total item": len(item), "Total users": len(user), "Total feedbacks": len(feedback)}
