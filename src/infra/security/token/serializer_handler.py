from itsdangerous import URLSafeTimedSerializer, BadSignature

from domain.entities.users import User
from .base_handler import TokenHandler
from .exceptions import TokenError


class SerializerTokenHandler(TokenHandler):
    def encode(self, payload: dict):
        token_ser = URLSafeTimedSerializer(self._secret, self._salt)
        token = token_ser.dumps(payload)
        return token

    def decode(self, token: str) -> dict:
        token_ser = URLSafeTimedSerializer(self._secret, self._salt)
        try:
            payload = token_ser.loads(token, max_age=self._exp)
        except BadSignature as e:
            raise TokenError(str(e))
        return payload

    def make_disp_url_for_user(self, base_path: str, user: User):
        token = self.get_token_for_user(user)
        return base_path + token
