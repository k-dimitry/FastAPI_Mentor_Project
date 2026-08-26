from pydantic import BaseModel

from api.v1.tasks.stats.by_day.response import TaskStatsByDayResponse
from api.v1.tasks.stats.total.response import TaskStatsTotalResponse


class DashboardResponse(BaseModel):
    total: TaskStatsTotalResponse
    by_day: TaskStatsByDayResponse
