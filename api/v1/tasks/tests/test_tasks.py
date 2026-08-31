import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_tasks_authorized(client: AsyncClient, user_token):
    # Создадим пару задач для пользователя через API
    await client.post(
        '/api/v1/tasks/',
        headers={'Authorization': f'Bearer {user_token}'},
        json={'title': 'Task 1', 'description': 'desc'},
    )
    await client.post(
        '/api/v1/tasks/',
        headers={'Authorization': f'Bearer {user_token}'},
        json={'title': 'Task 2'},
    )
    response = await client.get(
        '/api/v1/tasks/',
        headers={'Authorization': f'Bearer {user_token}'},
    )
    assert response.status_code == 200
    data = response.json()
    assert 'result' in data
    assert data['count'] == 2
    assert len(data['result']) == 2


@pytest.mark.asyncio
async def test_get_tasks_unauthorized(client: AsyncClient):
    response = await client.get('/api/v1/tasks/')
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_task_success(client: AsyncClient, user_token):
    response = await client.post(
        '/api/v1/tasks/',
        headers={'Authorization': f'Bearer {user_token}'},
        json={'title': 'New task', 'description': 'desc'},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'New task'
    assert data['is_done'] is False


@pytest.mark.asyncio
async def test_create_task_unauthorized(client: AsyncClient):
    response = await client.post(
        '/api/v1/tasks/',
        json={'title': 'No auth'},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_patch_task_owner(client: AsyncClient, user_token):
    # Создаём задачу
    create_resp = await client.post(
        '/api/v1/tasks/',
        headers={'Authorization': f'Bearer {user_token}'},
        json={'title': 'Original', 'description': 'desc'},
    )
    task_id = create_resp.json()['id']
    # Обновляем свою задачу
    response = await client.patch(
        f'/api/v1/tasks/{task_id}',
        headers={'Authorization': f'Bearer {user_token}'},
        json={'title': 'Updated'},
    )
    assert response.status_code == 200
    assert response.json()['title'] == 'Updated'


@pytest.mark.asyncio
async def test_patch_task_foreign(client: AsyncClient, user_token, admin_token):
    # Создаём задачу от user
    create_resp = await client.post(
        '/api/v1/tasks/',
        headers={'Authorization': f'Bearer {user_token}'},
        json={'title': 'Mine'},
    )
    task_id = create_resp.json()['id']
    # Пытаемся обновить от admin (чужой пользователь)
    response = await client.patch(
        f'/api/v1/tasks/{task_id}',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'title': 'Hacked'},
    )
    assert (
        response.status_code == 404
    )  # наша логика отдаёт 404 для чужой задачи


@pytest.mark.asyncio
async def test_get_tasks_filter_is_done(client: AsyncClient, user_token):
    # Создаём выполненные и невыполненные задачи
    await client.post(
        '/api/v1/tasks/',
        headers={'Authorization': f'Bearer {user_token}'},
        json={'title': 'Done task', 'is_done': True},
    )
    await client.post(
        '/api/v1/tasks/',
        headers={'Authorization': f'Bearer {user_token}'},
        json={'title': 'Open task'},
    )
    # Запрос с is_done=true
    response = await client.get(
        '/api/v1/tasks/?is_done=true',
        headers={'Authorization': f'Bearer {user_token}'},
    )
    assert response.status_code == 200
    data = response.json()
    assert data['count'] == 1
    assert data['result'][0]['title'] == 'Done task'
