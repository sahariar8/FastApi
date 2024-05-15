from datetime import datetime, timedelta
from fastapi import APIRouter,Depends,HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from database import sessionLocal
from models import Users
from pydantic import BaseModel
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from jose import jwt,JWTError
from starlette import status

router = APIRouter(
    prefix='/auth',
    tags=['Auth']
)

SECRET_KEY = '4eede6869c9bd701f4a2045ef255835635c93cede95f6eeed8ae7bac776aec7b'
ALGORITHM = 'HS256'
OAUTH_BEARER = OAuth2PasswordBearer(tokenUrl='auth/token')


bcrypt_context = CryptContext(schemes=['bcrypt'],deprecated = 'auto')
class userRequest(BaseModel):
    email:str
    username:str
    firstname:str
    lastname:str
    password:str
    role:str
    
class Token(BaseModel):
    access_token:str
    token_type:str
    

async def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close
    

db_dependency = Annotated[Session,Depends(get_db)]

# Authentication

def authenticate_user(username:str,password:str,db:db_dependency):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user
    
#End Authentication

def create_access_token(username:str,user_id:int,expires_delta:timedelta):
    encode = {'sub':username,'id':user_id}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp':expires})
    return jwt.encode(encode,SECRET_KEY,algorithm=ALGORITHM)

async def get_current_user(token:Annotated[str,Depends(OAUTH_BEARER)]):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        username:str = payload.get('sub')
        user_id:int = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate User')
        return {'username':username,'id':user_id}
    
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate User')
        
        
    

@router.get("/all_users")
async def all_users(db:db_dependency):
    all_users = db.query(Users).all()
    return all_users

@router.post("/token",response_model=Token)
async def access_token(form_data:Annotated[OAuth2PasswordRequestForm,Depends()],db:db_dependency):
    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate User')
    token = create_access_token(user.username,user.id, timedelta(minutes=20))
    return {'access_token':token,'token_type':"bearer"}

@router.post("/create_users")
async def create_user(db:db_dependency,user_request:userRequest):
    new_user = Users(
        email = user_request.email,
        username = user_request.username,
        first_name = user_request.firstname,
        last_name = user_request.lastname,
        role = user_request.role,
        hashed_password = bcrypt_context.hash(user_request.password),
        is_active = True
        
    )
    db.add(new_user)
    db.commit()
    
    return new_user
