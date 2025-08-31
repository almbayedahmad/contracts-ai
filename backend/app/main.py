from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.errors import ErrorMiddleware
from app.core.logging import setup_logging

def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
    app.add_middleware(ErrorMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # TODO: include routers: from app.api.v1 import parties, contracts, extraction, compliance
    # app.include_router(parties.router, prefix="/v1")
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
