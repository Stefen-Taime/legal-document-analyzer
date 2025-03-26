from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict
from datetime import datetime

from app.models.analysis import Precedent
from app.services.vector_service import VectorService

router = APIRouter()

def get_vector_service():
    return VectorService()

@router.get("/search", response_model=List[Precedent])
async def search_precedents(
    query: str = Query(..., description="Requête de recherche"),
    limit: int = Query(10, description="Nombre maximum de résultats à retourner"),
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Recherche des précédents juridiques similaires
    """
    try:
        precedents = await vector_service.search_precedents(query, limit)
        return precedents
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche de précédents: {str(e)}"
        )

@router.get("/{precedent_id}", response_model=Precedent)
async def get_precedent(
    precedent_id: str = Path(..., description="ID du précédent à récupérer"),
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Récupère les détails d'un précédent juridique
    """
    try:
        precedent = await vector_service.get_precedent(precedent_id)
        
        if not precedent:
            raise HTTPException(
                status_code=404,
                detail=f"Précédent avec l'ID {precedent_id} non trouvé"
            )
            
        return precedent
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération du précédent: {str(e)}"
        )

@router.post("/", response_model=Dict[str, str])
async def add_precedent(
    title: str = Body(...),
    description: str = Body(...),
    precedent_type: str = Body(...),
    relevance: str = Body(...),
    source: Optional[str] = Body(None),
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Ajoute un nouveau précédent juridique
    """
    try:
        precedent_id = await vector_service.add_precedent(
            title=title,
            description=description,
            precedent_type=precedent_type,
            relevance=relevance,
            source=source
        )
        
        return {"id": precedent_id, "status": "success"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'ajout du précédent: {str(e)}"
        )

@router.post("/seed", response_model=Dict[str, int])
async def seed_precedents(
    file_path: str = Body(..., embed=True),
    vector_service: VectorService = Depends(get_vector_service)
):
    """
    Initialise la base de données avec des précédents juridiques à partir d'un fichier
    """
    try:
        count = await vector_service.seed_precedents(file_path)
        return {"count": count}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'initialisation des précédents: {str(e)}"
        )