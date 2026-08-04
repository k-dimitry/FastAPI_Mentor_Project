from uuid import UUID, uuid4

from sqlalchemy import func, over, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .dto import TaskCreateDTO, TaskListDTO, TaskResponseDTO, TaskUpdateDTO
from .exceptions import TaskAlreadyExistsError
from .models import Task


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
        self, dto: TaskCreateDTO, user_id: UUID | None = None
    ) -> TaskResponseDTO:
        """Create Task and return DTO."""

        owner = user_id or uuid4()
        new_task = Task(
            title=dto.title,
            description=dto.description,
            user_id=owner,
        )
        self.db.add(new_task)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise TaskAlreadyExistsError(
                f"Task '{dto.title}' already exists for this user."
            )
        await self.db.refresh(new_task)
        return self._to_dto(new_task)

    async def get_task(self, task_id: UUID) -> TaskResponseDTO | None:
        """Return Task by id or None."""
        task = await self.db.get(Task, task_id)
        if not task:
            return None
        return self._to_dto(task)

    async def get_all_tasks(self, page: int = 1, size: int = 20) -> TaskListDTO:
        """Return list of all Tasks with pagination"""
        offset = (page - 1) * size
        sub = (
            select(Task, func.count().over().label('total'))
            .order_by(Task.created_at)
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(sub)
        rows = result.all()
        if not rows:
            total = 0
            items = []
        else:
            total = rows[0].total
            items = [self._to_dto(row.Task) for row in rows]

        return TaskListDTO(
            items=items,
            total=total,
            page=page,
            size=size,
        )

    async def update_task(
        self, task_id: UUID, dto: TaskUpdateDTO
    ) -> TaskResponseDTO | None:
        """Partially update Task and return updated DTO."""
        task = await self.db.get(Task, task_id)
        if not task:
            return None

        if dto.title_is_set:
            task.title = dto.title
        if dto.description_is_set:
            task.description = dto.description
        if dto.is_done_is_set:
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
