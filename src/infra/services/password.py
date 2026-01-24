from passlib.context import CryptContext


class PasswordService:
    def __init__(self):
        self._context = CryptContext(
            schemes=["pbkdf2_sha256"],
            pbkdf2_sha256__default_rounds=300000,
            pbkdf2_sha256__salt_size=16,
            deprecated="auto"
        )

    def hash_password(self, raw_password: str) -> str:
        return self._context.hash(raw_password)

    def check_password(self, hashed: str, checking: str) -> bool:
        return self._context.verify(checking, hashed)
