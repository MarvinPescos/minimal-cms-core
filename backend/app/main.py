from fastapi import FastAPI, Request
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.shared.errors.exceptions import BaseAppException
from app.core import settings


from app.infrastructure.cache import limiter, rate_limit_exceeded_handler
from app.features.auth import router as auth_router
from app.features.events import router as event_router
from app.features.gallery import router as gallery_router




app = FastAPI()

# CORS Configuration - Uses CORS_ORIGINS from settings/environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Attach rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

app.include_router(auth_router)
app.include_router(event_router)
app.include_router(gallery_router)

