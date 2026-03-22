from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.services.client import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientResponse], status_code=status.HTTP_200_OK)
async def list_clients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ClientResponse]:
    service = ClientService(db)
    return await service.list_clients(current_user.id)


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    service = ClientService(db)
    return await service.create_client(current_user.id, data)


@router.get("/{client_id}", response_model=ClientResponse, status_code=status.HTTP_200_OK)
async def get_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    service = ClientService(db)
    return await service.get_client(current_user.id, client_id)


@router.put("/{client_id}", response_model=ClientResponse, status_code=status.HTTP_200_OK)
async def update_client(
    client_id: str,
    data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    service = ClientService(db)
    return await service.update_client(current_user.id, client_id, data)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = ClientService(db)
    await service.delete_client(current_user.id, client_id)
