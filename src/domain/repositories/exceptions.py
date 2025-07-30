def parse_integrity_err_message(msg: str):
    key_val_raw = msg.split('\n')[1]
    key, val = key_val_raw.split()[2].lstrip(
        '(').rstrip(')').replace(')=(', ' ').split()
    return key, val


class RepositoryError(Exception):
    ...


class TaskRepositoryError(RepositoryError):
    ...


class UserRepositoryError(RepositoryError):
    ...


class GroupRepositoryError(RepositoryError):
    ...
