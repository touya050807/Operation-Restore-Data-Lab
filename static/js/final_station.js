/* ============================================================================
   final_station.js — Final Mission Station: pilih kelompok yang sedang
   diproses, input Mission Code 1-5, verifikasi otomatis -> Final Code.
   Setelah selesai, panitia dapat memproses kelompok lain tanpa perlu
   masuk ulang ke station (tanpa password lagi).
   ============================================================================ */

document.addEventListener("DOMContentLoaded", () => {
  initParticles();

  const verifyBtn = document.getElementById("verifyBtn");
  verifyBtn.addEventListener("click", handleVerify);
  document.getElementById("processAnotherBtn").addEventListener("click", resetForm);
});

async function handleVerify() {
  const payload = {};
  for (let i = 1; i <= 5; i++) payload[`code${i}`] = document.getElementById(`code${i}`).value;

  document.getElementById("verifyBtn").disabled = true;
  document.getElementById("scanOverlay").classList.add("show");
  await playTerminalLines("terminalLines", [
    "> Menerima input Mission Code...",
    "> Memeriksa keabsahan kode...",
    "> Memastikan seluruh kode dari kelompok yang sama...",
    "> Verifying..."
  ], 500);

  try {
    const res = await fetch("/api/station/final/verify", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const ct = res.headers.get("content-type") || "";
    const data = ct.includes("json") ? await res.json() : { success: false, reason: "technical" };
    document.getElementById("scanOverlay").classList.remove("show");

    const box = document.getElementById("resultBox");
    box.style.display = "flex";

    if (data.success) {
      playSuccessSound();
      box.innerHTML = `
        <span class="text-online" style="font-size:1.3rem;">●</span>
        <div>
          <b>✅ All Mission Codes Verified</b>
          <p style="margin:4px 0 0;">Final Code: <span class="mono text-online" style="font-size:1.2rem; letter-spacing:.1em;">${escapeHtmlFS(data.final_code)}</span></p>
          <p class="mono text-muted" style="font-size:.75rem; margin-top:8px;">Final Code ini sama untuk semua kelompok. Berikan ke kelompok untuk membuka Website Final Mission.</p>
        </div>`;
      document.getElementById("processAnotherRow").style.display = "flex";
    } else {
      playErrorSound();
      let message = "Kode belum berhasil diperiksa. Isian kodemu tidak dihapus; coba lagi.";
      let title = "❌ Verification Failed";
      if (["locked", "not_logged_in", "role_not_selected", "forbidden", "technical"].includes(data.reason)) {
        title = "⚠ Pemeriksaan gagal (bukan kode salah)";
        message = data.reason === "locked" ? "Station terkunci. Buka dengan password station lalu coba lagi."
          : data.reason === "technical" ? "Server tidak dapat memeriksa kode saat ini. Coba lagi."
          : "Sesi panitia bermasalah. Masuk ulang sebagai panitia lalu coba lagi.";
      }
      if (data.reason === "invalid_code") message = "Salah satu atau lebih kode tidak dikenali sistem.";
      else if (data.reason === "incomplete") message = "Pastikan kelima kode terisi dan tidak ada yang duplikat.";
      else if (data.reason === "missing_mission") message = "Kode tidak mencakup seluruh mission aktif.";

      box.innerHTML = `
        <span class="text-offline" style="font-size:1.3rem;">✕</span>
        <div><b>${title}</b><p style="margin:4px 0 0;">${message}</p></div>`;
      verifyBtn.disabled = false;
    }
  } catch (err) {
    document.getElementById("scanOverlay").classList.remove("show");
    await showResultOverlay({ type: "error", title: "Koneksi bermasalah.", subtitle: "Kode belum diperiksa; isianmu tetap ada. Coba lagi." });
    document.getElementById("verifyBtn").disabled = false;
  }
}

function resetForm() {
  for (let i = 1; i <= 5; i++) document.getElementById(`code${i}`).value = "";
  document.getElementById("resultBox").style.display = "none";
  document.getElementById("processAnotherRow").style.display = "none";
  document.getElementById("verifyBtn").disabled = false;
}

function escapeHtmlFS(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
