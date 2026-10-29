# ============================================================================
#  services/cooldown_service.py — JEDA 30 DETIK SETELAH JAWABAN SALAH.
#  Hanya Mission 2 (analysis) dan Mission 4 (algorithm). Misi/website lain tidak memakai jeda.
#  Dikuasai BACKEND: waktu server (time.time), disimpan di tabel answer_cooldowns (bertahan saat refresh/restart).
#  Pengaturan aktif/nonaktif disimpan di challenge_settings (default AKTIF) dan diubah hanya oleh Admin.
#  Pemeriksaan + pemberian jeda untuk satu (kelompok, misi) dilakukan di bawah kunci proses agar permintaan paralel
#  tidak dapat menembus jeda (deployment: 1 worker gunicorn; lihat README).
#  Error jaringan/server tidak pernah memicu jeda: jeda hanya dibuat setelah server MENILAI jawaban dan hasilnya salah.
# ============================================================================
import math
import threading
import time
from collections import defaultdict

from db_layer.db import execute, query_one

COOLDOWN_MISSIONS = frozenset({"analysis", "algorithm"})
COOLDOWN_SECONDS = 30
SETTING_KEY = "wrong_cooldown_enabled"

_locks = defaultdict(threading.Lock)


def applies(mission_key):
    return mission_key in COOLDOWN_MISSIONS


def is_enabled():
    r = query_one("SELECT value FROM challenge_settings WHERE key = ?", (SETTING_KEY,))
    return not (r and str(r["value"]).strip() == "0")          # tidak ada pengaturan = aktif


def set_enabled(on):
    execute("INSERT INTO challenge_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (SETTING_KEY, "1" if on else "0"))


def lock_for(group_id, mission_id):
    return _locks[(group_id, mission_id)]


def remaining(group_id, mission_key, mission_id):
    """Sisa detik (dibulatkan ke atas) atau 0. Selalu 0 bila misi tidak memakai jeda atau pengaturan nonaktif."""
    if not applies(mission_key) or not is_enabled():
        return 0
    r = query_one("SELECT until_ts FROM answer_cooldowns WHERE group_id = ? AND mission_id = ?", (group_id, mission_id))
    if not r:
        return 0
    return max(0, math.ceil(r["until_ts"] - time.time()))


def start(group_id, mission_id):
    execute("""INSERT INTO answer_cooldowns (group_id, mission_id, until_ts) VALUES (?, ?, ?)
               ON CONFLICT(group_id, mission_id) DO UPDATE SET until_ts = excluded.until_ts""",
            (group_id, mission_id, time.time() + COOLDOWN_SECONDS))
