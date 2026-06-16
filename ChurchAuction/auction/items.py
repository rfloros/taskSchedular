from dataclasses import dataclass


@dataclass
class Item:
    itemNumber: int
    name: str
    itemType: str  # "live" or "silent"
    salePrice: float | None = None
    winnerId: int | None = None

    @property
    def sold(self) -> bool:
        return self.winnerId is not None

    def to_dict(self) -> dict:
        return {
            "itemNumber": self.itemNumber,
            "name": self.name,
            "itemType": self.itemType,
            "salePrice": self.salePrice,
            "winnerId": self.winnerId,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        return cls(
            itemNumber=data["itemNumber"],
            name=data["name"],
            itemType=data.get("itemType") or data.get("type") or "silent",
            salePrice=data.get("salePrice"),
            winnerId=data.get("winnerId"),
        )
