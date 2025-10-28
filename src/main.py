"""Compatibility wrapper for launching the runtime via `python -m src.main`."""

from services.runtime.src.main import app, settings  # noqa: F401


if __name__ == "__main__":  # pragma: no cover - convenience entry point
    import uvicorn

    uvicorn.run(
        "services.runtime.src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )

