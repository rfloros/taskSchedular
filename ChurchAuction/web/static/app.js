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
async function refreshSummary() {
  const s = await api("/api/summary");
  $("#summary").innerHTML =
    `<span>Items: ${s.soldItems}/${s.totalItems} sold</span>` +
    `<span>Bidders: ${s.checkedOut}/${s.totalBidders} checked out</span>` +
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

async function refreshBidders() {
  const bidders = await api("/api/bidders");
  const items = await api("/api/items");
  const nameByItem = Object.fromEntries(items.map((i) => [i.itemNumber, i.name]));

  $("#bidders-table tbody").innerHTML = bidders
    .map((b) => {
      const won = b.itemsWon.map((id) => nameByItem[id] || `#${id}`).join(", ");
      const status = b.paid ? `<span class="pill paid">checked out</span>` : `<span class="pill due">due</span>`;
      return `<tr><td>${b.bidderId}</td><td>${b.name}</td><td>${won}</td><td>${money(b.totalOwed)}</td><td>${status}</td></tr>`;
    })
    .join("");

  $("#checkout-table tbody").innerHTML = bidders
    .map((b) => {
      const status = b.paid ? `<span class="pill paid">checked out</span>` : `<span class="pill due">due</span>`;
      const checkoutBtn = b.paid
        ? `<button class="secondary" disabled>Done</button>`
        : `<button data-checkout="${b.bidderId}">Check out</button>`;
      return `<tr><td>${b.bidderId}</td><td>${b.name}</td><td>${money(b.totalOwed)}</td><td>${status}</td>` +
        `<td><a class="btn" href="/api/bidders/${b.bidderId}/receipt" target="_blank">Receipt</a> ${checkoutBtn}</td></tr>`;
    })
    .join("");

  document.querySelectorAll("[data-checkout]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await api(`/api/bidders/${btn.dataset.checkout}/checkout`, { method: "POST" });
        toast("Bidder checked out");
        await refreshAll();
      } catch (e) { toast(e.message, false); }
    });
  });
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
