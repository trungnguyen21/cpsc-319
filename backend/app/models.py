from pydantic import BaseModel

# Due to OAuth2 specs, User model must contain 'username' and 'password'
# 'email' or 'user_name' would not work
class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None 

class UserInDB(User):
    hashed_password: str

class UserSignUp(BaseModel):
    username: str
    full_name: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None