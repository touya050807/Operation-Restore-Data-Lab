/* ============================================================================
   answer_flow.js — alur kirim & validasi jawaban BERSAMA (Mission 2, 4 dan Station Mission 1, 3).
   Prinsip:
   - Setiap soal punya ID unik (data-qid dari database), state & feedback sendiri, dan tombol "Periksa Jawaban" sendiri.
   - Tombol global hanya mengirim soal yang terisi; soal kosong diberi status "belum diisi" (bukan salah, tidak dinilai).
   - Lima keadaan berbeda: loading, benar, belum tepat (salah), belum lengkap, gagal diperiksa (error teknis).
   - Jawaban peserta TIDAK PERNAH dihapus oleh respons salah/error.
   - Jeda 30 dtk setelah jawaban salah (Mission 2 & 4 saja) DITENTUKAN SERVER; di sini hanya ditampilkan (hitung mundur dari
     sisa detik yang dikirim server). Menyembunyikan/menonaktifkan tombol bukan pengaman: server menolak (429) selama jeda.
   - Skor resmi ditentukan backend; klien hanya menampilkan respons.
   ============================================================================ */
var AnswerFlow = (function () {
  const REASON = {
    not_identified: "Sesi kelompok tidak ditemukan. Masuk ulang ke kelompokmu lalu kirim lagi (jawabanmu masih ada di kotak).",
    not_logged_in: "Sesi panitia berakhir. Masuk ulang sebagai panitia lalu kirim lagi.",
    role_not_selected: "Peran panitia belum dipilih. Pilih peran lalu kirim lagi.",
    forbidden: "Akun ini tidak berhak mengirim jawaban di halaman ini.",
    locked: "Station terkunci. Buka kembali dengan password station lalu kirim lagi.",
    invalid_group: "Kelompok tidak valid. Pilih ulang kelompok.",
    inactive: "Misi ini sedang tidak aktif.",
    no_answers: "Belum ada jawaban yang terisi.",
    bad_request: "Format jawaban tidak dikenali server.",
  };
  let cfg = null;
  let cdEnd = 0, cdTimer = null;                               // jeda: waktu akhir (performance.now) dan interval tampilan
  const cooldownLeft = () => Math.max(0, Math.ceil((cdEnd - performance.now()) / 1000));

  const $ = (s, r) => (r || document).querySelector(s);
  const cards = () => [...document.querySelectorAll("#questionList .repair-panel[data-qid]")];
  const cardOf = (qid) => document.querySelector(`#questionList .repair-panel[data-qid="${CSS.escape(String(qid))}"]`);

  function banner(kind, text) {
    let el = $("#submitMessage");
    if (!el) return;
    el.className = "submit-message " + (kind ? "sm-" + kind : "");
    el.textContent = text || "";
    el.style.display = text ? "block" : "none";
  }

  function setFeedback(card, kind, text) {
    const fb = $(".q-feedback", card);
    if (!fb) return;
    fb.className = "q-feedback fb-" + kind;
    fb.setAttribute("role", "status");
    fb.textContent = text;
    fb.style.display = "block";
    card.dataset.state = kind;
  }
  function clearFeedback(card) {
    const fb = $(".q-feedback", card);
    if (fb) { fb.style.display = "none"; fb.textContent = ""; fb.className = "q-feedback"; }
    delete card.dataset.state;
  }

  function setBusy(card, on) {
    card.dataset.busy = on ? "1" : "0";
    card.classList.toggle("is-loading", on);
    const b = $(".q-submit", card);
    if (b) { b.disabled = on || cooldownLeft() > 0; b.textContent = on ? "Memeriksa…" : (card.dataset.state === "error" ? "Kirim ulang" : "Periksa Jawaban"); }
  }

  function applyCooldownUI() {
    const left = cooldownLeft(), box = $("#cooldownBox");
    document.querySelectorAll("#questionList .q-submit").forEach((b) => { if (left > 0) b.disabled = true; else if (b.closest(".repair-panel").dataset.busy !== "1") b.disabled = false; });
    const g = $("#submitBtn"); if (g) { if (left > 0) g.disabled = true; else if (!cards().some((c) => c.dataset.busy === "1")) g.disabled = false; }
    if (box) {
      if (left > 0) { box.style.display = "block"; box.className = "submit-message sm-wrong"; box.textContent = `Jeda setelah jawaban salah: tunggu ${left} detik sebelum menjawab lagi. Jawabanmu di kotak tidak hilang.`; }
      else { box.style.display = "none"; box.textContent = ""; }
    }
  }
  function startCooldown(seconds) {
    seconds = Number(seconds);
    if (!(seconds > 0)) return;
    cdEnd = performance.now() + seconds * 1000;
    clearInterval(cdTimer);
    cdTimer = setInterval(() => { applyCooldownUI(); if (cooldownLeft() <= 0) { clearInterval(cdTimer); cdTimer = null; } }, 250);
    applyCooldownUI();
  }

  function markCorrect(card, text) {
    card.classList.add("correct");
    const area = $(".q-input-area", card), act = $(".q-actions", card);
    if (area) area.style.display = "none";
    if (act) act.style.display = "none";
    setFeedback(card, "ok", text);
  }

  function refreshSubmitRow() {
    const row = $("#submitRow");
    if (row) row.style.display = cards().some((c) => !c.classList.contains("correct")) ? "flex" : "none";
  }

  function applyDetails(data, sentIds) {
    const d = data.details || {};
    sentIds.forEach((qid) => {
      const card = cardOf(qid);
      if (!card) return;
      const r = d[qid];
      if (!r) {                                    // server tidak menjawab soal ini -> bukan "salah"
        setFeedback(card, "error", "Server tidak mengembalikan hasil untuk soal ini. Kirim ulang.");
      } else if (r.status === "correct") {
        markCorrect(card, "✓ Jawaban benar." + (r.points_awarded ? ` +${r.points_awarded} poin` : ""));
      } else if (r.status === "already_correct") {
        markCorrect(card, "✓ Sudah benar sebelumnya (poin tidak bertambah lagi).");
      } else if (r.status === "wrong") {
        setFeedback(card, "wrong", "✗ Jawaban belum tepat. Perbaiki jawabanmu lalu tekan Periksa Jawaban lagi.");
      } else if (r.status === "incomplete") {
        setFeedback(card, "incomplete", "Jawaban belum lengkap — belum diperiksa.");
      } else {
        setFeedback(card, "error", "Soal tidak dikenali server. Muat ulang halaman.");
      }
    });
  }

  async function submit(targets, isGlobal) {
    if (cooldownLeft() > 0) { applyCooldownUI(); return; }        // server tetap menolak bila diakali; ini hanya menghemat request
    targets = targets.filter((c) => c.dataset.busy !== "1" && !c.classList.contains("correct"));
    if (!targets.length) { banner("info", "Semua soal sudah benar atau sedang diperiksa."); return; }
    banner("", "");
    const answers = {}, blanks = [];
    targets.forEach((card) => {
      let v = collectAnswerFromCard(card);
      // pengiriman massal: urutan yang belum pernah diubah peserta dianggap belum dikerjakan (bukan jawaban salah)
      const ol = $("[data-order-list]", card);
      if (isGlobal && ol && !ol.dataset.touched) v = null;
      if (v === null) blanks.push(card); else answers[card.dataset.qid] = v;
    });
    blanks.forEach((c) => setFeedback(c, "incomplete", "Belum diisi/diubah — soal ini belum diperiksa."));
    const ids = Object.keys(answers);
    if (!ids.length) {
      banner("info", isGlobal ? "Belum ada jawaban yang terisi. Isi minimal satu soal lalu kirim." : "Isi jawabanmu dulu sebelum memeriksa.");
      return;
    }
    const token = cfg.token ? cfg.token() : null;
    const sent = ids.map((id) => cardOf(id)).filter(Boolean);
    sent.forEach((c) => { setBusy(c, true); setFeedback(c, "loading", "Memeriksa jawaban…"); });
    const bBtn = $("#submitBtn"); if (bBtn) bBtn.disabled = true;
    try {
      const res = await fetch(cfg.url(), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.assign({}, cfg.extra ? cfg.extra() : {}, { answers })),
      });
      const ct = res.headers.get("content-type") || "";
      const data = ct.includes("json") ? await res.json() : null;
      if (cfg.token && cfg.token() !== token) return;           // panitia sudah pindah kelompok: abaikan respons lama
      if (data && data.reason === "cooldown") {                  // BUKAN jawaban salah dan BUKAN error: server meminta menunggu
        sent.forEach((c) => { c.dataset.state = ""; setFeedback(c, "incomplete", "Belum diperiksa: masih dalam jeda. Jawabanmu tetap ada."); });
        startCooldown(data.remaining_seconds);
        return;
      }
      if (!data || !data.success) {
        const msg = (data && REASON[data.reason]) || `Server tidak dapat memeriksa jawaban (kode ${res.status}). Jawabanmu masih ada di kotak; tekan Kirim ulang.`;
        sent.forEach((c) => { c.dataset.state = "error"; setFeedback(c, "error", "⚠ Jawaban BELUM berhasil diperiksa. " + msg); });
        banner("error", "Pengiriman gagal — ini bukan jawaban salah. " + msg);
        return;
      }
      applyDetails(data, ids);
      if (cfg.onData) cfg.onData(data);
      const nWrong = ids.filter((i) => (data.details[i] || {}).status === "wrong").length;
      const nOk = ids.filter((i) => ["correct", "already_correct"].includes((data.details[i] || {}).status)).length;
      banner(nWrong ? "wrong" : "ok", `${nOk} soal benar, ${nWrong} soal belum tepat${blanks.length ? `, ${blanks.length} belum diisi` : ""}.`);
      if (data.cooldown && data.cooldown.enabled && data.cooldown.seconds_left > 0) startCooldown(data.cooldown.seconds_left);
      if (cfg.after) cfg.after(ids);
      if (data.status === "completed" && cfg.onCompleted) await cfg.onCompleted(data);
    } catch (err) {
      if (cfg.token && cfg.token() !== token) return;
      const msg = "Tidak dapat menghubungi server. Jawabanmu masih ada di kotak; periksa koneksi lalu tekan Kirim ulang.";
      sent.forEach((c) => { c.dataset.state = "error"; setFeedback(c, "error", "⚠ Jawaban BELUM berhasil diperiksa. " + msg); });
      banner("error", "Pengiriman gagal — ini bukan jawaban salah. " + msg);
    } finally {
      sent.forEach((c) => setBusy(c, false));                  // loading SELALU berhenti
      if (bBtn) bBtn.disabled = cooldownLeft() > 0;
      refreshSubmitRow();
    }
  }

  function init(config) {
    cfg = config;
    const list = $("#questionList");
    if (cfg.cooldownInit > 0) startCooldown(cfg.cooldownInit);
    list.addEventListener("click", (e) => {
      const b = e.target.closest(".q-submit");
      if (b) submit([b.closest(".repair-panel")], false);
    });
    list.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && e.target.matches("input.q-input")) { e.preventDefault(); submit([e.target.closest(".repair-panel")], false); }
    });
    const edited = (e) => {                                    // mengubah jawaban menghapus status lama (jawaban tetap)
      const card = e.target.closest && e.target.closest(".repair-panel");
      if (card && ["wrong", "error", "incomplete"].includes(card.dataset.state)) { clearFeedback(card); setBusy(card, false); }
    };
    ["input", "change", "click"].forEach((ev) => list.addEventListener(ev, (e) => { if (!e.target.closest(".q-submit")) edited(e); }));
    const g = $("#submitBtn");
    if (g) g.addEventListener("click", () => submit(cards(), true));
  }

  return { init, refreshSubmitRow, cards };
})();
