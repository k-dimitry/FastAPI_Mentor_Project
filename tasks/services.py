from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tasks.dto import TaskCreateDTO, TaskResponseDTO, TaskUpdateDTO
from tasks.models import Task


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _to_dto(task: Task) -> TaskResponseDTO:
        """Transform SQLAlchemy model into DTO."""
        return TaskResponseDTO(
            id=task.id,
            title=task.title,
            description=task.description,
            created_at=task.created_at,
            updated_at=task.updated_at,
            is_done=task.is_done,
        )

    async def create_task(
        self,
        dto: TaskCreateDTO,
        user_id: UUID | None = None,  # Временно, пока нет авторизации
    ) -> TaskResponseDTO:
        """Create Task and return DTO."""
        # Пока используем переданный user_id или генерируем заглушку
        owner = user_id or uuid4()

        new_task = Task(
            title=dto.title,
            description=dto.description,
            user_id=owner,
        )
        self.db.add(new_task)
        await self.db.commit()
        await self.db.refresh(new_task)
        return self._to_dto(new_task)

    async def get_task(self, task_id: UUID) -> TaskResponseDTO | None:
        """Return Task by id or None."""
        task = await self.db.get(Task, task_id)
        if not task:
            return None
        return self._to_dto(task)

    async def get_all_tasks(self) -> list[TaskResponseDTO]:
        """Return list of all Tasks."""
        result = await self.db.execute(select(Task))
        tasks = result.scalars().all()
        return [self._to_dto(t) for t in tasks]

    async def update_task(
        self,
        task_id: UUID,
        dto: TaskUpdateDTO,
    ) -> TaskResponseDTO | None:
        """Partially update Task and return updated DTO."""
        task = await self.db.get(Task, task_id)
        if not task:
            return None

        if dto.title is not None:
            task.title = dto.title
        if dto.description is not None:
            task.description = dto.description
        if dto.is_done is not None:
            task.is_done = dto.is_done

        await self.db.commit()
        await self.db.refresh(task)
        return self._to_dto(task)

    async def delete_task(self, task_id: UUID) -> bool:
        """Delete Task. Return True, if done, else False."""
        task = await self.db.get(Task, task_id)
        if not task:
            return False
        await self.db.delete(task)
        await self.db.commit()
        return True
