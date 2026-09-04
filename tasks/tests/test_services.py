from uuid import uuid4

import pytest

from tasks.dto import TaskCreateDTO, TaskResponseDTO, TaskUpdateDTO
from tasks.exceptions import TaskAlreadyExistsError
from tasks.models import Task
from users.models import User

pytestmark = pytest.mark.asyncio


class TestTaskService:
    @pytest.fixture
    async def user(self, db_session):
        user = User(
            username='svc_user',
            email='svc@example.com',
            first_name='Svc',
            last_name='User',
            hashed_password='hashed',
            is_admin=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    async def test_create_task_success(self, service, user):
        dto = TaskCreateDTO(title='Test', description='desc')
        result = await service.create_task(dto, user_id=user.id)
        assert isinstance(result, TaskResponseDTO)
        assert result.title == 'Test'
        assert result.description == 'desc'
        assert result.is_done is False

        task_in_db = await service.db.get(Task, result.id)
        assert task_in_db is not None
        assert task_in_db.user_id == user.id

    async def test_create_task_duplicate(self, service, user):
        dto = TaskCreateDTO(title='Unique')
        await service.create_task(dto, user_id=user.id)
        with pytest.raises(TaskAlreadyExistsError):
            await service.create_task(dto, user_id=user.id)

    async def test_get_all_tasks_pagination(self, service, user):
        for i in range(5):
            await service.create_task(
                TaskCreateDTO(title=f'Task {i}'), user_id=user.id
            )

        # Используем сортировку по title, чтобы результат был детерминирован
        result = await service.get_all_tasks(
            user_id=user.id,
            limit=2,
            offset=1,
            order_by='title',
            direction='asc',
        )
        assert result.total == 5
        assert len(result.items) == 2
        assert result.limit == 2
        assert result.offset == 1
        titles = [item.title for item in result.items]
        assert titles == ['Task 1', 'Task 2']

    async def test_get_task_by_id(self, service, user):
        created = await service.create_task(
            TaskCreateDTO(title='Find me'), user_id=user.id
        )
        found = await service.get_task(created.id, user.id)
        assert found is not None
        assert found.id == created.id

        # Создаём другого пользователя и проверяем, что задача ему не доступна
        other_user = User(
            username='other',
            email='other@example.com',
            first_name='Other',
            last_name='User',
            hashed_password='hashed',
            is_admin=False,
        )
        service.db.add(other_user)
        await service.db.commit()
        await service.db.refresh(other_user)
        assert await service.get_task(created.id, other_user.id) is None

    async def test_update_task(self, service, user):
        created = await service.create_task(
            TaskCreateDTO(title='Old', description='old desc'),
            user_id=user.id,
        )
        update_dto = TaskUpdateDTO(title='New')
        updated = await service.update_task(
            created.id, update_dto, user_id=user.id
        )
        assert updated.title == 'New'
        assert updated.description == 'old desc'
        assert updated.is_done is False

        # Чужой пользователь
        other_user = User(
            username='other2',
            email='other2@example.com',
            first_name='Other',
            last_name='User',
            hashed_password='hashed',
            is_admin=False,
        )
        service.db.add(other_user)
        await service.db.commit()
        await service.db.refresh(other_user)

        # Для чужой задачи возвращается None
        assert (
            await service.update_task(
                created.id, update_dto, user_id=other_user.id
            )
            is None
        )

    async def test_delete_task(self, service, user):
        created = await service.create_task(
            TaskCreateDTO(title='ToDelete'), user_id=user.id
        )
        deleted = await service.delete_task(created.id, user_id=user.id)
        assert deleted is True
        assert await service.get_task(created.id, user.id) is None

        # Удаление несуществующей задачи (случайный UUID)
        assert await service.delete_task(uuid4(), user_id=user.id) is False

    async def test_filter_tasks_by_is_done(self, service, user):
        await service.create_task(
            TaskCreateDTO(title='Done', is_done=True), user_id=user.id
        )
        await service.create_task(
            TaskCreateDTO(title='Not Done', is_done=False), user_id=user.id
        )

        result = await service.get_all_tasks(user_id=user.id, is_done=True)
        assert result.total == 1
        assert result.items[0].title == 'Done'
