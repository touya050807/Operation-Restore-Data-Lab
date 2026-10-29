/* ============================================================================
   station.js — Station Panitia (Mission 1 & 3): pergantian kelompok CEPAT
   tanpa reload halaman/logout. Dropdown kelompok -> fetch state kelompok
   tersebut -> render ulang daftar soal secara in-place.
   ============================================================================ */

let STATION_CURRENT_GROUP_ID = null;
let STATION_LOAD_SEQ = 0;     // permintaan state terbaru; respons lama (kelompok sebelumnya) diabaikan

document.addEventListener("DOMContentLoaded", () => {
  initParticles();

  const switcher = document.getElementById("groupSwitcher");
  switcher.addEventListener("change", () => loadGroupState(switcher.value));

  // muat kelompok pertama di dropdown saat halaman dibuka
  loadGroupState(switcher.value);

  AnswerFlow.init({
    url: () => `/api/station/${STATION_KEY}/submit`,
    extra: () => ({ group_id: STATION_CURRENT_GROUP_ID }),
    token: () => STATION_CURRENT_GROUP_ID,          // respons untuk kelompok lain diabaikan
    onData: (data) => updateStationProgress(data.correct_points, data.requirement_points),
    onCompleted: async (data) => {
      await showResultOverlay({ type: "success", title: "ACCESS GRANTED", subtitle: "Selamat! Server berhasil dipulihkan.", subnote: `Mission Code: ${data.mission_code}` });
      loadGroupState(STATION_CURRENT_GROUP_ID);
    },
  });
});

async function loadGroupState(groupId) {
  STATION_CURRENT_GROUP_ID = groupId;
  const seq = ++STATION_LOAD_SEQ;
  // KOSONGKAN tampilan segera: kartu & jawaban kelompok sebelumnya tidak boleh tersisa (dan tidak boleh terkirim untuk kelompok baru)
  document.getElementById("questionList").innerHTML = '<p class="text-muted" id="stationLoading" role="status">Memuat data kelompok…</p>';
  const sb = document.getElementById("submitBtn"); if (sb) sb.disabled = true;
  const row = document.getElementById("submitRow"); if (row) row.style.display = "none";
  const mcb = document.getElementById("missionCodeBox"); if (mcb) mcb.style.display = "none";
  const m0 = document.getElementById("submitMessage"); if (m0) m0.style.display = "none";

  try {
    const res = await fetch(`/api/station/${STATION_KEY}/state?group_id=${encodeURIComponent(groupId)}`, { cache: "no-store" });
    const data = await res.json();
    if (seq !== STATION_LOAD_SEQ) return;                         // sudah pindah lagi: abaikan respons lama
    if (!data.success) {
      document.getElementById("questionList").innerHTML = "";
      const m = document.getElementById("submitMessage");
      if (m) { m.className = "submit-message sm-error"; m.style.display = "block"; m.textContent = data.reason === "locked" ? "Station terkunci. Buka dengan password station." : "Data kelompok tidak dapat dimuat (" + (data.reason || "error") + "). Pilih ulang kelompok."; }
      return;
    }
    if (String(data.group.id) !== String(groupId)) return;       // pengaman tambahan: respons harus untuk kelompok yang dipilih
    const grpLabel = document.getElementById("currentGroupLabel");
    if (grpLabel) grpLabel.textContent = `GROUP ${String(data.group.group_number).padStart(2, "0")}`;
    renderStationQuestions(data.questions);
    applySavedAnswers(data.questions);                            // pulihkan jawaban tersimpan KELOMPOK INI
    updateStationProgress(data.progress.correct_points, data.requirement_points);
    updateMissionCodeBox(data.group, data.mission_code);

    AnswerFlow.refreshSubmitRow();
    document.getElementById("submitBtn").disabled = false;
  } catch (err) {
    if (seq !== STATION_LOAD_SEQ) return;
    document.getElementById("questionList").innerHTML = "";
    await showResultOverlay({ type: "error", title: "Gagal memuat data kelompok.", subtitle: "Coba pilih ulang." });
  }
}

function renderStationQuestions(questions) {
  const container = document.getElementById("questionList");
  container.innerHTML = questions.map((q, i) => renderQuestionCard(q, i)).join("");
  container.querySelectorAll(".repair-panel[data-qid]").forEach((card) => initQuestionCardWidgets(card));
}

function refreshSubmitRow() {
  const row = document.getElementById("submitRow");
  const cards = document.querySelectorAll("#questionList .repair-panel[data-qid]:not(.correct)");
  row.style.display = cards.length ? "flex" : "none";
}

function updateStationProgress(correctPoints, requirementPoints) {
  document.getElementById("progressLabel").textContent = `${correctPoints} / ${requirementPoints} poin`;
  const pct = requirementPoints ? Math.floor((correctPoints / requirementPoints) * 100) : 100;
  document.getElementById("progressFill").style.width = pct + "%";
}

function updateMissionCodeBox(group, missionCode) {
  const box = document.getElementById("missionCodeBox");
  if (missionCode) {
    box.style.display = "flex";
    document.getElementById("missionCodeGroupLabel").textContent = `Kelompok ${group.group_number} — SELESAI`;
    document.getElementById("missionCodeValue").textContent = missionCode;
  } else {
    box.style.display = "none";
  }
}
