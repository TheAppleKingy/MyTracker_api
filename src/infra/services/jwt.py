import jwt
import time

from typing import Optional


from .exceptions import JWTUnauthorizedError
from src.application.interfaces.services import AuthenticationServiceInterface


class JWTAuthenticationService(AuthenticationServiceInterface):
    def __init__(
        self,
        exp_time: int,
        secret: str
    ):
        self._exp = exp_time
        self._secret = secret

    def generate_token(self, user_id: int, exp: Optional[int] = None) -> str:
        return self.encode({"user_id": user_id}, exp=exp)

    def get_tg_name_from_token(self, token: str) -> Optional[str]:
        try:
            payload = self.decode(token)
        except jwt.InvalidTokenError:
            raise JWTUnauthorizedError("Token invlaid", status=401)
        return payload.get("user_id")

    def decode(self, token: str) -> dict:
        return jwt.decode(token, self._secret, ["HS256"])

    def encode(self, payload: dict, exp: Optional[int] = None) -> str:
        payload.update({"exp": int(time.time() + (exp or self._exp))})
        return jwt.encode(
            payload=payload,
            key=self._secret,
            algorithm="HS256"
        )
