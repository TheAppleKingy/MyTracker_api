import config

from typing import Sequence

from domain.entities.users import User
from .abstract import AbstractTokenHandler
from .exceptions import TokenError


class TokenHandler(AbstractTokenHandler):
    _secret = config.SECRET_KEY

    def __init__(self, expire_time: int, salt: str = config.TOKEN_SALT):
        self._salt = salt
        self._exp = expire_time

    def validate_token(self, token: str = None, fields_required: Sequence[str] = None):
        if not token:
            raise TokenError('token was not provide')
        decoded = self.decode(token)
        if fields_required:
            if not all([key in decoded.keys() for key in fields_required]):
                raise TokenError(
                    'provided token does not contain required info')
        return decoded

    def get_token_for_user(self, user: User):
        payload = {'user_id': user.id}
        return self.encode(payload)
