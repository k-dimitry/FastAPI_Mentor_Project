from uuid import UUID


def is_author_or_admin(
    current_user_id: UUID,
    target_user_id: UUID,
    is_admin: bool,
) -> bool:
    """Проверяет, может ли пользователь получить доступ к целевому объекту."""
    return current_user_id == target_user_id or is_admin
