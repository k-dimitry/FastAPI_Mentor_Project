
from fastapi import FastAPI

from api.v1.router import router as v1_router

app = FastAPI()  # noqa: E402
app.include_router(v1_router, prefix="/api/v1")