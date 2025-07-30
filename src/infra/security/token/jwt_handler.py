import jwt

from datetime import datetime, timezone, timedelta

from .exceptions import TokenError
from .base_handler import TokenHandler


class JWTHandler(TokenHandler):
    def encode(self, payload: dict):
        payload.update({'exp': datetime.now(
            timezone.utc) + timedelta(seconds=self._exp)})
        token = jwt.encode(payload, self._secret)
        return token

    def decode(self, token: str):
        try:
            payload = jwt.decode(token, self._secret, algorithms=['HS256'])
        except jwt.InvalidTokenError as e:
            raise TokenError(str(e))
        return payload
