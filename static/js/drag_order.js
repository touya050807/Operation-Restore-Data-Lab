/* ============================================================================
   drag_order.js
   Widget "urutkan" (ordering) sederhana yang dipakai untuk tipe soal
   Ordering/Drag & Drop. Mendukung drag & drop mouse (native HTML5 DnD) DAN
   tombol naik/turun (selalu berfungsi, termasuk di HP/tablet panitia).
   ============================================================================ */

function initOrderList(containerId) {
  const list = document.getElementById(containerId);
  if (!list) return;
  let dragEl = null;

  list.querySelectorAll(".order-item").forEach((item) => {
    item.setAttribute("draggable", "true");
    item.addEventListener("dragstart", () => { dragEl = item; item.classList.add("dragging"); });
    item.addEventListener("dragend", () => { item.classList.remove("dragging"); dragEl = null; list.dataset.touched = "1"; });
    item.addEventListener("dragover", (e) => {
      e.preventDefault();
      const after = getDragAfterElement(list, e.clientY);
      if (dragEl == null) return;
      if (after == null) list.appendChild(dragEl);
      else list.insertBefore(dragEl, after);
    });
  });

  list.querySelectorAll(".move-up").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = btn.closest(".order-item");
      const prev = item.previousElementSibling;
      if (prev) { list.insertBefore(item, prev); list.dataset.touched = "1"; }
    });
  });
  list.querySelectorAll(".move-down").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = btn.closest(".order-item");
      const next = item.nextElementSibling;
      if (next) { list.insertBefore(next, item); list.dataset.touched = "1"; }
    });
  });
}

function getDragAfterElement(container, y) {
  const items = [...container.querySelectorAll(".order-item:not(.dragging)")];
  return items.reduce((closest, child) => {
    const box = child.getBoundingClientRect();
    const offset = y - box.top - box.height / 2;
    if (offset < 0 && offset > closest.offset) return { offset, element: child };
    return closest;
  }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function getOrderValues(containerId) {
  const list = document.getElementById(containerId);
  return [...list.querySelectorAll(".order-item")].map((el) => el.dataset.value);
}

/** Acak array (Fisher-Yates) — dipakai supaya urutan tampil ke peserta tidak selalu sama dgn jawaban benar. */
function shuffleArray(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
