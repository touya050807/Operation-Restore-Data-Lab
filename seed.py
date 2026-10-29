# ============================================================================
#  seed.py
#  Mengisi data awal supaya sistem langsung siap dipakai:
#  - 1 akun panitia default (WAJIB diganti passwordnya setelah login pertama)
#  - 10 kelompok
#  - 5 mission tetap: 1 Python Runtime, 2 Problem Analysis Center, 3 Database
#    Validation, 4 Algorithm Engine (5 algoritma, tanpa cooldown/timer), 5 Knowledge Core
#    (dikerjakan di WEBSITE 2, bank soalnya TIDAK ada di sini)
#  - Mission 1 (Python) dan 3 (Database) = STATION MODE dengan password meja
#    panitia (lihat STATION_PASSWORDS di bawah)
#  - Kategori Bank Soal bawaan
#  - Contoh soal beragam tipe jawaban per mission (Text/Number/Essay/
#    True-False/Multiple Choice/Multiple Select/Ordering/Matching) — panitia
#    bebas edit/tambah/hapus lewat Dashboard Panitia -> Bank Soal
#  - Pengaturan konten Final Mission bawaan
#
#  Jalankan sekali: `python seed.py`
#  Aman dijalankan berkali-kali — data yang sudah ada tidak ditimpa/diduplikasi.
# ============================================================================

import os
import json
from werkzeug.security import generate_password_hash

from db_layer.db import init_db, query_one, query_all, execute


# Kategori soal Mission 1, 2, 3 dan 4 di Website 1 (Admin dapat menambah lewat Category Management).
# Tujuh kategori Knowledge Core (Mission 5) ada di Website 2, bukan di sini.
DEFAULT_CATEGORIES = [
    "Google Colab", "Computational Thinking", "Basic Logic", "Simple Arithmetic", "Algoritma",
    # Mission 2 (5 topik penyusunan) dan Mission 1 (topik materi Python dasar)
    "Decomposition", "Pattern Recognition", "Abstraction", "Algorithm Design", "Logical Reasoning",
    "Variabel dan Tipe Data", "Input dan Output", "Operator", "Kondisi", "Komentar",
    "Struktur Data", "Perulangan", "Fungsi", "Mini Project",
]

# Mission 1 dan 3 dikerjakan di meja panitia -> wajib password.
STATION_PASSWORDS = {
    "python": "python123",
    "database": "database123",
}

MISSIONS = [
    dict(mission_key="python", name="Python Runtime", icon="⌨",
         description="Modul eksekusi kode Python mengalami crash berulang.",
         instructions="Peserta menyampaikan jawaban langsung ke panitia di meja Python Runtime untuk diinput.",
         mission_code_prefix="PY", sort_order=1, station_mode=1),
    dict(mission_key="analysis", name="Problem Analysis Center", icon="◈",
         description="Modul analisis kehilangan struktur berpikirnya.",
         instructions="Selesaikan studi kasus dengan pendekatan Computational Thinking langsung di perangkat kelompok.",
         mission_code_prefix="CT", sort_order=2, station_mode=0),
    dict(mission_key="database", name="Database Validation", icon="▤",
         description="Database mahasiswa terkontaminasi data rusak.",
         instructions="Peserta menyampaikan hasil analisis dataset langsung ke panitia di meja Database Validation.",
         mission_code_prefix="DB", sort_order=3, station_mode=1),
    dict(mission_key="algorithm", name="Algorithm Engine", icon="⌁",
         description="Algorithm Engine kehilangan urutan proses.",
         instructions=("Susun kelima algoritma dengan menggeser kartu langkah (drag-and-drop) atau tombol ▲▼, "
                       "lalu periksa. Semua algoritma harus benar. Tidak ada jeda atau batas waktu: boleh langsung memeriksa lagi."),
         mission_code_prefix="AG", sort_order=4, station_mode=0),
    dict(mission_key="knowledge", name="Knowledge Core", icon="🧠",
         description="Knowledge Core kehilangan basis pengetahuannya.",
         instructions="Dikerjakan di Website Knowledge Core (Mission 5): jawab soal tujuh kategori sampai 150 poin.",
         mission_code_prefix="KC", sort_order=5, station_mode=0),
]

# Mission 4 — Algorithm Engine: tepat 5 algoritma aktivitas sehari-hari, masing-masing >= 10 langkah.
# Di database kunci urutan benar disimpan di kolom correct_answer (tidak pernah dikirim ke browser);
# urutan yang tampil ke peserta diacak di server dan dijamin berbeda dari kunci.
ALGORITHMS = [
    ("Memasak Mi Instan", [
        "Siapkan satu bungkus mi instan, panci, dan semangkuk",
        "Isi panci dengan air secukupnya",
        "Panaskan air di atas kompor hingga mendidih",
        "Masukkan mi ke dalam air yang mendidih",
        "Aduk perlahan dan masak sekitar tiga menit",
        "Sambil menunggu, tuang bumbu ke dalam mangkuk",
        "Angkat mi yang sudah matang dan tiriskan",
        "Pindahkan mi ke mangkuk berisi bumbu",
        "Tambahkan sedikit air rebusan lalu aduk rata",
        "Matikan kompor dan sajikan mi selagi hangat",
    ]),
    ("Mencuci Pakaian dengan Mesin Cuci", [
        "Pisahkan pakaian putih dan pakaian berwarna",
        "Periksa dan kosongkan isi saku setiap pakaian",
        "Masukkan satu kelompok pakaian ke dalam tabung mesin cuci",
        "Tuangkan deterjen sesuai takaran",
        "Tutup pintu mesin cuci dan nyalakan mesin",
        "Pilih program cuci yang sesuai jenis pakaian",
        "Tekan tombol mulai dan tunggu proses cuci selesai",
        "Keluarkan pakaian yang sudah bersih dari tabung",
        "Jemur pakaian dengan gantungan di tempat yang terkena angin",
        "Angkat dan lipat pakaian setelah kering",
    ]),
    ("Memesan Ojek Online", [
        "Buka aplikasi ojek online di ponsel",
        "Aktifkan lokasi agar titik jemput terdeteksi",
        "Masukkan alamat tujuan perjalanan",
        "Periksa estimasi tarif dan rute yang ditampilkan",
        "Pilih jenis layanan yang diinginkan",
        "Tekan tombol pesan untuk mencari pengemudi",
        "Tunggu hingga pengemudi menerima pesanan",
        "Cocokkan nama dan nomor kendaraan dengan data di aplikasi",
        "Naik dan pakai helm selama perjalanan",
        "Bayar sesuai metode yang dipilih dan beri penilaian",
    ]),
    ("Meminjam Buku di Perpustakaan", [
        "Datang ke perpustakaan dan tunjukkan kartu anggota",
        "Cari judul buku melalui katalog atau komputer pencarian",
        "Catat kode rak buku yang tertera pada katalog",
        "Menuju rak yang sesuai dengan kode tersebut",
        "Ambil buku dan periksa kondisinya",
        "Bawa buku ke meja peminjaman",
        "Berikan buku dan kartu anggota kepada petugas",
        "Petugas mencatat peminjaman dan tanggal pengembalian",
        "Terima buku beserta bukti peminjaman",
        "Kembalikan buku ke perpustakaan sebelum tanggal pengembalian",
    ]),
    ("Berbelanja di Minimarket", [
        "Tulis daftar barang yang perlu dibeli",
        "Masuk ke minimarket dan ambil keranjang belanja",
        "Cari setiap barang di rak sesuai daftar",
        "Periksa harga dan tanggal kedaluwarsa pada kemasan",
        "Masukkan barang yang sesuai ke dalam keranjang",
        "Cocokkan isi keranjang dengan daftar belanja",
        "Antre di kasir sesuai urutan kedatangan",
        "Kasir memindai seluruh barang dan menghitung total",
        "Lakukan pembayaran dan terima kembalian bila ada",
        "Simpan struk lalu bawa barang belanjaan pulang",
    ]),
]


def _algorithm_questions():
    import random
    rnd = random.Random(2026)
    out = []
    for i, (title, steps) in enumerate(ALGORITHMS, start=1):
        shown = steps[:]
        rnd.shuffle(shown)
        out.append(dict(
            category="Algoritma",
            prompt=f"Algoritma {i} — {title}: susun langkah-langkah berikut menjadi urutan yang benar.",
            answer_type="ordering", options_json=json.dumps(shown, ensure_ascii=False),
            correct_answer=json.dumps(steps, ensure_ascii=False), points=1))
    return out

def _python_questions():
    from services.python_bank import questions
    return questions()


def _analysis_questions():
    from services.analysis_bank import questions
    return questions()


def _database_questions():
    from services.dataset_audit import build_questions
    return build_questions(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "student_dataset.csv"))[0]


# Soal contoh awal, sengaja beragam tipe jawaban (panitia bebas ubah semuanya
# lewat Dashboard Panitia -> Bank Soal).
SAMPLE_QUESTIONS = {
    # Mission 1: services/python_bank.py (materi Python dasar; kunci diverifikasi dengan MENJALANKAN kode di tests/test_w1_bank.py)
    "python": _python_questions(),
    # Mission 2 dan 3: soal & kunci dihasilkan KODE (services/analysis_bank.py, services/dataset_audit.py)
    "analysis": _analysis_questions(),
    "database": _database_questions(),
    # "knowledge": bank soal Knowledge Core berada di Website 2 (tidak dimuat di Website 1).
    # "algorithm": lihat ALGORITHMS di atas.
}

FINAL_MISSION_DEFAULT = {
    "case_study": (
        "Sistem peminjaman laboratorium ITSB sering mengalami bentrok jadwal sehingga banyak "
        "mahasiswa tidak memperoleh jadwal praktikum."
    ),
    "fields": [
        {"id": "masalah_utama", "label": "Masalah Utama", "icon": "❓", "type": "textarea"},
        {"id": "decomposition", "label": "Decomposition", "icon": "🧩", "type": "textarea"},
        {"id": "pattern_recognition", "label": "Pattern Recognition", "icon": "🔍", "type": "textarea"},
        {"id": "abstraction", "label": "Abstraction", "icon": "🎯", "type": "textarea"},
        {"id": "algoritma", "label": "Algoritma", "icon": "📜", "type": "textarea"},
        {"id": "program_python", "label": "Program Python Sederhana", "icon": "🐍", "type": "code"},
        {"id": "kesimpulan", "label": "Kesimpulan", "icon": "✅", "type": "textarea"},
    ],
}


def _sync_algorithms(mission_id):
    """Jika soal algoritma di database berbeda dari 5 algoritma terbaru, hapus yang lama
    (beserta progres soalnya) lalu biarkan seeding mengisi ulang. Progres mission dihitung ulang."""
    want = {f"Algoritma {i} — {t}: susun langkah-langkah berikut menjadi urutan yang benar."
            for i, (t, _s) in enumerate(ALGORITHMS, start=1)}
    have = {r["prompt"] for r in query_all("SELECT prompt FROM questions WHERE mission_id = ?", (mission_id,))}
    if have and have != want:
        execute("DELETE FROM question_progress WHERE question_id IN (SELECT id FROM questions WHERE mission_id = ?)", (mission_id,))
        execute("DELETE FROM questions WHERE mission_id = ?", (mission_id,))
        execute("UPDATE mission_progress SET status='in_progress', correct_points=0, completed_at=NULL WHERE mission_id = ?", (mission_id,))


def ensure_missions():
    """Idempoten: membuat/menyelaraskan 5 mission (urutan, mode station, soal Algorithm Engine).
    Dipanggil dari seed() DAN saat app start, sehingga database lama otomatis mengikuti pembagian website terbaru."""
    for m in MISSIONS:
        existing = query_one("SELECT id FROM missions WHERE mission_key = ?", (m["mission_key"],))
        if existing:
            mission_id = existing["id"]
            # migrasi DB lama: samakan urutan & mode station dengan pembagian website terbaru
            execute(
                """UPDATE missions SET station_mode = ?, sort_order = ?,
                   station_password = CASE WHEN ? = 1 THEN COALESCE(station_password, ?) ELSE NULL END
                   WHERE id = ?""",
                (m["station_mode"], m["sort_order"], m["station_mode"],
                 STATION_PASSWORDS.get(m["mission_key"]), mission_id),
            )
        else:
            mission_id = execute(
                """INSERT INTO missions
                   (mission_key, name, icon, description, instructions, mission_code_prefix, sort_order,
                    station_mode, station_password)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (m["mission_key"], m["name"], m["icon"], m["description"], m["instructions"],
                 m["mission_code_prefix"], m["sort_order"], m["station_mode"],
                 STATION_PASSWORDS.get(m["mission_key"])),
            )
            requirement = 150 if m["mission_key"] == "knowledge" else 0   # Knowledge Core: target 150 poin (dinilai di Website 2)
            execute("UPDATE missions SET requirement_points = ? WHERE id = ?", (requirement, mission_id))

        # soal awal hanya diisi bila mission belum punya soal sama sekali (tidak menimpa/menggandakan)
        if m["mission_key"] == "algorithm":
            _sync_algorithms(mission_id)     # ganti set algoritma lama (jika ada) dengan 5 algoritma terbaru
        elif m["mission_key"] == "knowledge":
            execute("UPDATE missions SET requirement_points = 150 WHERE id = ?", (mission_id,))
        has_q = query_one("SELECT 1 FROM questions WHERE mission_id = ? LIMIT 1", (mission_id,))
        if has_q:
            continue
        questions = _algorithm_questions() if m["mission_key"] == "algorithm" else SAMPLE_QUESTIONS.get(m["mission_key"], [])
        total_points = 0
        for i, q in enumerate(questions):
            execute(
                """INSERT INTO questions
                   (mission_id, category, prompt, answer_type, correct_answer, match_mode,
                    options_json, points, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (mission_id, q["category"], q["prompt"], q["answer_type"], q.get("correct_answer", ""),
                 q.get("match_mode", "case_insensitive"), q.get("options_json"), q["points"], i),
            )
            total_points += q["points"]
        if questions and m["mission_key"] != "knowledge":
            # Mission 1,2,3 dan 5: seluruh poin harus benar
            execute("UPDATE missions SET requirement_points = ? WHERE id = ?", (total_points, mission_id))
    _migrate_question_banks()
    _sync_database_keys()



# Soal lama yang diganti pada versi bank 4 (di-NONAKTIFKAN, tidak dihapus: riwayat lama tetap aman).
LEGACY_PROMPTS = {
    "python": ["Jelaskan mengapa kode `for i in range(len(data) + 1)`"],
    "analysis": ["Susun tahapan Computational Thinking berikut menjadi urutan yang benar.",
                 "Manakah yang termasuk 4 pilar Computational Thinking?",       # v6: diganti soal Abstraction yang lebih pasti
                 "Nilai empat anggota sebuah tim: 72, 85, 90, 69."],              # v6: diganti versi dengan data tak relevan

    "database": ["Unduh dataset student_dataset.csv. Berapa jumlah baris dengan Missing Value",
                 "Berapa jumlah baris dengan Invalid Email?", "Berapa jumlah baris dengan Invalid NIM?",
                 "Jelaskan langkah-langkah yang kalian lakukan untuk membersihkan data"],
}
BANK_VERSION = "6"


def _sync_database_keys():
    """Kunci soal Database SELALU mengikuti CSV terbaru (dihitung ulang saat start; 150 baris -> milidetik)."""
    m = query_one("SELECT id FROM missions WHERE mission_key = 'database'")
    if not m:
        return
    for q in SAMPLE_QUESTIONS["database"]:
        execute("UPDATE questions SET correct_answer = ? WHERE mission_id = ? AND prompt = ?",
                (q["correct_answer"], m["id"], q["prompt"]))


def _migrate_question_banks():
    """Idempoten. Database lama -> soal objektif baru (analysis/database/python), tanpa menghapus data lama."""
    cur = query_one("SELECT value FROM challenge_settings WHERE key = 'question_bank_version'")
    if cur and cur["value"] == BANK_VERSION:
        return
    for key, starts in LEGACY_PROMPTS.items():
        m = query_one("SELECT id FROM missions WHERE mission_key = ?", (key,))
        if not m:
            continue
        for st in starts:
            execute("UPDATE questions SET is_active = 0 WHERE mission_id = ? AND substr(prompt, 1, ?) = ?",
                    (m["id"], len(st), st))
        order = query_one("SELECT COALESCE(MAX(sort_order), 0) n FROM questions WHERE mission_id = ?", (m["id"],))["n"]
        if key == "python":
            # v6: teks soal Python dirapikan (kode di blok yang bisa disalin ke Colab). PERBARUI soal yang sama (id & riwayat tetap)
            from services.python_bank import items as _py_items
            for it in _py_items():
                mm = it.get("match_mode", "case_insensitive")
                execute("""UPDATE questions SET prompt = ?, match_mode = ?
                           WHERE mission_id = ? AND prompt = ?
                             AND NOT EXISTS (SELECT 1 FROM questions q2 WHERE q2.mission_id = ? AND q2.prompt = ?)""",
                        (it["prompt"], mm, m["id"], it["prev_prompt"], m["id"], it["prompt"]))
                execute("UPDATE questions SET match_mode = ? WHERE mission_id = ? AND prompt = ?", (mm, m["id"], it["prompt"]))
        if key in ("python", "analysis"):
            # soal lama yang dipertahankan: perbarui topik (kategori) dan urutan tampil; poin/kunci/riwayat TIDAK diubah
            for pos, q in enumerate(SAMPLE_QUESTIONS.get(key, [])):
                execute("UPDATE questions SET category = ?, sort_order = ? WHERE mission_id = ? AND prompt = ?",
                        (q["category"], pos, m["id"], q["prompt"]))
            order = len(SAMPLE_QUESTIONS.get(key, [])) + 100
        for q in SAMPLE_QUESTIONS.get(key, []):
            if query_one("SELECT 1 FROM questions WHERE mission_id = ? AND prompt = ?", (m["id"], q["prompt"])):
                continue
            order += 1
            execute("""INSERT INTO questions (mission_id, category, prompt, answer_type, correct_answer, match_mode,
                       options_json, points, sort_order) VALUES (?,?,?,?,?,?,?,?,?)""",
                    (m["id"], q["category"], q["prompt"], q["answer_type"], q.get("correct_answer", ""),
                     q.get("match_mode", "case_insensitive"), q.get("options_json"), q["points"], order))
        total = query_one("SELECT COALESCE(SUM(points), 0) t FROM questions WHERE mission_id = ? AND is_active = 1", (m["id"],))["t"]
        execute("UPDATE missions SET requirement_points = ? WHERE id = ?", (total, m["id"]))
    execute("INSERT INTO challenge_settings (key, value) VALUES ('question_bank_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (BANK_VERSION,))


def seed():
    init_db()

    # --- admin default ---
    if not query_one("SELECT id FROM admins WHERE username = ?", ("admin",)):
        execute(
            "INSERT INTO admins (username, password_hash, role) VALUES (?, ?, 'admin')",
            ("admin", generate_password_hash(os.environ.get("ADMIN_PASSWORD", "axis2026"))),
        )
        print("Admin default dibuat -> username: admin | password: axis2026 (SEGERA GANTI)")

    # --- kelompok: dibaca dari data/groups.json (file yang SAMA dipakai Website 2 & 3) ---
    gpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "groups.json")
    with open(gpath, encoding="utf-8") as f:
        group_defs = json.load(f)
    for gd in group_defs:
        if not query_one("SELECT id FROM groups WHERE group_number = ?", (gd["group_number"],)):
            execute(
                "INSERT INTO groups (group_number, name, access_code, status) VALUES (?, ?, ?, 'not_started')",
                (gd["group_number"], gd["name"], gd.get("access_code")),
            )

    # --- kategori ---
    for cat in DEFAULT_CATEGORIES:
        if not query_one("SELECT id FROM categories WHERE name = ?", (cat,)):
            execute("INSERT INTO categories (name) VALUES (?)", (cat,))

    ensure_missions()

    # --- password Final Mission Station (station khusus verifikasi Mission Code -> Final Code) ---
    if not query_one("SELECT key FROM challenge_settings WHERE key = 'final_station_password'"):
        execute(
            "INSERT INTO challenge_settings (key, value) VALUES ('final_station_password', 'final123')"
        )

    print("Seed selesai.")
    print("Password station -> Python: python123 | Database: database123")
    print("Password Final Mission Station -> final123")


if __name__ == "__main__":
    seed()
