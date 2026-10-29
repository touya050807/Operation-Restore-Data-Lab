/* ============================================================================
   admin_settings.js — tambah/hapus baris kartu Final Mission secara dinamis
   ============================================================================ */

document.addEventListener("DOMContentLoaded", () => {
  initParticles();

  const rows = document.getElementById("fieldRows");
  const template = document.getElementById("fieldRowTemplate");
  const addBtn = document.getElementById("addFieldRowBtn");
  if (!rows || !template || !addBtn) return;     // halaman ini tidak lagi memuat editor baris kartu

  addBtn.addEventListener("click", () => {
    const clone = template.content.cloneNode(true);
    rows.appendChild(clone);
    attachRemoveHandlers();
  });

  function attachRemoveHandlers() {
    rows.querySelectorAll(".remove-field-row").forEach((btn) => {
      btn.onclick = () => btn.closest(".field-row").remove();
    });
  }
  attachRemoveHandlers();
});
