from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.database import Base


class Task(Base):
    __tablename__ = 'tasks'

    #uuid
    id = Column(Integer, primary_key=True, index=True)
    # ограничить по длине!
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
