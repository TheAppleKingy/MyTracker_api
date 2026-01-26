from src.infra.exc import InfrastructureError


class JWTUnauthorizedError(InfrastructureError):
    pass


class TokenError(InfrastructureError):
    pass
