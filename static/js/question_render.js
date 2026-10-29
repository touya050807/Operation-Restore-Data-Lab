/* ============================================================================
   question_render.js
   Mesin render + pengumpulan jawaban BERSAMA untuk seluruh 8 tipe soal:
   text, number, essay, true_false, multiple_choice, multiple_select,
   ordering, matching. Dipakai oleh mission_participant.js (mission
   self-serve 2 & 5) DAN station.js (mission meja panitia 1 & 3) supaya
   render & pengumpulan jawaban konsisten di satu tempat.
   ============================================================================ */

function escapeHtmlQ(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  // innerHTML TIDAK meng-escape tanda kutip; tanpa ini opsi seperti print("Halo") memotong atribut value="..." (akar masalah MC dinilai salah)
  return div.innerHTML.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

/**
 * renderQuestionCard(question, index) -> HTML string satu kartu soal.
 * question: { id, prompt, category, points, answer_type, options, is_correct }
 */
function renderQuestionCard(question, index) {
  const isCorrect = !!question.is_correct;
  const qid = question.id;
  // Soal bisa memuat blok kode berpagar (```python ... ```). Teks di luar blok = narasi; isi blok disajikan UTUH (indentasi
  // dipertahankan, tanpa nomor baris) dengan tombol "Salin kode" supaya bisa langsung ditempel ke Google Colab.
  // Judul = baris pertama narasi (bukan potongan kode), badan = sisa narasi + blok kode.
  const segs = parsePromptSegments(question.prompt || "");
  const firstText = segs.findIndex((x) => x.type === "text" && x.text.trim() !== "");
  let shortTitle = "Soal";
  if (firstText >= 0) {
    const lines = segs[firstText].text.replace(/^\n+/, "").split("\n");
    shortTitle = lines[0];
    segs[firstText] = { type: "text", text: lines.slice(1).join("\n") };
  }
  const bodyHtml = segs.map((x) => {
    if (x.type === "code") {
      return `<div class="code-wrap"><button type="button" class="code-copy btn btn-ghost btn-sm" aria-label="Salin kode ke papan klip">Salin kode</button>` +
             `<pre class="code-block" tabindex="0"><code>${escapeHtmlQ(x.text)}</code></pre></div>`;
    }
    const t = x.text.replace(/^\n+|\s+$/g, "");
    return t ? `<pre style="white-space:pre-wrap;">${escapeHtmlQ(t)}</pre>` : "";
  }).join("");

  let inputHtml;
  if (isCorrect) {
    const saved = describeSavedAnswer(question.saved_answer);
    inputHtml = `<div class="alert alert-success show" style="margin-top:10px;">✓ Sudah dijawab dengan benar.` +
                (saved ? `<br><span class="mono" style="font-size:.82rem;white-space:pre-wrap;">Jawaban tersimpan: ${escapeHtmlQ(saved)}</span>` : "") + `</div>`;
  } else {
    inputHtml = renderInputForType(question);
  }

  return `
    <div class="repair-panel glass hud-corners rise-in ${isCorrect ? "correct" : ""}"
         data-qid="${qid}" data-qtype="${question.answer_type}">
      <div class="r-head">
        <span class="r-num">${index + 1}</span>
        <span class="r-title">${escapeHtmlQ(shortTitle)}</span>
        <span class="mono text-muted r-meta">${escapeHtmlQ(question.category)} · ${question.points} poin</span>
      </div>
      ${bodyHtml}
      ${isCorrect ? inputHtml : `<div class="q-input-area">${inputHtml}</div>
      <div class="q-actions"><button type="button" class="btn btn-purple btn-sm q-submit">Periksa Jawaban</button></div>`}
      ${!isCorrect ? '<div class="q-feedback" style="display:none;" aria-live="polite"></div>' : ""}
    </div>`;
}

/** Pecah prompt menjadi segmen {type:"text"|"code", text}. Pagar kode: baris ```[bahasa] ... baris ```. Tanpa pagar -> satu segmen teks. */
function parsePromptSegments(prompt) {
  const out = [], lines = String(prompt).split("\n");
  let buf = [], inCode = false;
  const flush = (type) => { if (buf.length || type === "code") out.push({ type, text: buf.join("\n") }); buf = []; };
  for (const ln of lines) {
    if (!inCode && /^```[A-Za-z0-9_+-]*\s*$/.test(ln)) { flush("text"); inCode = true; continue; }
    if (inCode && /^```\s*$/.test(ln)) { flush("code"); inCode = false; continue; }
    buf.push(ln);
  }
  if (inCode) { buf.unshift("```"); inCode = false; }          // pagar tak ditutup: tampilkan apa adanya sebagai teks
  flush("text");
  return out;
}

/** Tombol "Salin kode": menyalin teks blok kode persis (tanpa HTML), dengan cadangan execCommand. */
document.addEventListener("click", async (e) => {
  const b = e.target.closest && e.target.closest(".code-copy");
  if (!b) return;
  const code = b.parentElement.querySelector("pre code").textContent;
  let okc = false;
  try { await navigator.clipboard.writeText(code); okc = true; } catch (err) {
    const ta = document.createElement("textarea"); ta.value = code; ta.style.position = "fixed"; ta.style.opacity = "0"; document.body.appendChild(ta); ta.select();
    try { okc = document.execCommand("copy"); } catch (e2) { okc = false; } ta.remove();
  }
  const old = b.dataset.label || (b.dataset.label = b.textContent);
  b.textContent = okc ? "Tersalin ✓" : "Gagal menyalin — blok teks manual"; setTimeout(() => (b.textContent = old), 1800);
});

function renderInputForType(question) {
  const qid = question.id;
  const type = question.answer_type;

  if (type === "text") {
    return `<div class="field" style="margin-bottom:0;"><input type="text" class="q-input" placeholder="Jawaban..."></div>`;
  }
  if (type === "number") {
    return `<div class="field" style="margin-bottom:0;"><input type="number" class="q-input" placeholder="Jawaban (angka)..."></div>`;
  }
  if (type === "essay") {
    return `<div class="field" style="margin-bottom:0;"><textarea class="q-input" rows="4" placeholder="Tulis jawaban/penjelasan kalian..."></textarea></div>`;
  }
  if (type === "true_false") {
    return `<div class="mcq-options">
      <label class="mcq-option"><input type="radio" name="q_${qid}" value="true" class="q-input-radio" style="margin-right:8px;">Benar</label>
      <label class="mcq-option"><input type="radio" name="q_${qid}" value="false" class="q-input-radio" style="margin-right:8px;">Salah</label>
    </div>`;
  }
  if (type === "multiple_choice") {
    const options = question.options || [];
    return `<div class="mcq-options">` + options.map((opt) =>
      `<label class="mcq-option"><input type="radio" name="q_${qid}" value="${escapeHtmlQ(opt)}" class="q-input-radio" style="margin-right:8px;">${escapeHtmlQ(opt)}</label>`
    ).join("") + `</div>`;
  }
  if (type === "multiple_select") {
    const options = question.options || [];
    return `<div class="mcq-options">` + options.map((opt, i) =>
      `<label class="mcq-option checkbox-style"><input type="checkbox" value="${escapeHtmlQ(opt)}" class="q-input-checkbox" data-qid="${qid}">${escapeHtmlQ(opt)}</label>`
    ).join("") + `</div>`;
  }
  if (type === "ordering") {
    const options = question.options || [];   // sudah diacak di server (tidak sama dgn kunci)
    const listId = `orderList_${qid}`;
    return `<p style="font-size:.82rem; margin-bottom:10px;">Geser (drag) kartu, atau gunakan tombol ▲▼.</p>
      <ul class="order-list" id="${listId}" data-order-list="1">
        ${options.map((opt) => `
        <li class="order-item" data-value="${escapeHtmlQ(opt)}">
          <span class="drag-handle">⠿</span><span class="order-text">${escapeHtmlQ(opt)}</span>
          <span class="order-ctrl">
            <button type="button" class="btn btn-ghost btn-sm move-up">▲</button>
            <button type="button" class="btn btn-ghost btn-sm move-down">▼</button>
          </span>
        </li>`).join("")}
      </ul>`;
  }
  if (type === "matching") {
    const opts = question.options || { left: [], right: [] };
    const rightShuffled = shuffleArray(opts.right || []);
    return opts.left.map((leftItem, i) => `
      <div class="match-row" data-left="${escapeHtmlQ(leftItem)}">
        <div class="match-left">${escapeHtmlQ(leftItem)}</div>
        <select class="q-match-select">
          <option value="">— pilih pasangan —</option>
          ${rightShuffled.map((r) => `<option value="${escapeHtmlQ(r)}">${escapeHtmlQ(r)}</option>`).join("")}
        </select>
      </div>`).join("");
  }
  return `<div class="field" style="margin-bottom:0;"><input type="text" class="q-input" placeholder="Jawaban..."></div>`;
}

/** Dipanggil setelah kartu di-insert ke DOM: hidupkan widget interaktif (ordering, dsb). */
function initQuestionCardWidgets(card) {
  const orderList = card.querySelector("[data-order-list]");
  if (orderList) initOrderList(orderList.id);

  card.querySelectorAll(".mcq-option input[type=radio], .mcq-option input[type=checkbox]").forEach((inp) => {
    inp.addEventListener("change", () => {
      inp.closest(".mcq-option").classList.toggle("selected", inp.checked);
    });
  });
}

/** Ambil jawaban dari satu kartu sesuai tipe -> null jika belum diisi. */
function collectAnswerFromCard(card) {
  const type = card.dataset.qtype;
  const qid = card.dataset.qid;

  if (type === "true_false" || type === "multiple_choice") {
    const checked = card.querySelector(`input[name="q_${qid}"]:checked`);
    return checked ? checked.value : null;
  }
  if (type === "multiple_select") {
    const checked = [...card.querySelectorAll(".q-input-checkbox:checked")].map((c) => c.value);
    return checked.length ? checked : null;
  }
  if (type === "ordering") {
    const list = card.querySelector("[data-order-list]");
    return list ? getOrderValues(list.id) : null;
  }
  if (type === "matching") {
    const rows = card.querySelectorAll(".match-row");
    const result = {};
    let allFilled = true;
    rows.forEach((row) => {
      const left = row.dataset.left;
      const value = row.querySelector(".q-match-select").value;
      if (!value) allFilled = false;
      result[left] = value;
    });
    return allFilled && rows.length ? result : null;
  }
  // text / number / essay
  const input = card.querySelector(".q-input");
  return input && input.value.trim() !== "" ? input.value : null;
}


/** Isi satu kartu dengan jawaban v sesuai tipe soalnya (dipakai untuk draft lokal DAN jawaban tersimpan di server). */
function fillCardAnswer(card, v) {
  const type = card.dataset.qtype, qid = card.dataset.qid;
  if (type === "true_false" || type === "multiple_choice") {
    card.querySelectorAll(`input[name="q_${qid}"]`).forEach((i) => { i.checked = i.value === v; i.closest(".mcq-option")?.classList.toggle("selected", i.checked); });
  } else if (type === "multiple_select" && Array.isArray(v)) {
    card.querySelectorAll(".q-input-checkbox").forEach((i) => { i.checked = v.includes(i.value); i.closest(".mcq-option")?.classList.toggle("selected", i.checked); });
  } else if (type === "ordering" && Array.isArray(v)) {
    const list = card.querySelector("[data-order-list]");
    if (list) {
      const items = [...list.querySelectorAll(".order-item")];
      if (items.length === v.length && v.every((x) => items.some((it) => it.dataset.value === x)))
        { v.forEach((x) => list.appendChild(items.find((it) => it.dataset.value === x))); list.dataset.touched = "1"; }
    }
  } else if (type === "matching" && v && typeof v === "object") {
    card.querySelectorAll(".match-row").forEach((row) => { const sel = row.querySelector(".q-match-select"); if (sel && v[row.dataset.left] !== undefined) sel.value = v[row.dataset.left]; });
  } else {
    const inp = card.querySelector(".q-input"); if (inp && typeof v === "string") inp.value = v;
  }
}

/** Tampilan teks jawaban tersimpan (untuk kartu yang sudah benar). */
function describeSavedAnswer(v) {
  if (v === null || v === undefined) return "";
  if (Array.isArray(v)) return v.join(" → ");
  if (typeof v === "object") return Object.entries(v).map(([k, x]) => `${k} = ${x}`).join("; ");
  return String(v);
}

/** Pulihkan jawaban TERAKHIR yang tersimpan di server untuk kelompok yang sedang tampil (soal yang belum benar). */
function applySavedAnswers(questions) {
  (questions || []).forEach((q) => {
    if (q.is_correct || q.saved_answer === null || q.saved_answer === undefined) return;
    const card = document.querySelector(`#questionList .repair-panel[data-qid="${CSS.escape(String(q.id))}"]`);
    if (!card) return;
    fillCardAnswer(card, q.saved_answer);
    const area = card.querySelector(".q-input-area");
    if (area && !card.querySelector(".q-saved-note")) {
      const n = document.createElement("div"); n.className = "q-saved-note text-muted"; n.style.cssText = "font-size:.8rem;margin-top:6px;";
      n.textContent = "Jawaban terakhir kelompok ini yang tersimpan (belum tepat) — ubah lalu periksa lagi."; area.appendChild(n);
    }
  });
}

/* ---- Draft jawaban (localStorage, berversi). Hanya jawaban pilihan peserta; tidak ada kunci/kode/sandi. ---- */
var AnswerDraft = {
  key(scope) { return `axis2026_answer_draft_v1:${scope}`; },
  read(scope) { try { return JSON.parse(localStorage.getItem(this.key(scope)) || "null") || {}; } catch (e) { return {}; } },
  write(scope, data) { try { localStorage.setItem(this.key(scope), JSON.stringify(data)); } catch (e) { /* storage tidak tersedia */ } },
  clear(scope) { try { localStorage.removeItem(this.key(scope)); } catch (e) { /* abaikan */ } },
  // hapus draft kelompok+misi yang sama dengan epoch reset lain (sisa sebelum reset)
  purgeOld(scope) {
    try {
      const base = scope.split(".e")[0] + ".e", tail = ":" + scope.split(":").slice(-1)[0], keep = this.key(scope);
      Object.keys(localStorage).filter((k) => k.startsWith("axis2026_answer_draft_v1:" + base) && k.endsWith(tail) && k !== keep).forEach((k) => localStorage.removeItem(k));
    } catch (e) { /* abaikan */ }
  },
  // simpan semua kartu yang belum benar (debounce dilakukan pemanggil)
  capture(scope) {
    const out = {};
    document.querySelectorAll("#questionList .repair-panel[data-qid]:not(.correct)").forEach((card) => {
      const v = collectAnswerFromCard(card);
      if (v !== null) out[card.dataset.qid] = v;
    });
    this.write(scope, out);
  },
  restore(scope) {
    const d = this.read(scope);
    document.querySelectorAll("#questionList .repair-panel[data-qid]:not(.correct)").forEach((card) => {
      const v = d[card.dataset.qid]; if (v === undefined) return;
      fillCardAnswer(card, v);
    });
  },
};
