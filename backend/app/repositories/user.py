from sqlalchemy.orm import Session
from app.models.user import User

class UserRepository:
    def get(self, db: Session, id: int) -> User:
        return db.query(User).filter(User.id == id).first()

    def get_by_email(self, db: Session, email: str) -> User:
        return db.query(User).filter(User.email == email).first()

user_repository = UserRepository()
