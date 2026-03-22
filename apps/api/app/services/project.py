from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.client import Client
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_projects(
        self,
        user_id: str,
        client_id: str | None = None,
        is_active: bool | None = None,
    ) -> list[Project]:
        stmt = select(Project).where(Project.user_id == user_id)
        if client_id is not None:
            stmt = stmt.where(Project.client_id == client_id)
        if is_active is not None:
            stmt = stmt.where(Project.is_active.is_(is_active))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_project(self, user_id: str, data: ProjectCreate) -> Project:
        if data.client_id is not None:
            result = await self.db.execute(
                select(Client).where(Client.id == data.client_id, Client.user_id == user_id)
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError("Client not found")

        project = Project(
            user_id=user_id,
            name=data.name,
            description=data.description,
            color=data.color,
            client_id=data.client_id,
            is_active=data.is_active,
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_project(self, user_id: str, project_id: str) -> Project:
        result = await self.db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise NotFoundError("Project not found")
        return project

    async def update_project(self, user_id: str, project_id: str, data: ProjectUpdate) -> Project:
        project = await self.get_project(user_id, project_id)

        update_data = data.model_dump(exclude_unset=True)

        if "client_id" in update_data and update_data["client_id"] is not None:
            result = await self.db.execute(
                select(Client).where(
                    Client.id == update_data["client_id"], Client.user_id == user_id
                )
            )
            if result.scalar_one_or_none() is None:
                raise NotFoundError("Client not found")

        for field, value in update_data.items():
            setattr(project, field, value)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def deactivate_project(self, user_id: str, project_id: str) -> Project:
        project = await self.get_project(user_id, project_id)
        project.is_active = False
        await self.db.commit()
        await self.db.refresh(project)
        return project
