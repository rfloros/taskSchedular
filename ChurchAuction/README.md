# Church Auction Management System

A simple, single-laptop tool for running a church auction: import the item
catalog from Excel, check bidders in, record sales, check bidders out at any
time during the event (printing a **PDF receipt**), and export results back to
Excel.

## Architecture

The **in-memory model is the source of truth**, auto-saved to a local JSON file
after every change (`data/auction_state.json`). Excel is used only to import the
catalog and export final reports — never as the live store. This makes
mid-event checkout instant and crash-safe.

```
auction/            Domain + services (no UI)
  items.py          Item dataclass
  bidders.py        Bidder dataclass (with paid/checked-out flag)
  auction.py        Auction — pure logic (add item, check in, record sale, checkout, reports)
  storage.py        JSON save/load — the live source of truth (atomic writes)
  excel_io.py       import_items() / export_auction() — numeric prices
  receipts.py       bidder_receipt_pdf() — one-page PDF via fpdf2
web/
  app.py            FastAPI: REST API + serves the frontend
  static/           index.html, app.js, style.css  (plain HTML/JS, no build step)
cli.py              Terminal interface for quick testing
data/               Auto-saved auction_state.json
```

## Setup

```
python -m pip install -r requirements.txt
```

## Run the web app (primary interface)

```
python -m uvicorn web.app:app --reload
```

Open http://localhost:8000 — tabs for Catalog, Check-In, Record Sale, and
Checkout. State reloads automatically if you restart the server.

## Run the CLI (optional)

```
python cli.py
```

## Excel format

- **Import** expects an `Items` sheet (or first sheet) with columns
  `ItemId`, `Name`, `Type` (case/space-insensitive). Sale columns are ignored.
- **Export** writes `Items` and `Bidders` sheets with prices as real numbers
  (currency-formatted), so the file is clean and re-importable.
