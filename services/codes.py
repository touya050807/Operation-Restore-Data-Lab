# ============================================================================
#  services/codes.py — SATU Mission Code global per misi + SATU Final Code global.
#  Sumber nilai (prioritas): environment variable -> challenge_settings (DB) -> default.
#  MISSION5_CODE (Knowledge Core, Website 2) dan FINAL_CODE (Website 3) harus SAMA persis
#  dengan env var di website tersebut. MISSION4_CODE (Algorithm Engine) hanya dipakai di sini.
# ============================================================================
import os
import hashlib

from db_layer.db import query_one, execute

DEFAULT_CODES = {
    "python": "PY-AXIS", "analysis": "CT-AXIS", "database": "DB-AXIS",
    "knowledge": "KC-AXIS", "algorithm": "ALG-AXIS",
}
DEFAULT_FINAL = "RESTORE-AXIS-2026"
ENV_KEYS = {"python": "MISSION1_CODE", "analysis": "MISSION2_CODE", "database": "MISSION3_CODE",
            "algorithm": "MISSION4_CODE", "knowledge": "MISSION5_CODE", "final": "FINAL_CODE"}


def norm(code):
    return str(code or "").strip().upper()


def _db_key(key):
    return "final_code" if key == "final" else f"mission_code_{key}"


def code_source(key):
    env = ENV_KEYS.get(key)
    return "env" if env and norm(os.environ.get(env)) else "db"


def get_code(key):
    env = ENV_KEYS.get(key)
    if env and norm(os.environ.get(env)):
        return norm(os.environ[env])
    row = query_one("SELECT value FROM challenge_settings WHERE key = ?", (_db_key(key),))
    if row and norm(row["value"]):
        return norm(row["value"])
    return DEFAULT_FINAL if key == "final" else DEFAULT_CODES.get(key, "")


def set_code(key, value):
    """False jika nilai dikunci oleh environment variable atau kosong."""
    value = norm(value)
    if not value or code_source(key) == "env":
        return False
    execute(
        """INSERT INTO challenge_settings (key, value) VALUES (?, ?)
           ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
        (_db_key(key), value),
    )
    return True


def get_final_code():
    return get_code("final")


def fingerprint(code):
    """Sidik jari non-reversibel (8 hex) untuk membandingkan kode antarwebsite tanpa membocorkannya."""
    return hashlib.sha256(norm(code).encode()).hexdigest()[:8]


def init_codes():
    for key, default in list(DEFAULT_CODES.items()) + [("final", DEFAULT_FINAL)]:
        if not query_one("SELECT 1 FROM challenge_settings WHERE key = ?", (_db_key(key),)):
            execute("INSERT INTO challenge_settings (key, value) VALUES (?, ?)", (_db_key(key), default))
