"""Strategy contract of the fixture repo."""
from typing import Protocol


class Greeting(Protocol):
    def greet(self, name: str) -> str:
        ...
