from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tasks.dto import TaskCreateDTO, TaskListDTO, TaskResponseDTO, TaskUpdateDTO
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
        user_id: UUID | None = None,
    ) -> TaskResponseDTO:
        """Create Task and return DTO."""
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

    async def get_all_tasks(
        self,
        page: int = 1,
        size: int = 20,
    ) -> TaskListDTO:
        """Return list of all Tasks with pagination"""
        total_query = select(func.count()).select_from(Task)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar_one()

        offset = (page - 1) * size
        query = select(Task).offset(offset).limit(size)
        result = await self.db.execute(query)
        tasks = result.scalars().all()

        items = [self._to_dto(t) for t in tasks]

        return TaskListDTO(
            items=items,
            total=total,
            page=page,
            size=size,
        )

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
