import uvicorn
from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Task

app = FastAPI()


@app.get('/tasks')
async def get_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task))
    tasks = result.scalars().all()
    return tasks


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/hello/{name}')
async def say_hello(name: str):
    return {'message': f'Hello {name}'}
