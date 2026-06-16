"""Church auction domain model and services.

Pure domain logic (`Item`, `Bidder`, `Auction`) plus I/O services kept separate
from the model: `storage` (JSON source of truth), `excel_io` (import/export),
and `receipts` (PDF generation).
"""

from auction.items import Item
from auction.bidders import Bidder
from auction.auction import Auction

__all__ = ["Item", "Bidder", "Auction"]
