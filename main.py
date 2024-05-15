
from fastapi import FastAPI
from database import engine
import models
from router import todos
from router import users

app = FastAPI()

app.include_router(users.router)
app.include_router(todos.router)


models.base.metadata.create_all(bind = engine)



