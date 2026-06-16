"""Command-line interface for quick testing without the browser.

State is the JSON store (auto-saved after every change); Excel is import/export
only. The web UI (web/app.py) is the primary interface.
"""

from auction import excel_io, receipts, storage


def print_menu():
    print("\n==== Auction Menu ====")
    print("1. Add Item")
    print("2. Check In Bidder")
    print("3. Record Sale")
    print("4. Bidder Receipt (PDF + text)")
    print("5. Check Out Bidder")
    print("6. Auction Summary")
    print("7. Import Items from Excel")
    print("8. Export Results to Excel")
    print("9. Exit")


def getInt(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a valid number.")


def getFloat(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Please enter a valid price.")


def getType(prompt: str) -> str:
    while True:
        value = input(prompt).strip().lower()
        if value in ("live", "silent"):
            return value
        print("Please enter 'live' or 'silent'.")


def main():
    auction = storage.load_auction()
    print(f"Loaded {len(auction.items)} items, {len(auction.bidders)} bidders.")

    while True:
        print_menu()
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                auction.addItem(getInt("Item Number: "), input("Item Name: "),
                                getType("Item Type (live/silent): "))
                storage.save_auction(auction)
                print("Item added.")

            elif choice == "2":
                auction.checkInBidder(getInt("Bidder ID: "), input("Bidder Name: "))
                storage.save_auction(auction)
                print("Bidder checked in.")

            elif choice == "3":
                auction.recordSale(getInt("Item Number: "), getInt("Winning Bidder ID: "),
                                   getFloat("Sale Price: "))
                storage.save_auction(auction)
                print("Sale recorded.")

            elif choice == "4":
                bidderId = getInt("Bidder ID: ")
                print(auction.getBidderReceipt(bidderId))
                path = f"receipt_{bidderId}.pdf"
                with open(path, "wb") as f:
                    f.write(receipts.bidder_receipt_pdf(auction, bidderId))
                print(f"PDF written to {path}")

            elif choice == "5":
                auction.checkout(getInt("Bidder ID: "))
                storage.save_auction(auction)
                print("Bidder checked out.")

            elif choice == "6":
                print(auction.getAuctionSummary())

            elif choice == "7":
                filename = input("Excel file to import items from: ").strip()
                added = 0
                for item in excel_io.import_items(filename):
                    if item.itemNumber not in auction.items:
                        auction.items[item.itemNumber] = item
                        added += 1
                storage.save_auction(auction)
                print(f"Imported {added} new items.")

            elif choice == "8":
                filename = input("Excel file to export to: ").strip()
                excel_io.export_auction(auction, filename)
                print(f"Exported to {filename}.")

            elif choice == "9":
                print("Exiting. (All changes already saved.)")
                break

            else:
                print("Invalid option.")

        except ValueError as e:
            print("Error:", e)
        except Exception as e:
            print("Unexpected error:", e)


if __name__ == "__main__":
    main()
