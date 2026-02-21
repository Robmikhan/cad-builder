from fastapi import APIRouter
from services.models.model_manager import ModelManager

router = APIRouter()

@router.get("")
def list_models():
    mm = ModelManager()
    return mm.status()
