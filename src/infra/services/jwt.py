import jwt
import time

from typing import Optional


from .exceptions import JWTUnauthorizedError
from src.application.interfaces.services import AuthenticationServiceInterface


class JWTAuthenticationService(AuthenticationServiceInterface):
    def __init__(
        self,
        secret: str
    ):
        self._secret = secret

    def get_tg_name_from_token(self, token: str) -> Optional[str]:
        try:
            payload = self.decode(token)
        except jwt.InvalidTokenError:
            raise JWTUnauthorizedError("Token invlaid", status=401)
        return payload.get("tg_name")

    def decode(self, token: str) -> dict:
        payload = jwt.decode(token, self._secret, ["HS256"])
        if not payload.get("exp", None):
            raise JWTUnauthorizedError("Untracked expiration of token", status=401)
        return payload
