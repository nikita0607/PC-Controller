import dataclasses


@dataclasses.dataclass
class Connection:
    login: str
    registered_user: bool
    access_level: int
