"""PDF bidder receipts using fpdf2 (lightweight, pure-Python)."""

from datetime import date

from fpdf import FPDF

from auction.auction import Auction

CHURCH_NAME = "Nativity of the Virgin Mary"


def bidder_receipt_pdf(
    auction: Auction, bidderId: int, church_name: str = CHURCH_NAME
) -> bytes:
    """Render a one-page PDF receipt for a bidder and return the bytes."""
    bidder = auction._getBidder(bidderId)

    pdf = FPDF(format="Letter")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Header
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, church_name, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, "Auction Receipt", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, date.today().strftime("%B %d, %Y"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Bidder info
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"{bidder.name}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Bidder ID: {bidder.bidderId}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Items table
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(25, 8, "Item #", border="B")
    pdf.cell(115, 8, "Item", border="B")
    pdf.cell(35, 8, "Price", border="B", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    if not bidder.itemsWon:
        pdf.cell(0, 8, "No items won.", new_x="LMARGIN", new_y="NEXT")
    for itemNumber in bidder.itemsWon:
        item = auction._getItem(itemNumber)
        price = item.salePrice or 0.0
        pdf.cell(25, 8, str(item.itemNumber))
        pdf.cell(115, 8, item.name)
        pdf.cell(35, 8, f"${price:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(140, 10, "Total Owed", border="T")
    pdf.cell(35, 10, f"${bidder.totalOwed:,.2f}", border="T", align="R",
             new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 10)
    status = "PAID - Thank you!" if bidder.paid else "Balance due at checkout."
    pdf.cell(0, 7, status, new_x="LMARGIN", new_y="NEXT")

    out = pdf.output()
    return bytes(out)
