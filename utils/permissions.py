from core.exceptions import HTTP403
from models import User
from schemas.user import UserOut


def can_change_other_su(current_user: User, target_user: UserOut) -> None:
    """
    :param current_user: текущий пользователь
    :param target_user: пользователь, которого хотим изменить
    :return: None. Бросит 403, если целевой пользователь SU и мы не являемся целевым пользователем
    """
    if target_user.is_superuser and current_user.id != target_user.id:
        raise HTTP403("Can't change another superuser")