from dataclasses import dataclass, field


@dataclass
class Bidder:
    bidderId: int
    name: str
    itemsWon: list[int] = field(default_factory=list)
    totalOwed: float = 0.0
    amountPaid: float = 0.0  # money actually collected from this bidder
    settledItems: list[int] = field(default_factory=list)  # items handed over

    @property
    def balanceDue(self) -> float:
        """How much the bidder still owes (never negative-looking noise)."""
        return round(self.totalOwed - self.amountPaid, 2)

    @property
    def fullyPaid(self) -> bool:
        """True once everything owed has been collected."""
        return self.totalOwed > 0 and self.balanceDue <= 0

    @property
    def outstandingItems(self) -> list[int]:
        """Items won but not yet handed over (e.g. won after checkout)."""
        settled = set(self.settledItems)
        return [i for i in self.itemsWon if i not in settled]

    def to_dict(self) -> dict:
        return {
            "bidderId": self.bidderId,
            "name": self.name,
            "itemsWon": list(self.itemsWon),
            "totalOwed": self.totalOwed,
            "amountPaid": self.amountPaid,
            "settledItems": list(self.settledItems),
            # Derived fields, exposed so the frontend can render without recomputing.
            "balanceDue": self.balanceDue,
            "fullyPaid": self.fullyPaid,
            "outstandingItems": self.outstandingItems,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bidder":
        itemsWon = list(data.get("itemsWon", []))
        totalOwed = data.get("totalOwed", 0.0)

        # Migrate legacy saves that only had a boolean `paid` flag: a paid bidder
        # is treated as having paid their full balance with all items handed over.
        legacy_paid = data.get("paid", False)
        amountPaid = data.get("amountPaid")
        if amountPaid is None:
            amountPaid = totalOwed if legacy_paid else 0.0
        settledItems = data.get("settledItems")
        if settledItems is None:
            settledItems = list(itemsWon) if legacy_paid else []

        return cls(
            bidderId=data["bidderId"],
            name=data["name"],
            itemsWon=itemsWon,
            totalOwed=totalOwed,
            amountPaid=amountPaid,
            settledItems=list(settledItems),
        )
