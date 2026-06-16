from dataclasses import dataclass, field


@dataclass
class Bidder:
    bidderId: int
    name: str
    itemsWon: list[int] = field(default_factory=list)
    totalOwed: float = 0.0
    paid: bool = False  # set True when the bidder has been checked out

    def to_dict(self) -> dict:
        return {
            "bidderId": self.bidderId,
            "name": self.name,
            "itemsWon": list(self.itemsWon),
            "totalOwed": self.totalOwed,
            "paid": self.paid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bidder":
        return cls(
            bidderId=data["bidderId"],
            name=data["name"],
            itemsWon=list(data.get("itemsWon", [])),
            totalOwed=data.get("totalOwed", 0.0),
            paid=data.get("paid", False),
        )
