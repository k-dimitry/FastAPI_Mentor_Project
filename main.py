import logging.config
import os

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

import tasks.models  # noqa
import users.models  # noqa
from api.v1.router import router as v1_router
from common.exceptions import AlreadyExistsError
from common.middleware import log_requests

logging.config.fileConfig(
    os.path.join(os.path.dirname(__file__), 'logging.ini'),
    disable_existing_loggers=False,
)
app = FastAPI()
app.middleware('http')(log_requests)
app.include_router(v1_router, prefix='/api')


@app.exception_handler(AlreadyExistsError)
async def already_exists_exception_handler(_: Request, exc: AlreadyExistsError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={'detail': exc.message},
    )
