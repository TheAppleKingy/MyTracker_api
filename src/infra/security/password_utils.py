from passlib.context import CryptContext


context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str):
    return context.hash(password)


def check_password(password: str, hashed: str):
    return context.verify(password, hashed)


def is_hashed(string: str):
    return context.identify(string) is not None
