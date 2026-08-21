from urllib.parse import urlencode

from fastapi import Request


def get_pagination_urls(
    request: Request,
    offset: int,
    limit: int,
    total: int,
) -> tuple[str | None, str | None]:
    """
    Возвращает URL-адреса для следующей и предыдущей страниц
    на основе limit/offset.

    :param request: Объект запроса FastAPI.
    :param offset: Текущее смещение.
    :param limit: Количество элементов на странице.
    :param total: Общее количество элементов.
    :return: Кортеж (next_url, previous_url). None, если страницы нет.
    """
    next_url = None
    previous_url = None

    if offset + limit < total:
        params = dict(request.query_params)
        params['offset'] = str(offset + limit)
        params['limit'] = str(limit)
        next_url = str(request.url.replace(query=urlencode(params)))

    if offset > 0:
        params = dict(request.query_params)
        new_offset = max(0, offset - limit)
        params['offset'] = str(new_offset)
        params['limit'] = str(limit)
        previous_url = str(request.url.replace(query=urlencode(params)))

    return next_url, previous_url
