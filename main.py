from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

import tasks.models  # noqa
import users.models  # noqa
from api.v1.router import router as v1_router
from common.exceptions import AlreadyExistsError

app = FastAPI()
app.include_router(v1_router, prefix='/api')


@app.exception_handler(AlreadyExistsError)
async def already_exists_exception_handler(_: Request, exc: AlreadyExistsError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={'detail': exc.message},
    )
