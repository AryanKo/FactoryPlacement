"""
AquaShield — FastAPI Main Entrypoint
Mounts /api/explain (DevB) router and sets up CORS middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.explain import router as explain_router

app = FastAPI(
    title="AquaShield API",
    description="Grounded water-risk decision support with Gemma 4",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(explain_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "AquaShield API"}
