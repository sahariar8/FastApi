from typing import Annotated
from fastapi import Depends, FastAPI,Path,Query,HTTPException
from database import sessionLocal,engine
from sqlalchemy.orm import Session
import models
from pydantic import BaseModel,Field
from starlette import status
from models import Todos
from router.todos import router

app = FastAPI()
app.include_router(router)

models.base.metadata.create_all(bind = engine)



