from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse], status_code=status.HTTP_200_OK)
async def list_projects(
    client_id: str | None = None,
    is_active: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    service = ProjectService(db)
    return await service.list_projects(current_user.id, client_id=client_id, is_active=is_active)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    service = ProjectService(db)
    return await service.create_project(current_user.id, data)


@router.get("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    service = ProjectService(db)
    return await service.get_project(current_user.id, project_id)


@router.put("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    service = ProjectService(db)
    return await service.update_project(current_user.id, project_id, data)


@router.patch(
    "/{project_id}/deactivate",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
)
async def deactivate_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    service = ProjectService(db)
    return await service.deactivate_project(current_user.id, project_id)
