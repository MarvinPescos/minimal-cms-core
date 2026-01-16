from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.shared.errors.exceptions import BaseAppException

from app.features.auth import router as auth_router
from app.features.events import router as event_router


app = FastAPI()

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

app.include_router(auth_router)
app.include_router(event_router)
