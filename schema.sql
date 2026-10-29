-- ============================================================================
-- OPERATION: RESTORE DATA LAB — schema.sql
-- Database existing project ini adalah SQLite (file tunggal, tanpa server
-- DB terpisah) supaya mudah dijalankan panitia di laptop mana pun tanpa
-- instalasi tambahan. Dieksekusi otomatis oleh db_layer/db.py saat pertama
-- kali dijalankan (CREATE TABLE IF NOT EXISTS -> aman dijalankan berulang).
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- PANITIA / ADMIN
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'admin',   -- 'admin' (role tunggal, siap dikembangkan)
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- KELOMPOK
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS groups (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    group_number  INTEGER UNIQUE NOT NULL,
    name          TEXT NOT NULL,
    access_code   TEXT,                              -- NULL/kosong = tidak butuh kode akses
    status        TEXT NOT NULL DEFAULT 'not_started',-- not_started/in_progress/completed
    started_at    TEXT,
    completed_at  TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- MISSION (5 mission tetap, konten sepenuhnya dapat diedit panitia)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS missions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_key         TEXT UNIQUE NOT NULL,          -- 'python' | 'analysis' | 'database' | 'algorithm' | 'knowledge'
    name                TEXT NOT NULL,
    icon                TEXT NOT NULL DEFAULT '🛰',
    description         TEXT NOT NULL DEFAULT '',
    instructions        TEXT NOT NULL DEFAULT '',
    is_active           INTEGER NOT NULL DEFAULT 1,     -- 0/1
    requirement_points  INTEGER NOT NULL DEFAULT 0,     -- poin minimal agar mission Completed
    mission_code_prefix TEXT NOT NULL DEFAULT 'MC',
    sort_order          INTEGER NOT NULL DEFAULT 0,
    station_mode        INTEGER NOT NULL DEFAULT 0,      -- 1 = mission ini dikerjakan di meja panitia (Mission 1 dan 3)
    station_password    TEXT                              -- password masuk station (NULL jika station_mode=0)
);

-- ---------------------------------------------------------------------------
-- KATEGORI SOAL (dapat ditambah/diedit panitia lewat Pengaturan Challenge)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT UNIQUE NOT NULL
);

-- ---------------------------------------------------------------------------
-- PERTANYAAN / BANK SOAL — dipakai oleh Mission 1, 2, 3, 5 (Mission 4 / Knowledge Core: bank soal di Website 2)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS questions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id     INTEGER NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    category       TEXT NOT NULL DEFAULT 'General Knowledge',
    prompt         TEXT NOT NULL,
    answer_type    TEXT NOT NULL DEFAULT 'text',
    -- text | number | essay | true_false | multiple_choice | multiple_select
    -- | ordering | matching
    correct_answer TEXT NOT NULL DEFAULT '',
    -- text: jawaban persis | true_false: 'true'/'false'
    -- multiple_choice: 1 opsi persis | multiple_select: JSON array opsi benar
    -- ordering: JSON array urutan benar | matching: JSON object {left: right}
    -- essay: tidak dipakai (dinilai otomatis selesai jika diisi)
    match_mode     TEXT NOT NULL DEFAULT 'case_insensitive', -- exact | case_insensitive | trim | space  (dipakai type text)
    options_json   TEXT,
    -- multiple_choice/multiple_select: JSON array pilihan
    -- ordering: JSON array item (ditampilkan teracak ke peserta)
    -- matching: JSON object {"left": [...], "right": [...]}
    points         INTEGER NOT NULL DEFAULT 1,
    is_active      INTEGER NOT NULL DEFAULT 1,
    sort_order     INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- PROGRESS PER KELOMPOK PER MISSION
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mission_progress (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id       INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    mission_id     INTEGER NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    status         TEXT NOT NULL DEFAULT 'locked',  -- locked | in_progress | completed
    correct_points INTEGER NOT NULL DEFAULT 0,
    attempts       INTEGER NOT NULL DEFAULT 0,
    started_at     TEXT,
    completed_at   TEXT,
    UNIQUE(group_id, mission_id)
);

-- Jawaban benar per soal per kelompok (supaya soal yang sudah benar tidak perlu diulang)
CREATE TABLE IF NOT EXISTS question_progress (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id     INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    question_id  INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    is_correct   INTEGER NOT NULL DEFAULT 0,
    answered_at  TEXT NOT NULL DEFAULT (datetime('now')),
    last_answer  TEXT,                           -- jawaban terakhir yang dikirim (JSON); dipulihkan per kelompok
    UNIQUE(group_id, question_id)
);

-- ---------------------------------------------------------------------------
-- MISSION CODE (satu per kelompok per mission, dibuat otomatis saat Completed)
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- FINAL CODE (dibuat oleh panitia lewat Final Mission Verification)
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- FINAL MISSION (submission peserta)
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- PENGATURAN CHALLENGE (generic key-value, dipakai utk konten Final Mission dll)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS challenge_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

-- ---------------------------------------------------------------------------
-- PRESENTATION (Presentation Sheet/PPT yang dapat dikustomisasi per kelompok)
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- ACTIVITY LOG
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL DEFAULT (datetime('now')),
    group_id   INTEGER REFERENCES groups(id) ON DELETE SET NULL,
    mission_id INTEGER REFERENCES missions(id) ON DELETE SET NULL,
    admin_id   INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    action     TEXT NOT NULL,
    detail     TEXT NOT NULL DEFAULT ''
);

-- ---------------------------------------------------------------------------
-- JEDA JAWABAN SALAH (hanya Mission 2 & 4): kapan kelompok boleh menjawab lagi. Waktu server (epoch detik).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS answer_cooldowns (
    group_id   INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    mission_id INTEGER NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    until_ts   REAL NOT NULL,
    PRIMARY KEY (group_id, mission_id)
);

CREATE INDEX IF NOT EXISTS idx_questions_mission ON questions(mission_id);
CREATE INDEX IF NOT EXISTS idx_progress_group ON mission_progress(group_id);
CREATE INDEX IF NOT EXISTS idx_qprogress_group ON question_progress(group_id);
CREATE INDEX IF NOT EXISTS idx_logs_ts ON activity_logs(ts DESC);
