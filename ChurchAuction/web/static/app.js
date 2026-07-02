// ---- helpers ----
const $ = (sel) => document.querySelector(sel);

function toast(msg, ok = true) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "show " + (ok ? "ok" : "err");
  setTimeout(() => (t.className = ""), 2600);
}

async function api(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (e) {}
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

const money = (n) => (n == null ? "" : "$" + Number(n).toFixed(2));

// ---- tabs ----
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    $("#" + btn.dataset.tab).classList.add("active");
  });
});

// ---- renderers ----
// A bidder's payment status has three states now: fully paid, partially paid
// (e.g. checked out then won more), or nothing paid yet.
function statusPill(b) {
  if (b.fullyPaid) return `<span class="pill paid">paid</span>`;
  if (b.amountPaid > 0) return `<span class="pill partial">owes ${money(b.balanceDue)}</span>`;
  return `<span class="pill due">due</span>`;
}

async function refreshSummary() {
  const s = await api("/api/summary");
  const owed = s.outstandingBidders > 0
    ? `<span>Outstanding: ${money(s.outstandingBalance)} from ${s.outstandingBidders}</span>`
    : `<span>Outstanding: none</span>`;
  $("#summary").innerHTML =
    `<span>Items: ${s.soldItems}/${s.totalItems} sold</span>` +
    `<span>Paid up: ${s.fullyPaid}/${s.totalBidders}</span>` +
    owed +
    `<span>Revenue: ${money(s.totalRevenue)}</span>`;
}

async function refreshItems() {
  const items = await api("/api/items");
  const bidders = await api("/api/bidders");
  const nameById = Object.fromEntries(bidders.map((b) => [b.bidderId, b.name]));
  $("#items-table tbody").innerHTML = items
    .map((i) => {
      const status = i.winnerId != null
        ? `<span class="pill sold">sold</span>`
        : `<span class="pill unsold">unsold</span>`;
      const winner = i.winnerId != null ? `${nameById[i.winnerId] || ""} (#${i.winnerId})` : "";
      const undoBtn = i.winnerId != null
        ? `<button class="secondary" data-undo="${i.itemNumber}">Undo sale</button>`
        : "";
      return `<tr><td>${i.itemNumber} ${status}</td><td>${i.name}</td><td>${i.itemType}</td>` +
        `<td>${money(i.salePrice)}</td><td>${winner}</td><td>${undoBtn}</td></tr>`;
    })
    .join("");

  document.querySelectorAll("[data-undo]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm(`Undo the sale for item #${btn.dataset.undo}?`)) return;
      try {
        await api(`/api/sales/${btn.dataset.undo}/undo`, { method: "POST" });
        toast("Sale undone");
        await refreshAll();
      } catch (e) { toast(e.message, false); }
    });
  });
}

// Checkout tab is master-detail: a bidder list plus a detail card for the one
// currently selected. We cache the last-fetched data so clicking a row (and the
// 4s poll) can redraw instantly without re-fetching, and keep the selection
// across polls so the open detail card doesn't collapse under someone's hands.
let selectedCheckoutId = null;
let lastBidders = [];
let lastItemById = {};

async function refreshBidders() {
  const bidders = await api("/api/bidders");
  const items = await api("/api/items");
  lastBidders = bidders;
  lastItemById = Object.fromEntries(items.map((i) => [i.itemNumber, i]));
  const nameByItem = Object.fromEntries(items.map((i) => [i.itemNumber, i.name]));

  $("#bidders-table tbody").innerHTML = bidders
    .map((b) => {
      const won = b.itemsWon.map((id) => nameByItem[id] || `#${id}`).join(", ");
      return `<tr><td>${b.bidderId}</td><td>${b.name}</td><td>${won}</td><td>${money(b.totalOwed)}</td><td>${statusPill(b)}</td></tr>`;
    })
    .join("");

  renderCheckout();
}

function renderCheckout() {
  $("#checkout-table tbody").innerHTML = lastBidders
    .map((b) => {
      const sel = b.bidderId === selectedCheckoutId ? " selected" : "";
      return `<tr class="checkout-row${sel}" data-select="${b.bidderId}">` +
        `<td>${b.bidderId}</td><td>${b.name}</td><td>${money(b.balanceDue)}</td><td>${statusPill(b)}</td></tr>`;
    })
    .join("");

  const bidder = lastBidders.find((b) => b.bidderId === selectedCheckoutId);
  $("#checkout-detail").innerHTML = bidder
    ? checkoutDetailHtml(bidder)
    : `<p class="hint">Select a bidder to check them out.</p>`;

  document.querySelectorAll("[data-select]").forEach((row) => {
    row.addEventListener("click", () => {
      selectedCheckoutId = Number(row.dataset.select);
      renderCheckout();
    });
  });

  document.querySelector("[data-markpaid]")?.addEventListener("click", async (e) => {
    try {
      await api(`/api/bidders/${e.target.dataset.markpaid}/checkout`, { method: "POST" });
      toast("Marked as paid");
      await refreshAll();
    } catch (err) { toast(err.message, false); }
  });

  document.querySelector("[data-uncheckout]")?.addEventListener("click", async (e) => {
    try {
      await api(`/api/bidders/${e.target.dataset.uncheckout}/uncheckout`, { method: "POST" });
      toast("Payment undone");
      await refreshAll();
    } catch (err) { toast(err.message, false); }
  });
}

function checkoutDetailHtml(b) {
  const items = b.itemsWon.map((id) => lastItemById[id]).filter(Boolean);
  const toCollect = new Set(b.outstandingItems || []);
  const rows = items.length
    ? items
        .map((i) => {
          const flag = toCollect.has(i.itemNumber)
            ? ` <span class="pill due">to collect</span>`
            : "";
          return `<div class="detail-item"><span>${i.name}${flag}</span>` +
            `<span>${money(i.salePrice)}</span></div>`;
        })
        .join("")
    : `<p class="hint">No items won.</p>`;

  const reminder = b.balanceDue > 0
    ? `<p class="charge-note">Charge ${money(b.balanceDue)} in Square, then mark as paid.</p>`
    : "";

  // Mark-as-paid whenever a balance is owed; only offer Undo to a bidder who has
  // actually paid something (a $0 bidder never checked out).
  let action = "";
  if (b.balanceDue > 0) {
    action = `<button data-markpaid="${b.bidderId}">Mark as paid</button>`;
  } else if (b.amountPaid > 0) {
    action = `<button class="secondary" data-uncheckout="${b.bidderId}">Undo checkout</button>`;
  }

  return `<div class="detail-name">${b.name}</div>` +
    `<div class="detail-sub">Bidder #${b.bidderId} ${statusPill(b)}</div>` +
    `<div class="detail-items">${rows}</div>` +
    `<div class="detail-line"><span>Total won</span><span>${money(b.totalOwed)}</span></div>` +
    `<div class="detail-line"><span>Paid</span><span>${money(b.amountPaid)}</span></div>` +
    `<div class="detail-total"><span>Balance due</span>` +
    `<span class="detail-total-amt">${money(b.balanceDue)}</span></div>` +
    reminder +
    `<div class="detail-actions">` +
    `<a class="btn secondary" href="/api/bidders/${b.bidderId}/receipt" target="_blank">Print receipt</a>` +
    action +
    `</div>`;
}

async function refreshAll() {
  await Promise.all([refreshSummary(), refreshItems(), refreshBidders()]);
}

// ---- forms ----
$("#item-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/items", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        itemNumber: Number($("#item-number").value),
        name: $("#item-name").value,
        itemType: $("#item-type").value,
      }),
    });
    e.target.reset();
    toast("Item added");
    await refreshAll();
  } catch (err) { toast(err.message, false); }
});

$("#import-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = $("#import-file").files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const r = await api("/api/items/import", { method: "POST", body: fd });
    toast(`Imported ${r.added} items (${r.skipped} skipped)`);
    e.target.reset();
    await refreshAll();
  } catch (err) { toast(err.message, false); }
});

$("#bidder-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/bidders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        bidderId: Number($("#bidder-id").value),
        name: $("#bidder-name").value,
      }),
    });
    e.target.reset();
    toast("Bidder checked in");
    await refreshAll();
  } catch (err) { toast(err.message, false); }
});

$("#sale-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/sales", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        itemNumber: Number($("#sale-item").value),
        bidderId: Number($("#sale-bidder").value),
        salePrice: Number($("#sale-price").value),
      }),
    });
    e.target.reset();
    toast("Sale recorded");
    await refreshAll();
  } catch (err) { toast(err.message, false); }
});

$("#clear-data-btn")?.addEventListener("click", () => {
  $("#clear-modal-overlay").hidden = false;
});

$("#clear-modal-cancel")?.addEventListener("click", () => {
  $("#clear-modal-overlay").hidden = true;
});

$("#clear-modal-overlay")?.addEventListener("click", (e) => {
  if (e.target.id === "clear-modal-overlay") $("#clear-modal-overlay").hidden = true;
});

$("#clear-modal-yes")?.addEventListener("click", async () => {
  try {
    await api("/api/reset", { method: "POST" });
    toast("All auction data cleared");
    await refreshAll();
  } catch (e) {
    toast(e.message, false);
  } finally {
    $("#clear-modal-overlay").hidden = true;
  }
});

// ---- init ----
refreshAll().catch((e) => toast(e.message, false));

// ---- live sync ----
// Several stations (check-in, sales, checkout) can run at once on the WiFi.
// Re-pull every few seconds so each screen sees the others' changes without a
// manual refresh. Only the tables/summary are redrawn -- form inputs are left
// untouched, so this won't wipe what someone is typing. Errors are swallowed so
// a brief network blip doesn't spam the toast.
setInterval(() => refreshAll().catch(() => {}), 4000);
