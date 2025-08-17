from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

def get_object_or_404(db: Session, model, object_id: int, detail: Optional[str] = None):
    """通用查询工具：根据id获取对象，不存在则抛404"""
    obj = db.query(model).filter(model.id == object_id).first()
    if not obj:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail= detail or f"{model.__name__}不存在"
                )
    return obj

