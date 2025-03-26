from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
import os

from app.routers import documents, analysis, precedents
from app.services.document_service import DocumentService
from app.services.analysis_service import AnalysisService
from app.services.vector_service import VectorService
from app.llm.llm_factory import LLMService

# Création de l'application FastAPI
app = FastAPI(
    title="API d'analyse de documents juridiques",
    description="API pour l'extraction de clauses, l'analyse de risques et la génération de recommandations pour des documents juridiques",
    version="1.0.0",
    docs_url=None,
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines exactes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage des routeurs
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analyses"])
app.include_router(precedents.router, prefix="/precedents", tags=["Précédents juridiques"])

# Endpoint de santé
@app.get("/health", tags=["Santé"])
async def health_check():
    """
    Vérifie l'état de santé de l'API
    """
    return {"status": "healthy", "version": "1.0.0"}

# Documentation Swagger personnalisée
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="API d'analyse de documents juridiques - Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
    )

# Événement de démarrage
@app.on_event("startup")
async def startup_event():
    """
    Initialisation des services au démarrage de l'application
    """
    # Initialiser les services
    document_service = DocumentService()
    analysis_service = AnalysisService()
    vector_service = VectorService()
    llm_service = LLMService()
    
    # Créer le répertoire d'uploads s'il n'existe pas
    os.makedirs("/app/uploads", exist_ok=True)
    
    print("API d'analyse de documents juridiques démarrée avec succès!")

# Montage des fichiers statiques pour les uploads
app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")

# Si ce fichier est exécuté directement
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
