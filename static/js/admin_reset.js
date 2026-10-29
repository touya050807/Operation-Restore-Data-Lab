/* admin_reset.js — dialog konfirmasi reset pengerjaan satu kelompok (Website 1). Eksekusi hanya setelah KONFIRMASI. */
document.addEventListener("DOMContentLoaded", () => {
  if (typeof initParticles === "function") initParticles();
  const $ = (id) => document.getElementById(id);
  const nums = JSON.parse($("groupsData").textContent), ov = JSON.parse($("overviewData").textContent);
  const info = {}; nums.forEach((n, i) => (info[n] = ov[i]));
  const sel = $("resetGroup"), dlg = $("resetDialog"); let busy = false;
  const label = () => sel.options[sel.selectedIndex].text;
  const showOverview = () => {
    const o = info[sel.value] || {};
    $("resetOverview").textContent = `Saat ini: ${o.answered || 0} soal terjawab (${o.correct || 0} benar), ${o.completed || 0} dari ${o.missions || 0} misi selesai.`;
  };
  const notice = (ok, text) => { $("resetNotice").className = "alert show " + (ok ? "alert-success" : "alert-error"); $("resetNotice").textContent = text; };
  sel.addEventListener("change", showOverview); showOverview();
  $("resetOpen").addEventListener("click", () => {
    $("resetDialogText").textContent = `Apakah Anda yakin ingin mereset seluruh pengerjaan ${label()} pada Website 1 — Main Website? ` +
      "Semua jawaban, poin, progres, status penyelesaian, dan Mission Code kelompok ini pada website tersebut akan direset. " +
      "Data kelompok lain, identitas kelompok, bank soal, serta data di Website 2 dan Website 3 tidak akan terpengaruh.";
    dlg.classList.add("show"); $("resetCancel").focus();
  });
  $("resetCancel").addEventListener("click", () => dlg.classList.remove("show"));
  $("resetConfirm").addEventListener("click", async () => {
    if (busy) return; busy = true; $("resetConfirm").disabled = true;
    const gn = Number(sel.value);
    try {
      const res = await fetch("/api/admin/reset", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ group_number: gn, confirm_group: gn }) });
      const ct = res.headers.get("content-type") || "";
      const d = ct.includes("json") ? await res.json() : null;
      dlg.classList.remove("show");
      if (d && d.success) { info[gn] = d.overview; showOverview(); notice(true, `Reset berhasil: ${d.answers_deleted} jawaban dan ${d.mission_progress_deleted} progres misi Kelompok ${gn} dihapus di Website 1.`); }
      else notice(false, "Reset GAGAL — tidak ada klaim berhasil. " + (d && d.reason === "not_logged_in" ? "Sesi admin berakhir; masuk ulang." : `Kode: ${(d && d.reason) || res.status}. Data mungkin tidak berubah; periksa lalu coba lagi.`));
    } catch (e) { dlg.classList.remove("show"); notice(false, "Reset GAGAL — server tidak dapat dihubungi. Tidak ada perubahan yang dikonfirmasi."); }
    finally { busy = false; $("resetConfirm").disabled = false; }
  });
});
