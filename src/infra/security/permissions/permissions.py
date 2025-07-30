from domain.entities.users import User
from .abstract import AbstractPermission
from .exc import PermissionException


class IsActivePermission(AbstractPermission):
    def check_user(self, user: User):
        if not user.is_active:
            raise PermissionException('User is not active')
