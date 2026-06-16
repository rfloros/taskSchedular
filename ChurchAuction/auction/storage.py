"""JSON persistence — the live source of truth during an event.

The web/CLI layer calls `save_auction` after every mutation so a crash never
loses data and a bidder can be checked out at any moment. Writes are atomic
(temp file + replace) to avoid a corrupted file if the process dies mid-write.
"""

import json
import os
import tempfile

from auction.auction import Auction

DEFAULT_PATH = os.path.join("data", "auction_state.json")


def save_auction(auction: Auction, path: str = DEFAULT_PATH) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    data = auction.to_dict()
    # Atomic write: dump to a temp file in the same dir, then replace.
    fd, tmp_path = tempfile.mkstemp(dir=directory or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def load_auction(path: str = DEFAULT_PATH) -> Auction:
    """Load saved state, or return a fresh empty Auction if none exists."""
    if not os.path.exists(path):
        return Auction()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Auction.from_dict(data)
