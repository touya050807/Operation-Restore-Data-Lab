/* ============================================================================
   admin_questions.js — form dinamis Bank Soal untuk 8 tipe jawaban:
   text, number, essay, true_false, multiple_choice, multiple_select,
   ordering, matching. Menampilkan field sesuai tipe + populate form saat
   tombol Edit ditekan.
   ============================================================================ */

const TYPE_FIELDS = {
  text: ["matchModeField", "answerFieldText"],
  number: ["answerFieldText"],
  essay: [],
  true_false: ["answerFieldTF"],
  multiple_choice: ["optionsField", "answerFieldText"],
  multiple_select: ["optionsField", "multiCorrectField"],
  ordering: ["orderingItemsField", "orderingCorrectField"],
  matching: ["matchingField"],
};

const ALL_TOGGLE_FIELDS = [
  "matchModeField", "optionsField", "multiCorrectField", "orderingItemsField",
  "orderingCorrectField", "matchingField", "answerFieldText", "answerFieldTF",
];

document.addEventListener("DOMContentLoaded", () => {
  initParticles();

  const typeSelect = document.getElementById("f_type");
  const answerTFSelect = document.getElementById("f_answer_tf");
  const answerTextInput = document.getElementById("f_answer");
  const form = document.getElementById("questionForm");

  function syncFieldsForType() {
    const type = typeSelect.value;
    const toShow = new Set(TYPE_FIELDS[type] || []);
    ALL_TOGGLE_FIELDS.forEach((id) => {
      document.getElementById(id).style.display = toShow.has(id) ? "block" : "none";
    });
    answerTextInput.placeholder = type === "multiple_choice"
      ? "Ketik persis salah satu opsi di atas" : "Jawaban benar persis";
  }
  typeSelect.addEventListener("change", syncFieldsForType);
  syncFieldsForType();

  form.addEventListener("submit", () => {
    if (typeSelect.value === "true_false") {
      answerTextInput.value = answerTFSelect.value;
    }
  });

  // ---------------------------------------------------------------------
  // EDIT: klik tombol Edit -> isi form dari data-question (JSON per baris)
  // ---------------------------------------------------------------------
  document.querySelectorAll(".edit-question-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const q = JSON.parse(btn.dataset.question);

      document.getElementById("formTitle").textContent = `✏ Edit Soal #${q.id}`;
      document.getElementById("f_id").value = q.id;
      document.getElementById("f_mission").value = q.mission_id;
      document.getElementById("f_category").value = q.category;
      document.getElementById("f_prompt").value = q.prompt;
      typeSelect.value = q.answer_type;
      document.getElementById("f_points").value = q.points;
      document.getElementById("f_match").value = q.match_mode || "case_insensitive";
      document.getElementById("f_active").checked = !!q.is_active;

      // reset semua field tipe-spesifik dulu
      document.getElementById("f_options").value = "";
      document.getElementById("f_multi_correct").value = "";
      document.getElementById("f_ordering_items").value = "";
      document.getElementById("f_ordering_correct").value = "";
      document.getElementById("f_matching_pairs").value = "";
      answerTextInput.value = "";

      if (q.answer_type === "multiple_choice") {
        document.getElementById("f_options").value = (q.options || []).join("\n");
        answerTextInput.value = q.correct_answer;
      } else if (q.answer_type === "multiple_select") {
        document.getElementById("f_options").value = (q.options || []).join("\n");
        try { document.getElementById("f_multi_correct").value = JSON.parse(q.correct_answer).join("\n"); } catch (e) {}
      } else if (q.answer_type === "ordering") {
        document.getElementById("f_ordering_items").value = (q.options || []).join("\n");
        try { document.getElementById("f_ordering_correct").value = JSON.parse(q.correct_answer).join("\n"); } catch (e) {}
      } else if (q.answer_type === "matching") {
        try {
          const pairs = JSON.parse(q.correct_answer);
          document.getElementById("f_matching_pairs").value = Object.entries(pairs).map(([l, r]) => `${l} => ${r}`).join("\n");
        } catch (e) {}
      } else if (q.answer_type === "true_false") {
        answerTFSelect.value = q.correct_answer;
      } else {
        answerTextInput.value = q.correct_answer;
      }

      syncFieldsForType();
      document.getElementById("cancelEditBtn").style.display = "inline-flex";
      document.getElementById("questionFormCard").scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  document.getElementById("cancelEditBtn").addEventListener("click", () => {
    document.getElementById("formTitle").textContent = "+ Tambah Soal Baru";
    form.reset();
    document.getElementById("f_id").value = "";
    document.getElementById("cancelEditBtn").style.display = "none";
    syncFieldsForType();
  });
});
