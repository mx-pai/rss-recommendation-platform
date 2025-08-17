from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, creste_access_token, verify_token
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer()

def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
        ) -> User:
    """获取当前用户"""
    username = verify_token(credentials.credentials)
    if username is None:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证",
                headers={"WWW-Authenticate": "Bearer"}
                )
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"}
                )
    return user

@router.post("/register", response_model=UserResponse)

def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
                )

    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
                )

    hashed_password = hash_password(user_data.password)
    db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
            )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"}
                )
    access_token = creste_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user





