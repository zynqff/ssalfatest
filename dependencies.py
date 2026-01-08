from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
from database import get_db

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Dependency to get the current user from the user_id cookie.
    Returns the user object or None.
    """
    user_id = request.cookies.get("user_id")
    if user_id:
        try:
            return db.query(models.User).filter(models.User.id == int(user_id)).first()
        except (ValueError, TypeError):
            return None
    return None

async def get_current_admin_user(user: models.User = Depends(get_current_user)):
    """
    Dependency to ensure the current user is an admin.
    Raises HTTPException if the user is not an admin.
    """
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен. Требуются права администратора."
        )
    return user
