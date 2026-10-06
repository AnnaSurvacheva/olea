import logging


import time


from fastapi import FastAPI, Request


from questions.presentation.router import router as question_router
from core.logging_config import setup_logger

logger = logging.getLogger(__name__)


from core.admin import setup_admin


app = FastAPI()
app.include_router(question_router)


setup_admin(app=app)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Ошибка: %s %s", request.method, request.url.path)
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1f мс)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response
