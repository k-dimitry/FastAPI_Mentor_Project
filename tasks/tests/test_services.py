from datetime import datetime, timezone
from uuid import uuid4

import pytest
import time_machine

from tasks.dto import TaskCreateDTO, TaskUpdateDTO
from tasks.exceptions import TaskAlreadyExistsError
from tasks.models import Task

pytestmark = pytest.mark.asyncio


class TestTaskServiceCreate:
    async def test_create_task_success(self, service, user):
        dto = TaskCreateDTO(title='Test', description='desc')

        result = await service.create_task(dto, user_id=user.id)

        assert result.title == 'Test'
        assert result.description == 'desc'
        assert result.is_done is False
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None

        task_in_db = await service.db.get(Task, result.id)
        assert task_in_db is not None
        assert task_in_db.title == 'Test'
        assert task_in_db.description == 'desc'
        assert task_in_db.is_done is False
        assert task_in_db.user_id == user.id

    async def test_create_task_without_description(self, service, user):
        dto = TaskCreateDTO(title='No description')

        result = await service.create_task(dto, user_id=user.id)

        assert result.description is None

        task_in_db = await service.db.get(Task, result.id)
        assert task_in_db.description is None

    @time_machine.travel(
        datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc),
        tick=False,
    )
    async def test_create_task_timestamps(self, service, user):
        dto = TaskCreateDTO(title='Timed')
        expected = datetime(2026, 8, 30, 12, 30, tzinfo=timezone.utc)

        result = await service.create_task(dto, user_id=user.id)
        task_in_db = await service.db.get(Task, result.id)

        assert result.created_at == expected
        assert result.updated_at == expected
        assert task_in_db.created_at == expected
        assert task_in_db.updated_at == expected


class TestTaskServiceDuplicate:
    async def test_create_duplicate_title_same_user(
        self, service, user, created_task
    ):
        dto = TaskCreateDTO(title=created_task.title)

        with pytest.raises(TaskAlreadyExistsError):
            await service.create_task(dto, user_id=user.id)

    async def test_create_same_title_different_users(
        self, service, user, other_user
    ):
        title = 'Shared title'
        dto = TaskCreateDTO(title=title)

        await service.create_task(dto, user_id=user.id)
        result = await service.create_task(dto, user_id=other_user.id)

        assert result.title == title


class TestTaskServiceRead:
    async def test_get_all_tasks_pagination(self, service, user, five_tasks):
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

        first = result.items[0]
        assert first.id is not None
        assert first.title == 'Task 1'
        assert first.description is None
        assert first.is_done is False
        assert first.created_at is not None
        assert first.updated_at is not None

    async def test_get_task_by_id(self, service, created_task, user):
        found = await service.get_task(created_task.id, user.id)

        assert found is not None
        assert found.id == created_task.id
        assert found.title == created_task.title
        assert found.description == created_task.description
        assert found.is_done == created_task.is_done
        assert found.created_at == created_task.created_at
        assert found.updated_at == created_task.updated_at

    async def test_get_task_by_id_foreign(
        self, service, created_task, other_user
    ):
        found = await service.get_task(created_task.id, other_user.id)

        assert found is None

    async def test_get_task_by_id_nonexistent(self, service, user):
        found = await service.get_task(uuid4(), user.id)

        assert found is None


class TestTaskServiceUpdate:
    @time_machine.travel(
        datetime(2030, 1, 1, 0, 0, tzinfo=timezone.utc),
        tick=False,
    )
    async def test_update_task_title(self, service, created_task, user):
        dto = TaskUpdateDTO(title='Updated')
        expected_updated = datetime(2030, 1, 1, 0, 0, tzinfo=timezone.utc)

        updated = await service.update_task(
            created_task.id, dto, user_id=user.id
        )

        assert updated is not None
        assert updated.title == 'Updated'
        assert updated.description == created_task.description
        assert updated.is_done == created_task.is_done
        assert updated.created_at == created_task.created_at
        assert updated.updated_at == expected_updated
        assert updated.updated_at != created_task.updated_at
        assert updated.updated_at > created_task.updated_at

        service.db.expire_all()
        task_in_db = await service.db.get(Task, created_task.id)
        assert task_in_db.title == 'Updated'
        assert task_in_db.description == created_task.description
        assert task_in_db.created_at == created_task.created_at
        assert task_in_db.updated_at == expected_updated

    async def test_update_task_description(self, service, created_task, user):
        dto = TaskUpdateDTO(description='new desc')

        updated = await service.update_task(
            created_task.id, dto, user_id=user.id
        )

        assert updated.description == 'new desc'
        assert updated.title == created_task.title
        assert updated.is_done == created_task.is_done

        service.db.expire_all()
        task_in_db = await service.db.get(Task, created_task.id)
        assert task_in_db.description == 'new desc'
        assert task_in_db.title == created_task.title
        assert task_in_db.is_done == created_task.is_done

    async def test_update_task_clear_description(
        self, service, created_task, user
    ):
        """PATCH с description=None должен стереть описание."""
        dto = TaskUpdateDTO(description=None)

        updated = await service.update_task(
            created_task.id, dto, user_id=user.id
        )

        assert updated.description is None
        assert updated.title == created_task.title

        service.db.expire_all()
        task_in_db = await service.db.get(Task, created_task.id)
        assert task_in_db.description is None
        assert task_in_db.title == created_task.title
        assert task_in_db.is_done == created_task.is_done

    async def test_update_task_is_done(self, service, created_task, user):
        dto = TaskUpdateDTO(is_done=True)

        updated = await service.update_task(
            created_task.id, dto, user_id=user.id
        )

        assert updated.is_done is True
        assert updated.title == created_task.title
        assert updated.description == created_task.description

        service.db.expire_all()
        task_in_db = await service.db.get(Task, created_task.id)
        assert task_in_db.is_done is True
        assert task_in_db.title == created_task.title
        assert task_in_db.description == created_task.description

    async def test_update_task_unset_fields_not_changed(
        self, service, created_task, user
    ):
        """Поля, не переданные в DTO (UNSET), не должны изменяться."""
        dto = TaskUpdateDTO(title='Only title')

        updated = await service.update_task(
            created_task.id, dto, user_id=user.id
        )

        assert updated.title == 'Only title'
        assert updated.description == created_task.description
        assert updated.is_done == created_task.is_done

        service.db.expire_all()
        task_in_db = await service.db.get(Task, created_task.id)
        assert task_in_db.title == 'Only title'
        assert task_in_db.description == created_task.description
        assert task_in_db.is_done == created_task.is_done

    async def test_update_task_foreign(self, service, created_task, other_user):
        dto = TaskUpdateDTO(title='Hacked')

        updated = await service.update_task(
            created_task.id, dto, user_id=other_user.id
        )

        assert updated is None

        task_in_db = await service.db.get(Task, created_task.id)
        assert task_in_db.title == created_task.title

    async def test_update_task_nonexistent(self, service, user):
        dto = TaskUpdateDTO(title='Whatever')

        updated = await service.update_task(uuid4(), dto, user_id=user.id)

        assert updated is None

    async def test_update_task_updated_at_changes(
        self, service, created_task, user
    ):
        """updated_at должен измениться после PATCH."""
        dto = TaskUpdateDTO(title='After update')

        updated = await service.update_task(
            created_task.id, dto, user_id=user.id
        )

        assert updated.updated_at >= created_task.updated_at


class TestTaskServiceDelete:
    async def test_delete_task(self, service, created_task, user):
        deleted = await service.delete_task(created_task.id, user_id=user.id)

        assert deleted is True
        task_in_db = await service.db.get(Task, created_task.id)
        assert task_in_db is None

    async def test_delete_task_foreign(self, service, created_task, other_user):
        deleted = await service.delete_task(
            created_task.id, user_id=other_user.id
        )

        assert deleted is False
        task_in_db = await service.db.get(Task, created_task.id)
        assert task_in_db is not None

    async def test_delete_task_nonexistent(self, service, user):
        deleted = await service.delete_task(uuid4(), user_id=user.id)

        assert deleted is False

class TestTaskServiceFilter:
    async def test_filter_tasks_by_is_done(
        self, service, user, tasks_with_mixed_done
    ):
        result = await service.get_all_tasks(user_id=user.id, is_done=True)

        assert result.total == 1
        assert len(result.items) == 1
        task = result.items[0]
        assert task.title == 'Done'
        assert task.is_done is True

    async def test_filter_tasks_by_is_done_false(
        self, service, user, tasks_with_mixed_done
    ):
        result = await service.get_all_tasks(user_id=user.id, is_done=False)

        assert result.total == 1
        assert result.items[0].title == 'Not Done'
        assert result.items[0].is_done is False
