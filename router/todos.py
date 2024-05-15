from typing import Annotated
from fastapi import Depends,Path,Query,HTTPException,APIRouter
from database import sessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel,Field
from starlette import status
from models import Todos
from .users import get_current_user

router = APIRouter()



class TodoRequest(BaseModel):
    title:str = Field(min_length=3)
    description:str = Field(min_length=3)
    priority:int = Field(gt=0,lt=6)
    complete:bool
    


def get_db():
    
    db = sessionLocal()
    try:
        yield db
    finally:
       db.close
       
db_dependency = Annotated[Session,Depends(get_db)]
user_dependency = Annotated[dict,Depends(get_current_user)]
        
@router.get("/todos")
async def get_all_todos(user:user_dependency,db:db_dependency):
    return db.query(Todos).filter(Todos.owner_id == user.get('id') ).all()

@router.get("/todos/{todo_id}")
async def individual_id(user:user_dependency,db:db_dependency,todo_id:int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401,detail='Authentication failed')
        
    single_todo = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if single_todo is not None:
        return single_todo
    raise HTTPException(status_code=404,detail='Id Not Found')

@router.get('/todos/')
async def todo_by_filter(db:db_dependency,todos_priority:int=Query(gt=0,lt=6)):
    filtered_todo = db.query(Todos).filter(Todos.priority == todos_priority).all()
    if filtered_todo is not None:
        return filtered_todo
    raise HTTPException(status_code=404,detail='Todo not found with this priority')

@router.get('/todos/{priority}/')
async def get_todos_depends_on_priority_and_complete(db:db_dependency,complete:int,priority:int=Path(gt=0,lt=6)):
    get_todos = db.query(Todos).filter(Todos.priority == priority,Todos.complete == complete).all()
    if get_todos is not None:
        return get_todos
    raise HTTPException(status_code=404,detail='Not Found')

    
#Post Route
@router.post("/todos/create_todos",status_code=status.HTTP_201_CREATED)
async def get_todos(user:user_dependency,db:db_dependency,todo_request:TodoRequest):
    if user is None:
        raise HTTPException(status_code=404,detail='Authentication Failed')
    new_todo = Todos(**todo_request.model_dump(),owner_id = user.get('id') )
    db.add(new_todo)
    db.commit()
    

#update Route    
@router.put("/todos/{todo_id}")
async def update_todo(user:user_dependency,db:db_dependency,
                      todo_request:TodoRequest,todo_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401,detail='UnAuthenticate User')
    
    get_todo = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if get_todo is None:
        raise HTTPException(status_code=404,detail='id not found')
    get_todo.title = todo_request.title
    get_todo.description = todo_request.description
    get_todo.priority = todo_request.priority
    get_todo.complete = todo_request.complete
    
    db.add(get_todo)
    db.commit()
    
    
#Delete Route   
@router.delete("/todos/{todo_id}")
async def todo_delete(user:user_dependency,db:db_dependency,todo_id:int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401,detail='UnAuthenticate User')
 
    get_todo = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if get_todo is None:
        raise HTTPException(status_code=404,detail='id not found')
    db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).delete()
    db.commit()
    