# ============================================================================
#  services/reset_service.py — RESET SELURUH PENGERJAAN SATU KELOMPOK pada WEBSITE 1 SAJA.
#  Satu kelompok, satu website, satu tindakan, dalam SATU transaksi (semua atau tidak sama sekali).
#  Dihapus: hasil jawaban per soal (question_progress, Mission 1-4) dan progres/status/Mission Code per misi
#           (mission_progress), status kelompok. Final Code Station tidak menyimpan status per kelompok
#           (hanya memverifikasi kode global) sehingga tidak ada yang perlu dihapus di sana.
#  TIDAK disentuh: identitas kelompok, bank soal, kunci, konfigurasi, kelompok lain, Website 2 dan 3, Activity Log.
#  `reset_epoch` naik -> draft jawaban di browser kelompok itu (localStorage) tidak dipulihkan lagi.
# ============================================================================
from db_layer.db import get_connection

EPOCH_KEY = "reset_epoch_g{}"


def get_epoch(group_number):
    conn = get_connection()
    try:
        r = conn.execute("SELECT value FROM challenge_settings WHERE key = ?", (EPOCH_KEY.format(group_number),)).fetchone()
        return int(r["value"]) if r and str(r["value"]).isdigit() else 0
    finally:
        conn.close()


def group_overview(group_number):
    conn = get_connection()
    try:
        gid = conn.execute("SELECT id FROM groups WHERE group_number = ?", (group_number,)).fetchone()
        if not gid:
            return None
        gid = gid["id"]
        a = conn.execute("SELECT COUNT(*) n, COALESCE(SUM(is_correct),0) c FROM question_progress WHERE group_id = ?", (gid,)).fetchone()
        m = conn.execute("SELECT COUNT(*) n, COALESCE(SUM(status='completed'),0) c FROM mission_progress WHERE group_id = ?", (gid,)).fetchone()
        return {"answered": a["n"], "correct": a["c"], "missions": m["n"], "completed": m["c"]}
    finally:
        conn.close()


def reset_group(group_number, admin_id=None):
    """Return dict ringkasan. Raise ValueError bila kelompok tidak valid. Exception lain -> rollback penuh."""
    if not isinstance(group_number, int) or isinstance(group_number, bool) or not 1 <= group_number <= 5:
        raise ValueError("invalid_group")
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT id FROM groups WHERE group_number = ?", (group_number,)).fetchone()
        if not row:
            raise ValueError("invalid_group")
        gid = row["id"]
        q = conn.execute("DELETE FROM question_progress WHERE group_id = ?", (gid,)).rowcount
        m = conn.execute("DELETE FROM mission_progress WHERE group_id = ?", (gid,)).rowcount
        conn.execute("DELETE FROM answer_cooldowns WHERE group_id = ?", (gid,))     # jeda jawaban salah ikut direset
        conn.execute("UPDATE groups SET status = 'not_started', started_at = NULL, completed_at = NULL WHERE id = ?", (gid,))
        key = EPOCH_KEY.format(group_number)
        cur = conn.execute("SELECT value FROM challenge_settings WHERE key = ?", (key,)).fetchone()
        epoch = (int(cur["value"]) if cur and str(cur["value"]).isdigit() else 0) + 1
        conn.execute("INSERT INTO challenge_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(epoch)))
        conn.execute("INSERT INTO activity_logs (group_id, admin_id, action, detail) VALUES (?, ?, 'group_reset', ?)",
                     (gid, admin_id, f"Reset pengerjaan Kelompok {group_number} di Website 1: {q} jawaban, {m} progres misi dihapus"))
        conn.commit()
        return {"group_number": group_number, "answers_deleted": q, "mission_progress_deleted": m, "epoch": epoch}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
