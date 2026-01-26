from src.domain.exc import HandledError


class InfrastructureError(HandledError):
    def __init__(self, *args, status: int = 500):
        super().__init__(*args, status=status)
