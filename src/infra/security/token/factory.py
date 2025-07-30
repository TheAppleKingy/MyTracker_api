import config

from .jwt_handler import JWTHandler
from .serializer_handler import SerializerTokenHandler


class TokenHandlerFactory:
    @classmethod
    def get_jwt_handler(cls, exp: int = config.TOKEN_EXPIRE_TIME):
        return JWTHandler(exp)

    @classmethod
    def get_serializer_token_handler(cls, exp: int = config.URL_EXPIRE_TIME, salt: str = config.TOKEN_SALT):
        return SerializerTokenHandler(exp, salt)
