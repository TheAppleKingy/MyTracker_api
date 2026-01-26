class HandledError(Exception):
    def __init__(self, *args, status: int = 400):
        super().__init__(*args)
        self.status = status


class DomainError(HandledError):
    pass
