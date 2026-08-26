from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, asc, case, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from tasks.dto import (
    TaskActiveUserDTO,
    TaskActiveUsersDTO,
    TaskCreateDTO,
    TaskListDTO,
    TaskResponseDTO,
    TaskStatsByDayDTO,
    TaskStatsByDayItemDTO,
    TaskStatsTotalDTO,
    TaskUpdateDTO,
)
from tasks.exceptions import TaskAlreadyExistsError
from tasks.models import Task
from users.models import User


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

    async def _get_user_task(self, task_id: UUID, user_id: UUID) -> Task | None:
        """Возвращает задачу, принадлежащую указанному пользователю,
        или None."""
        result = await self.db.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_task(
        self, dto: TaskCreateDTO, user_id: UUID
    ) -> TaskResponseDTO:
        """Create Task and return DTO."""
        owner = user_id
        new_task = Task(
            title=dto.title,
            description=dto.description,
            is_done=dto.is_done,
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

    async def get_task(
        self, task_id: UUID, user_id: UUID
    ) -> TaskResponseDTO | None:
        """Возвращает задачу, только если она принадлежит пользователю."""
        task = await self._get_user_task(task_id, user_id)
        if task is None:
            return None
        return self._to_dto(task)

    async def get_all_tasks(
        self,
        user_id: UUID,
        *,
        limit: int = 20,
        offset: int = 0,
        is_done: bool | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        query: str | None = None,
        order_by: str = 'created_at',
        direction: str = 'desc',
    ) -> TaskListDTO:
        """Возвращает список задач с фильтрами,
        поиском, сортировкой и пагинацией."""
        conditions = [Task.user_id == user_id]

        if is_done is not None:
            conditions.append(Task.is_done == is_done)
        if created_from is not None:
            conditions.append(Task.created_at >= created_from)
        if created_to is not None:
            conditions.append(Task.created_at <= created_to)
        if query:
            search = f'%{query}%'
            conditions.append(
                or_(
                    Task.title.ilike(search),
                    Task.description.ilike(search),
                )
            )

        # Подзапрос с оконной функцией для подсчёта total
        where_clause = and_(*conditions)
        stmt = select(Task, func.count().over().label('total')).where(
            where_clause
        )

        # Сортировка
        order_column = getattr(Task, order_by, Task.created_at)
        if direction == 'asc':
            stmt = stmt.order_by(asc(order_column))
        else:
            stmt = stmt.order_by(desc(order_column))

        # Пагинация limit/offset
        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        rows = result.all()

        if not rows:
            return TaskListDTO(items=[], total=0, limit=limit, offset=offset)

        total = rows[0].total
        items = [self._to_dto(row.Task) for row in rows]
        return TaskListDTO(items=items, total=total, limit=limit, offset=offset)

    async def update_task(
        self, task_id: UUID, dto: TaskUpdateDTO, user_id: UUID
    ) -> TaskResponseDTO | None:
        """Обновляет задачу, если принадлежит пользователю, иначе None."""
        task = await self._get_user_task(task_id, user_id)
        if task is None:
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

    async def delete_task(self, task_id: UUID, user_id: UUID) -> bool:
        """Удаляет задачу, только если принадлежит пользователю."""
        task = await self._get_user_task(task_id, user_id)
        if task is None:
            return False

        await self.db.delete(task)
        await self.db.commit()
        return True

    async def get_stats_total(self, user_id: UUID) -> TaskStatsTotalDTO:
        """Возвращает статистику по выполненным/невыполненным задачам."""
        stmt = select(
            func.count(case((Task.is_done.is_(True), 1))).label('done_count'),
            func.count(case((Task.is_done.is_(False), 1))).label(
                'not_done_count'
            ),
        ).where(Task.user_id == user_id)

        result = await self.db.execute(stmt)
        row = result.one()
        done = row.done_count or 0
        not_done = row.not_done_count or 0
        total = done + not_done
        done_percent = round((done / total) * 100, 2) if total else 0.0

        return TaskStatsTotalDTO(
            done_count=done,
            not_done_count=not_done,
            done_percent=done_percent,
        )

    async def get_stats_by_day(self, user_id: UUID) -> TaskStatsByDayDTO:
        """Возвращает статистику задач, сгруппированную по дням создания."""
        stmt = (
            select(
                func.date(Task.created_at).label('day'),
                func.count().label('total_count'),
                func.sum(case((Task.is_done.is_(True), 1), else_=0)).label(
                    'done_count'
                ),
                func.sum(case((Task.is_done.is_(False), 1), else_=0)).label(
                    'not_done_count'
                ),
            )
            .where(Task.user_id == user_id)
            .group_by('day')
            .order_by('day')
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        items = [
            TaskStatsByDayItemDTO(
                day=row.day,
                total_count=row.total_count,
                done_count=row.done_count or 0,
                not_done_count=row.not_done_count or 0,
            )
            for row in rows
        ]
        return TaskStatsByDayDTO(items=items)

    async def get_active_users(self, limit: int = 10) -> TaskActiveUsersDTO:
        """
        Возвращает топ пользователей по числу невыполненных задач
        (is_done=False).
        """
        # Подсчёт невыполненных задач по каждому пользователю
        stmt = (
            select(
                User.id.label('user_id'),
                User.username,
                User.email,
                func.count(Task.id).label('open_tasks'),
            )
            .join(Task, User.id == Task.user_id)
            .where(Task.is_done == False)  # noqa: E712
            .group_by(User.id, User.username, User.email)
            .order_by(desc('open_tasks'))
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        items = [
            TaskActiveUserDTO(
                user_id=row.user_id,
                username=row.username,
                email=row.email,
                open_tasks=row.open_tasks,
            )
            for row in rows
        ]
        return TaskActiveUsersDTO(items=items)
