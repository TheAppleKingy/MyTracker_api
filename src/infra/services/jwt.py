import jwt

from .exceptions import JWTUnauthorizedError
from src.application.interfaces.services import AuthenticationServiceInterface


class JWTAuthenticationService(AuthenticationServiceInterface):
    def __init__(
        self,
        secret: str
    ):
        self._secret = secret

    def get_tg_name_from_token(self, token: str) -> str:
        try:
            payload = self.decode(token)
        except jwt.InvalidTokenError:
            raise JWTUnauthorizedError("Token invalid", status=401)
        return payload["tg_name"]

    def decode(self, token: str) -> dict:
        return jwt.decode(token, self._secret, ["HS256"], options={"require": ["tg_name"]})
