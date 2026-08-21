from urllib.parse import urlencode

from fastapi import Request


def get_pagination_urls(
    request: Request,
    page: int,
    size: int,
    total: int,
) -> tuple[str | None, str | None]:
    """
    Возвращает URL-адреса для следующей и предыдущей страниц.

    :param request: Объект запроса FastAPI
    для получения базового URL и параметров.
    :param page: Текущая страница.
    :param size: Количество элементов на странице.
    :param total: Общее количество элементов.
    :return: Кортеж (next_url, previous_url). Значение None, если страницы нет.
    """
    next_url = None
    previous_url = None

    if page * size < total:
        query_params = dict(request.query_params)
        query_params['page'] = str(page + 1)
        query_params['size'] = str(size)
        next_url = str(request.url.replace(query=urlencode(query_params)))

    if page > 1:
        query_params = dict(request.query_params)
        query_params['page'] = str(page - 1)
        query_params['size'] = str(size)
        previous_url = str(request.url.replace(query=urlencode(query_params)))

    return next_url, previous_url
