from sqlalchemy import func, select

from notifications.tasks import generate_daily_stats
from tasks.dto import TaskCreateDTO, TaskUpdateDTO
from tasks.models import DailyStat


class TestGenerateDailyStats:
    async def test_upsert_same_date_updates_row(
        self, service, user, db_session
    ):
        user_id = user.id
        await service.create_task(TaskCreateDTO(title='Open'), user_id=user_id)
        done = await service.create_task(
            TaskCreateDTO(title='Done', is_done=True), user_id=user_id
        )

        first_id = generate_daily_stats()

        db_session.expire_all()
        rows = (await db_session.execute(select(DailyStat))).scalars().all()
        assert len(rows) == 1
        assert str(rows[0].id) == first_id
        assert rows[0].total == 2
        assert rows[0].done == 1
        assert rows[0].not_done == 1

        await service.update_task(
            done.id,
            TaskUpdateDTO(is_done=False),
            user_id=user_id,
        )

        second_id = generate_daily_stats()

        db_session.expire_all()
        rows = (await db_session.execute(select(DailyStat))).scalars().all()
        count = await db_session.scalar(
            select(func.count()).select_from(DailyStat)
        )
        assert second_id == first_id
        assert count == 1
        assert len(rows) == 1
        assert str(rows[0].id) == first_id
        assert rows[0].total == 2
        assert rows[0].done == 0
        assert rows[0].not_done == 2
