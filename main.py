from fastapi import FastAPI

import tasks.models  # noqa
import users.models  # noqa
from api.v1.router import router as v1_router

app = FastAPI()
app.include_router(v1_router, prefix='/api/v1')
