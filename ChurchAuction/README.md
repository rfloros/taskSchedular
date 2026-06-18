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

## Running the auction on event day (one laptop, several devices)

The whole event runs on **one host laptop** that holds the data. Other devices
(phones, tablets, laptops) on the **same WiFi** open the website in a browser and
all share the same auction — set up a check-in desk, a sales desk, and a checkout
desk if you like. Changes made on one device appear on the others within a few
seconds automatically (the screens re-poll every 4s).

1. **Start it** — on the host laptop, double-click **`start-auction.bat`**. A black
   window opens, the website opens in the laptop's browser, and the window prints
   the laptop's WiFi address(es). **Minimize that window — don't close it** (closing
   it stops the server for everyone).
2. **First-time firewall prompt** — the first time it runs, Windows may ask to allow
   Python through the firewall. Click **Allow access** (leave **Private networks**
   checked), or other devices won't be able to connect.
3. **Connect other devices** — on each device's browser, type the host laptop's
   address followed by `:8000`, e.g. `http://192.168.1.2:8000`. The launcher window
   shows the current address. You can also use the laptop's name:
   `http://<COMPUTER-NAME>:8000`.

**Keep the address stable:** a laptop's WiFi IP can change between days. Easiest
fix is to use the laptop **name** (`http://<COMPUTER-NAME>:8000`), which doesn't
change. For a fixed number, add a **DHCP reservation** for the laptop in the
router so it always gets the same IP.

> All data lives only on the host laptop (`data/auction_state.json`). Other devices
> just view and edit it over the WiFi — nothing is stored on them, and nothing
> leaves the building (no internet required).

## Run the CLI (optional)

```
python cli.py
```

## Excel format

- **Import** expects an `Items` sheet (or first sheet) with columns
  `ItemId`, `Name`, `Type` (case/space-insensitive). Sale columns are ignored.
- **Export** writes `Items` and `Bidders` sheets with prices as real numbers
  (currency-formatted), so the file is clean and re-importable.
