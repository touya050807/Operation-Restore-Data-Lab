/* ============================================================================
   mission_participant.js — halaman mission self-serve (Mission 2 & 4),
   memakai mesin render bersama (question_render.js) untuk seluruh tipe soal.
   ============================================================================ */

document.addEventListener("DOMContentLoaded", () => {
  initParticles();

  const questions = JSON.parse(document.getElementById("questionsData").textContent);
  renderQuestions(questions);
  const scope = `g${typeof GROUP_NUMBER !== "undefined" ? GROUP_NUMBER : 0}.e${typeof RESET_EPOCH !== "undefined" ? RESET_EPOCH : 0}:${MISSION_KEY}`;
  applySavedAnswers(questions);     // jawaban terakhir kelompok ini dari server (berlaku lintas perangkat)
  AnswerDraft.purgeOld(scope);      // draft dari sebelum reset pengerjaan tidak dipulihkan
  AnswerDraft.restore(scope);
  let t = null;   // debounce 1,5 detik; tanpa polling
  const save = () => { clearTimeout(t); t = setTimeout(() => AnswerDraft.capture(scope), 1500); };
  const ql = document.getElementById("questionList");
  ["input", "change", "click"].forEach((ev) => ql.addEventListener(ev, save));
  window.__draftScope = scope;

  if (!document.getElementById("submitBtn")) return;
  document.getElementById("submitRow").style.display = questions.some((q) => !q.is_correct) ? "flex" : "none";
  AnswerFlow.init({
    url: () => `/api/mission/${MISSION_KEY}/submit`,
    cooldownInit: typeof COOLDOWN_INIT === "number" ? COOLDOWN_INIT : 0,
    onData: (data) => {
      document.getElementById("progressLabel").textContent = `${data.correct_points} / ${data.requirement_points} poin`;
      const pct = data.requirement_points ? Math.floor((data.correct_points / data.requirement_points) * 100) : 100;
      document.getElementById("progressFill").style.width = Math.min(100, pct) + "%";
    },
    after: () => AnswerDraft.capture(scope),
    onCompleted: async (data) => {
      AnswerDraft.clear(scope);
      await showResultOverlay({ type: "success", title: "ACCESS GRANTED", subtitle: "Selamat! Server berhasil dipulihkan.", subnote: `Mission Code: ${data.mission_code}` });
      window.location.reload();
    },
  });
});

function renderQuestions(questions) {
  const container = document.getElementById("questionList");
  container.innerHTML = questions.map((q, i) => renderQuestionCard(q, i)).join("");
  container.querySelectorAll(".repair-panel[data-qid]").forEach((card) => initQuestionCardWidgets(card));
}
