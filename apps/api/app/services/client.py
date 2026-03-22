from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.client import Client
from app.models.project import Project
from app.schemas.client import ClientCreate, ClientUpdate


class ClientService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_clients(self, user_id: str) -> list[Client]:
        result = await self.db.execute(select(Client).where(Client.user_id == user_id))
        return list(result.scalars().all())

    async def create_client(self, user_id: str, data: ClientCreate) -> Client:
        client = Client(
            user_id=user_id,
            name=data.name,
            email=data.email,
            hourly_rate=data.hourly_rate,
            currency=data.currency,
        )
        self.db.add(client)
        await self.db.commit()
        await self.db.refresh(client)
        return client

    async def get_client(self, user_id: str, client_id: str) -> Client:
        result = await self.db.execute(
            select(Client).where(Client.id == client_id, Client.user_id == user_id)
        )
        client = result.scalar_one_or_none()
        if client is None:
            raise NotFoundError("Client not found")
        return client

    async def update_client(self, user_id: str, client_id: str, data: ClientUpdate) -> Client:
        client = await self.get_client(user_id, client_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)
        await self.db.commit()
        await self.db.refresh(client)
        return client

    async def delete_client(self, user_id: str, client_id: str) -> None:
        client = await self.get_client(user_id, client_id)

        # Check for active projects
        result = await self.db.execute(
            select(Project).where(
                Project.client_id == client_id,
                Project.is_active.is_(True),
            )
        )
        active_projects = result.scalars().first()
        if active_projects is not None:
            raise ConflictError("Cannot delete client with active projects")

        await self.db.delete(client)
        await self.db.commit()
