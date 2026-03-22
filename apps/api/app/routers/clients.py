from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.get("")
async def list_clients(current_user: User = Depends(get_current_user)) -> list:
    """Placeholder — implemented in ENG-95."""
    return []
