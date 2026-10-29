# ============================================================================
#  services/mission_service.py
#  Logika inti Mission System: progress per kelompok, pengecekan jawaban di
#  backend, requirement poin, dan pembuatan Mission Code. Jeda jawaban salah: hanya Mission 2 & 4 (cooldown_service).
# ============================================================================

import json
import random
from datetime import datetime

from db_layer.db import query_all, query_one, execute, get_connection
from services.answer_check import check_answer, is_blank
from services.activity_log import log_activity
from services.codes import get_code
from services import cooldown_service as cd

ISO = "%Y-%m-%d %H:%M:%S"


def now_str():
    return datetime.now().strftime(ISO)


def get_active_missions():
    return query_all("SELECT * FROM missions WHERE is_active = 1 ORDER BY sort_order")


def get_mission_by_key(key):
    return query_one("SELECT * FROM missions WHERE mission_key = ?", (key,))


def get_active_questions(mission_id):
    return query_all(
        "SELECT * FROM questions WHERE mission_id = ? AND is_active = 1 ORDER BY sort_order, id",
        (mission_id,),
    )


def shuffle_not_equal(items, correct, seed):
    """Acak deterministik (seed tetap -> reload tidak mengubah urutan awal) dan JAMIN
    urutan awal tidak sama dengan kunci jawaban."""
    rnd = random.Random(seed)
    out = list(items)
    for _ in range(20):
        rnd.shuffle(out)
        if out != list(correct) or len(out) < 2:
            return out
    return out[1:] + out[:1]


def saved_answers_map(group_id):
    """{question_id: (is_correct, jawaban_terakhir)} MILIK kelompok ini saja (kunci = group_id dari backend)."""
    out = {}
    for r in query_all("SELECT question_id, is_correct, last_answer FROM question_progress WHERE group_id = ?", (group_id,)):
        try:
            val = json.loads(r["last_answer"]) if r["last_answer"] is not None else None
        except (ValueError, TypeError):
            val = None
        out[r["question_id"]] = (bool(r["is_correct"]), val)
    return out


def serialize_question_for_frontend(question, is_correct=False, group_id=None, saved_answer=None):
    """Bentuk aman untuk dikirim ke browser — TIDAK PERNAH menyertakan
    correct_answer. options_json di-parse sesuai tipe soal. Soal ordering
    diacak DI SERVER (urutan awal selalu berbeda dari kunci)."""
    options = None
    if question["options_json"]:
        try:
            options = json.loads(question["options_json"])
        except (ValueError, TypeError):
            options = None
    if question["answer_type"] == "ordering" and isinstance(options, list):
        try:
            key = json.loads(question["correct_answer"] or "[]")
        except (ValueError, TypeError):
            key = []
        options = shuffle_not_equal(options, key, f"{group_id}-{question['id']}")

    return {
        "id": question["id"],
        "prompt": question["prompt"],
        "category": question["category"],
        "points": question["points"],
        "answer_type": question["answer_type"],
        "options": options,
        "is_correct": bool(is_correct),
        "saved_answer": saved_answer,          # jawaban terakhir kelompok ini (None bila belum pernah menjawab)
    }


def ensure_progress_row(group_id, mission_id):
    row = query_one(
        "SELECT * FROM mission_progress WHERE group_id = ? AND mission_id = ?",
        (group_id, mission_id),
    )
    if row:
        return row
    execute(   # OR IGNORE: dua request bersamaan untuk kelompok+misi yang sama tidak boleh saling menabrak (UNIQUE)
        "INSERT OR IGNORE INTO mission_progress (group_id, mission_id, status) VALUES (?, ?, 'in_progress')",
        (group_id, mission_id),
    )
    return query_one(
        "SELECT * FROM mission_progress WHERE group_id = ? AND mission_id = ?",
        (group_id, mission_id),
    )


def get_group_progress_map(group_id):
    """{ mission_key: mission_progress_row } — dipakai dashboard kelompok."""
    rows = query_all(
        """SELECT mp.*, m.mission_key FROM mission_progress mp
           JOIN missions m ON m.id = mp.mission_id
           WHERE mp.group_id = ?""",
        (group_id,),
    )
    return {r["mission_key"]: r for r in rows}


def get_group_mission_codes(group_id):
    """Kode global hanya dimunculkan untuk misi yang SUDAH diselesaikan kelompok ini."""
    rows = query_all(
        """SELECT m.mission_key, m.name FROM mission_progress mp
           JOIN missions m ON m.id = mp.mission_id
           WHERE mp.group_id = ? AND mp.status = 'completed'""",
        (group_id,),
    )
    return {r["mission_key"]: {"code": get_code(r["mission_key"]), "mission_key": r["mission_key"], "name": r["name"]} for r in rows}


def group_mission_code(group_id, mission):
    """Mission Code global jika kelompok sudah menyelesaikan misi ini, selain itu None."""
    row = query_one("SELECT status FROM mission_progress WHERE group_id = ? AND mission_id = ?", (group_id, mission["id"]))
    return get_code(mission["mission_key"]) if row and row["status"] == "completed" else None


def submit_mission_answers(group, mission, answers):
    """Pintu masuk penilaian. Mission 2 & 4: jeda jawaban salah dikendalikan di sini (backend), bukan oleh frontend."""
    if not cd.applies(mission["mission_key"]):
        return _grade_and_store(group, mission, answers)
    with cd.lock_for(group["id"], mission["id"]):
        left = cd.remaining(group["id"], mission["mission_key"], mission["id"])
        if left > 0:                                   # ditolak SEBELUM dinilai: tidak ada petunjuk benar/salah yang bocor
            return {"success": False, "reason": "cooldown", "remaining_seconds": left, "cooldown_seconds": cd.COOLDOWN_SECONDS}
        res = _grade_and_store(group, mission, answers)  # exception di sini -> 500, jeda TIDAK dibuat
        enabled = cd.is_enabled()
        if enabled and any(d.get("status") == "wrong" for d in res.get("details", {}).values()):
            cd.start(group["id"], mission["id"])
        res["cooldown"] = {"enabled": enabled, "seconds_left": cd.remaining(group["id"], mission["mission_key"], mission["id"]),
                           "total": cd.COOLDOWN_SECONDS}
        return res


def _grade_and_store(group, mission, answers):
    """
    group: dict (row groups); mission: dict (row missions)
    answers: { question_id: jawaban } — hanya soal yang dikirim yang diperiksa (per ID, bukan per urutan).

    Hasil per soal (details[qid].status):
      correct         : benar pada pengiriman ini (poin diberikan SEKALI)
      already_correct : sudah benar sebelumnya (tidak dinilai ulang, tidak ada poin tambahan)
      wrong           : salah; boleh diperbaiki dan dikirim lagi tanpa batas
      incomplete      : jawaban kosong/belum lengkap; tidak dinilai dan tidak dihitung percobaan
      invalid         : ID soal tidak dikenal / tidak aktif di misi ini
    Skor resmi selalu dihitung ulang dari database (SUM poin soal benar) sehingga kirim ulang tidak menggandakan poin.
    """
    progress = ensure_progress_row(group["id"], mission["id"])
    active_questions = {str(q["id"]): q for q in get_active_questions(mission["id"])}
    results, details = {}, {}
    graded = 0

    for qid_str, value in answers.items():
        qid_str = str(qid_str)
        question = active_questions.get(qid_str)
        if question is None:
            details[qid_str] = {"status": "invalid"}
            continue
        existing = query_one(
            "SELECT id, is_correct FROM question_progress WHERE group_id = ? AND question_id = ?",
            (group["id"], question["id"]),
        )
        if existing and existing["is_correct"]:
            results[qid_str] = True          # sudah benar: tidak dinilai ulang / tidak bisa dibatalkan
            details[qid_str] = {"status": "already_correct", "points_awarded": 0}
            continue
        if is_blank(question, value):
            details[qid_str] = {"status": "incomplete"}
            continue
        is_correct = check_answer(question, value)
        graded += 1
        results[qid_str] = is_correct
        # atomik: tidak pernah menimpa baris yang sudah benar, aman terhadap request bersamaan.
        # rowcount == 0 berarti request lain SUDAH mencatat benar lebih dulu -> ini bukan kiriman yang memberi poin (poin tepat sekali).
        conn = get_connection()
        try:
            changed = conn.execute(
                """INSERT INTO question_progress (group_id, question_id, is_correct, answered_at, last_answer)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(group_id, question_id) DO UPDATE
                   SET is_correct = excluded.is_correct, answered_at = excluded.answered_at, last_answer = excluded.last_answer
                   WHERE question_progress.is_correct = 0""",
                (group["id"], question["id"], 1 if is_correct else 0, now_str(), json.dumps(value, ensure_ascii=False)[:8000]),
            ).rowcount
            conn.commit()
        finally:
            conn.close()
        if changed == 0:
            results[qid_str] = True
            details[qid_str] = {"status": "already_correct", "points_awarded": 0}
            graded -= 1
            continue
        details[qid_str] = {"status": "correct" if is_correct else "wrong",
                            "points_awarded": question["points"] if is_correct else 0}

    if graded and progress["attempts"] == 0:
        execute("UPDATE mission_progress SET started_at = ? WHERE id = ?", (now_str(), progress["id"]))
        if group["status"] == "not_started":
            execute(
                "UPDATE groups SET status = 'in_progress', started_at = COALESCE(started_at, ?) WHERE id = ?",
                (now_str(), group["id"]),
            )

    correct_points = query_one(
        """SELECT COALESCE(SUM(q.points), 0) AS total FROM question_progress qp
           JOIN questions q ON q.id = qp.question_id
           WHERE qp.group_id = ? AND qp.is_correct = 1 AND q.mission_id = ? AND q.is_active = 1""",
        (group["id"], mission["id"]),
    )["total"]

    requirement = mission["requirement_points"]
    fresh = query_one("SELECT status FROM mission_progress WHERE id = ?", (progress["id"],))
    newly_completed = correct_points >= requirement and fresh["status"] != "completed"
    new_status = "completed" if correct_points >= requirement else "in_progress"

    execute(
        """UPDATE mission_progress
           SET status = ?, correct_points = ?, attempts = attempts + ?,
               completed_at = CASE WHEN ? = 'completed' AND completed_at IS NULL THEN ? ELSE completed_at END
           WHERE id = ?""",
        (new_status, correct_points, 1 if graded else 0, new_status, now_str(), progress["id"]),
    )

    mission_code = get_code(mission["mission_key"]) if new_status == "completed" else None
    if graded:
        log_activity(
            "mission_submit", group_id=group["id"], mission_id=mission["id"],
            detail=f"graded={graded}, correct_points={correct_points}/{requirement}",
        )
    if newly_completed:
        log_activity("mission_code_shown", group_id=group["id"], mission_id=mission["id"],
                     detail=f"Mission Code global ditampilkan untuk {mission['name']}")
        log_activity("mission_completed", group_id=group["id"], mission_id=mission["id"],
                     detail=f"{mission['name']} selesai")

    return {
        "success": True,
        "results": results, "details": details, "status": new_status,
        "correct_points": correct_points, "requirement_points": requirement,
        "mission_code": mission_code,
    }
