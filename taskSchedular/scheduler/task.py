from dataclasses import dataclass, field
import time

@dataclass(order=True)
class Task:
    priority: int
    name: str = field(compare = False)
    notes: str = field(compare = False)
    createdAt: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        return f"Task(name={self.name}, priority={self.priority})"
    