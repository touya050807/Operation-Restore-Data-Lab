# ============================================================================
#  db_layer/db.py
#  Lapisan akses database (SQLite, file tunggal — tidak perlu server DB
#  terpisah). Dipakai oleh seluruh services/. Skema didefinisikan di
#  schema.sql pada root project dan dijalankan otomatis (idempotent, aman
#  dijalankan berkali-kali) lewat init_db().
# ============================================================================

import os
import sqlite3

from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DB_PATH = os.environ.get("DB_PATH") or os.path.join(INSTANCE_DIR, "challenge.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


_WAL_READY = set()


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL tersimpan di file DB: cukup diset SEKALI per proses. Menjalankannya di setiap koneksi membuat
    # request bersamaan gagal "database is locked" (PRAGMA journal_mode tidak menunggu busy timeout).
    if DB_PATH not in _WAL_READY:
        conn.execute("PRAGMA journal_mode = WAL")
        _WAL_READY.add(DB_PATH)
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _ensure_column(conn, table, column, coltype_sql):
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype_sql}")


def init_db():
    """Buat seluruh tabel jika belum ada. Aman dipanggil setiap start-up
    (dipakai juga sebagai mekanisme 'migration' sederhana: menambah tabel
    baru tanpa menghapus data existing)."""
    conn = get_connection()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    # migrasi ringan: tambah kolom baru pada tabel yang sudah ada dari revisi
    # sebelumnya (CREATE TABLE IF NOT EXISTS tidak menambah kolom baru sendiri)
    _ensure_column(conn, "missions", "station_mode", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column(conn, "missions", "station_password", "TEXT")

    # revisi v3: TIDAK ADA timer/cooldown/batas waktu -> buang kolom lama bila ada (SQLite >= 3.35).
    for table, col in (("missions", "retry_delay_seconds"), ("missions", "duration_seconds"),
                       ("mission_progress", "locked_until")):
        cols = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if col in cols:
            try:
                conn.execute(f"ALTER TABLE {table} DROP COLUMN {col}")
            except Exception:      # SQLite lama: kolom dibiarkan, tidak pernah dibaca/ditulis
                pass

    # revisi v7: jawaban TERAKHIR yang dikirim per kelompok+soal (JSON) agar dapat dipulihkan saat panitia/peserta kembali ke kelompok itu
    _ensure_column(conn, "question_progress", "last_answer", "TEXT")

    # revisi: Category Management (deskripsi + status aktif)
    _ensure_column(conn, "categories", "description", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn, "categories", "is_active", "INTEGER NOT NULL DEFAULT 1")

    # revisi: akun staff role PANITIA (akun role 'admin' dapat memilih PANITIA atau ADMIN;
    # akun role 'panitia' HANYA dapat memilih PANITIA). Password default -> segera ganti.
    if not conn.execute("SELECT 1 FROM admins WHERE username = 'panitia'").fetchone():
        conn.execute(
            "INSERT INTO admins (username, password_hash, role) VALUES ('panitia', ?, 'panitia')",
            (generate_password_hash(os.environ.get("PANITIA_PASSWORD", "panitia2026")),),
        )

    # password awal dapat dipaksa lewat environment variable (dipakai saat start; idempotent)
    for uname, envname in (("admin", "ADMIN_PASSWORD"), ("panitia", "PANITIA_PASSWORD")):
        pw = os.environ.get(envname, "")
        if pw:
            conn.execute("UPDATE admins SET password_hash = ? WHERE username = ?",
                         (generate_password_hash(pw), uname))

    conn.commit()
    conn.close()


def query_all(sql, params=()):
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_one(sql, params=()):
    conn = get_connection()
    row = conn.execute(sql, params).fetchone()
    conn.close()
    return dict(row) if row else None


def execute(sql, params=()):
    """INSERT/UPDATE/DELETE. Mengembalikan lastrowid (berguna untuk INSERT)."""
    conn = get_connection()
    cur = conn.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def execute_many(sql, seq_of_params):
    conn = get_connection()
    conn.executemany(sql, seq_of_params)
    conn.commit()
    conn.close()
