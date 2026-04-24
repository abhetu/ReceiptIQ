from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title="Receipt Reconciliation Agent", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health_check() -> dict:
        return {"status": "ok"}

    # Optional router loading for compatibility with different project layouts.
    try:
        from app.api.routes import router as api_router  # type: ignore
        app.include_router(api_router)
    except Exception:
        try:
            from routes import router as api_router  # type: ignore
            app.include_router(api_router)
        except Exception:
            # Keep server bootable even when full backend modules are not present
            # in this lightweight repo snapshot.
            pass

    return app


app = create_app()
