from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.app.core.database import Base, engine
from backend.app.models.document import Document
from backend.app.api.routes.documents import router as documents_router


app = FastAPI(
    title="Intelligent Document Extraction API",
    description="AI-powered document extraction, validation and API platform",
    version="1.0.0"
)


# Create database tables
Base.metadata.create_all(bind=engine)


# Frontend configuration
templates = Jinja2Templates(
    directory="frontend/templates"
)

app.mount(
    "/static",
    StaticFiles(directory="frontend/static"),
    name="static"
)


# Frontend dashboard
@app.get("/", include_in_schema=False)
def dashboard(request: Request):
    return templates.TemplateResponse(
       request=request,
       name="dashboard.html"
    )


# Health endpoint
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "ok",
        "service": "document-intelligence-api"
    }


# Document API routes
app.include_router(documents_router)