from dataclasses import dataclass, field

from auction.bidders import Bidder
from auction.items import Item


@dataclass
class Auction:
    """In-memory auction state. Pure domain logic, no file I/O.

    Persistence (JSON), Excel import/export, and PDF receipts live in the
    separate `storage`, `excel_io`, and `receipts` modules so this class stays
    the single source of truth during an event.
    """

    bidders: dict[int, Bidder] = field(default_factory=dict)
    items: dict[int, Item] = field(default_factory=dict)

    # ---------- Internal helpers ----------
    def _getItem(self, itemNumber: int) -> Item:
        if itemNumber not in self.items:
            raise ValueError(f"Item {itemNumber} does not exist")
        return self.items[itemNumber]

    def _getBidder(self, bidderId: int) -> Bidder:
        if bidderId not in self.bidders:
            raise ValueError(f"Bidder {bidderId} does not exist")
        return self.bidders[bidderId]

    def _ensureItemDoesNotExist(self, itemNumber: int):
        if itemNumber in self.items:
            raise ValueError(f"Item {itemNumber} already exists")

    def _ensureBidderDoesNotExist(self, bidderId: int):
        if bidderId in self.bidders:
            raise ValueError(f"Bidder {bidderId} already exists")

    # ---------- Setup ----------
    def addItem(self, itemNumber: int, name: str, itemType: str) -> Item:
        self._ensureItemDoesNotExist(itemNumber)
        item = Item(itemNumber, name, itemType)
        self.items[itemNumber] = item
        return item

    def checkInBidder(self, bidderId: int, name: str) -> Bidder:
        self._ensureBidderDoesNotExist(bidderId)
        bidder = Bidder(bidderId, name)
        self.bidders[bidderId] = bidder
        return bidder

    def reset(self):
        """Clear all items and bidders to start a fresh auction."""
        self.items.clear()
        self.bidders.clear()

    # ---------- Core transaction ----------
    def recordSale(self, itemNumber: int, bidderId: int, salePrice: float):
        item = self._getItem(itemNumber)
        bidder = self._getBidder(bidderId)

        if item.winnerId is not None:
            raise ValueError("Item already sold")
        if salePrice <= 0:
            raise ValueError("Sale price must be positive")

        item.salePrice = salePrice
        item.winnerId = bidderId
        bidder.itemsWon.append(itemNumber)
        bidder.totalOwed += salePrice

    def undoSale(self, itemNumber: int):
        """Reverse a recorded sale (e.g. a fat-fingered price or wrong bidder)."""
        item = self._getItem(itemNumber)
        if item.winnerId is None:
            raise ValueError("Item has not been sold")

        bidder = self._getBidder(item.winnerId)
        bidder.itemsWon.remove(itemNumber)
        bidder.totalOwed -= item.salePrice or 0.0
        # Drop any "handed over" record so a reversed sale leaves no phantom.
        # (amountPaid is left as-is; refunds are handled off-system.)
        if itemNumber in bidder.settledItems:
            bidder.settledItems.remove(itemNumber)

        item.salePrice = None
        item.winnerId = None

    def checkout(self, bidderId: int) -> Bidder:
        """Settle a bidder's current balance and hand over their items.

        Sets amountPaid to the full total and snapshots every item won so far as
        collected. If the bidder later wins more, the new items and balance are
        automatically outstanding again until this is called once more.
        """
        bidder = self._getBidder(bidderId)
        bidder.amountPaid = bidder.totalOwed
        bidder.settledItems = list(bidder.itemsWon)
        return bidder

    def undoCheckout(self, bidderId: int) -> Bidder:
        """Reverse a checkout (e.g. the wrong bidder was marked paid)."""
        bidder = self._getBidder(bidderId)
        bidder.amountPaid = 0.0
        bidder.settledItems = []
        return bidder

    # ---------- Data reports ----------
    def getBidderReceipt(self, bidderId: int) -> str:
        bidder = self._getBidder(bidderId)

        lines = [f"Receipt for {bidder.name} (Bidder ID: {bidder.bidderId})"]
        lines.append("Items Won:")

        if not bidder.itemsWon:
            lines.append(" - None")

        for itemNumber in bidder.itemsWon:
            item = self._getItem(itemNumber)
            price = item.salePrice or 0.0
            lines.append(f" - {item.name} (Item {item.itemNumber}): ${price:.2f}")

        lines.append(f"Total Owed: ${bidder.totalOwed:.2f}")
        return "\n".join(lines)

    def getAuctionSummary(self) -> str:
        lines = ["Auction Summary:"]

        for item in self.items.values():
            if item.winnerId is None:
                lines.append(f" - {item.name} (Item {item.itemNumber}): Not Sold")
            else:
                bidder = self._getBidder(item.winnerId)
                price = item.salePrice or 0.0
                lines.append(
                    f" - {item.name} (Item {item.itemNumber}): "
                    f"Sold to {bidder.name} for ${price:.2f}"
                )

        lines.append(f"\nTotal Revenue: ${self.getTotalRevenue():.2f}")
        return "\n".join(lines)

    def getTotalRevenue(self) -> float:
        return sum(
            item.salePrice for item in self.items.values() if item.salePrice is not None
        )

    # ---------- Serialization (used by storage.py) ----------
    def to_dict(self) -> dict:
        return {
            "items": [item.to_dict() for item in self.items.values()],
            "bidders": [bidder.to_dict() for bidder in self.bidders.values()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Auction":
        auction = cls()
        for item_data in data.get("items", []):
            item = Item.from_dict(item_data)
            auction.items[item.itemNumber] = item
        for bidder_data in data.get("bidders", []):
            bidder = Bidder.from_dict(bidder_data)
            auction.bidders[bidder.bidderId] = bidder
        return auction
