"""FastAPI app wrapping the auction domain.

Holds one Auction in memory, loads saved state on startup, and auto-saves to
the JSON store after every mutation. Single-operator, single-laptop use.

Run with:  uvicorn web.app:app --reload
Then open: http://localhost:8000
"""

import io
import os
import tempfile
import threading

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auction import excel_io, receipts, storage

app = FastAPI(title="Church Auction")

# Single in-memory auction, persisted to JSON after every change.
auction = storage.load_auction()

# Serializes mutating requests. Several stations on the WiFi can hit the API at
# the same time; FastAPI runs these sync handlers in a threadpool, so without
# this lock two desks editing at once could race on the shared dicts or the
# JSON save. The lock is only held for the (fast) mutate-then-save section.
write_lock = threading.Lock()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def _save():
    storage.save_auction(auction)


# ---------- Request models ----------
class ItemIn(BaseModel):
    itemNumber: int
    name: str
    itemType: str = "silent"


class BidderIn(BaseModel):
    bidderId: int
    name: str


class SaleIn(BaseModel):
    itemNumber: int
    bidderId: int
    salePrice: float


# ---------- Items ----------
@app.get("/api/items")
def list_items():
    return [item.to_dict() for item in auction.items.values()]


@app.post("/api/items")
def add_item(item: ItemIn):
    with write_lock:
        try:
            created = auction.addItem(item.itemNumber, item.name, item.itemType)
        except ValueError as e:
            raise HTTPException(400, str(e))
        _save()
        return created.to_dict()


@app.post("/api/items/import")
async def import_items(file: UploadFile = File(...)):
    contents = await file.read()
    # openpyxl needs a real path or file-like; a BytesIO works.
    parsed = excel_io.import_items(io.BytesIO(contents))
    with write_lock:
        added, skipped = 0, 0
        for item in parsed:
            if item.itemNumber in auction.items:
                skipped += 1
                continue
            auction.items[item.itemNumber] = item
            added += 1
        _save()
        return {"added": added, "skipped": skipped, "total": len(auction.items)}


# ---------- Bidders ----------
@app.get("/api/bidders")
def list_bidders():
    return [bidder.to_dict() for bidder in auction.bidders.values()]


@app.post("/api/bidders")
def check_in_bidder(bidder: BidderIn):
    with write_lock:
        try:
            created = auction.checkInBidder(bidder.bidderId, bidder.name)
        except ValueError as e:
            raise HTTPException(400, str(e))
        _save()
        return created.to_dict()


@app.post("/api/bidders/{bidder_id}/checkout")
def checkout(bidder_id: int):
    with write_lock:
        try:
            bidder = auction.checkout(bidder_id)
        except ValueError as e:
            raise HTTPException(404, str(e))
        _save()
        return bidder.to_dict()


@app.post("/api/bidders/{bidder_id}/uncheckout")
def uncheckout(bidder_id: int):
    with write_lock:
        try:
            bidder = auction.undoCheckout(bidder_id)
        except ValueError as e:
            raise HTTPException(404, str(e))
        _save()
        return bidder.to_dict()


@app.get("/api/bidders/{bidder_id}/receipt")
def receipt(bidder_id: int):
    try:
        pdf = receipts.bidder_receipt_pdf(auction, bidder_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="receipt_{bidder_id}.pdf"'
        },
    )


# ---------- Sales ----------
@app.post("/api/sales")
def record_sale(sale: SaleIn):
    with write_lock:
        try:
            auction.recordSale(sale.itemNumber, sale.bidderId, sale.salePrice)
        except ValueError as e:
            raise HTTPException(400, str(e))
        _save()
        return auction.items[sale.itemNumber].to_dict()


@app.post("/api/sales/{item_number}/undo")
def undo_sale(item_number: int):
    with write_lock:
        try:
            auction.undoSale(item_number)
        except ValueError as e:
            raise HTTPException(400, str(e))
        _save()
        return auction.items[item_number].to_dict()


# ---------- Reset ----------
@app.post("/api/reset")
def reset_auction():
    """Clear all items and bidders to start a new auction."""
    with write_lock:
        auction.reset()
        _save()
        return {"status": "cleared"}


# ---------- Reports ----------
@app.get("/api/summary")
def summary():
    sold = [i for i in auction.items.values() if i.sold]
    bidders = auction.bidders.values()
    return {
        "totalItems": len(auction.items),
        "soldItems": len(sold),
        "totalBidders": len(auction.bidders),
        "fullyPaid": sum(1 for b in bidders if b.fullyPaid),
        "outstandingBidders": sum(1 for b in bidders if b.balanceDue > 0),
        "outstandingBalance": round(sum(b.balanceDue for b in bidders), 2),
        "totalRevenue": auction.getTotalRevenue(),
    }


@app.get("/api/export")
def export_xlsx():
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    excel_io.export_auction(auction, path)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="auction_results.xlsx",
    )


# Static frontend (mounted last so /api routes take priority).
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
