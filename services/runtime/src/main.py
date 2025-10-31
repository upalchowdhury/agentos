import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import agents, health, observability
from .config import settings
from .database import db

logger = logging.getLogger(__name__)

# Import enhanced APIs
try:
    from .api import agents_v2

    HAS_V2_API = True
except ImportError as exc:
    HAS_V2_API = False
    logger.warning("V2 API not available: %s", exc)

# Import telemetry ingest
try:
    from .api import telemetry_ingest

    HAS_TELEMETRY_INGEST = True
except ImportError as exc:
    HAS_TELEMETRY_INGEST = False
    logger.debug("Telemetry ingest not available: %s", exc)

# Import OpenTelemetry (optional)
try:
    from .telemetry import TelemetryConfig, setup_telemetry

    HAS_TELEMETRY = True
except ImportError as exc:
    HAS_TELEMETRY = False
    logger.debug("Telemetry not enabled: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Runtime service")
    
    # Initialize OpenTelemetry if available
    if HAS_TELEMETRY:
        try:
            setup_telemetry(
                TelemetryConfig(
                    service_name="runtime-service",
                    service_version="0.2.0",
                    # Configure exporters as needed:
                    # jaeger_endpoint="http://localhost:14268/api/traces",
                    # otlp_endpoint="http://localhost:4317",
                    enable_console_export=False,  # Set to True for debugging
                )
            )
            logger.info("OpenTelemetry initialized")
        except Exception as e:
            logger.warning(f"OpenTelemetry initialization failed: {e}")
    
    await db.connect()
    logger.info("Runtime service ready")
    yield
    logger.info("Shutting down Runtime service")
    await db.disconnect()


app = FastAPI(
    title="Agent Runtime Service",
    description="Deploy and execute AI agents",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(health.router)
app.include_router(observability.router)

# Include V2 API if available
if HAS_V2_API:
    app.include_router(agents_v2.router)
    logger.info("V2 API routes registered")

# Include telemetry ingest if available
if HAS_TELEMETRY_INGEST:
    app.include_router(telemetry_ingest.router)
    logger.info("Telemetry ingest routes registered")


@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
