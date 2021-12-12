import dataclasses


@dataclasses.dataclass
class Connection:
    login: str
    logged_in: bool
    is_user: bool = False
    logged_with_password: bool = None
    computer_hash_key: str = None
