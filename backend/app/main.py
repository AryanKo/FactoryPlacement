"""
AquaShield — FastAPI Main Entrypoint
Mounts /api/risk (DevA) and /api/explain (DevB) routers with CORS and exception handlers.
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import (
    DomainException,
    domain_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.routers import risk
from app.routers import explain

app = FastAPI(
    title=settings.app_name or "AquaShield API",
    description="Grounded water-risk decision support with Gemma 4",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):  # noqa: ANN001
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )


# --- ROUTERS ---
app.include_router(risk.router)
app.include_router(explain.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "AquaShield API"}
