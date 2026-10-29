"""Audit kualitas data untuk Mission 3 — Database Validation.

SEMUA angka jawaban dihitung dari CSV final lewat fungsi di sini (bukan diketik manual).
Fungsi `audit()` dijalankan sekali saat seed / saat CSV berubah; hasilnya menjadi kunci soal di database.

DEFINISI (dipakai identik oleh semua pertanyaan; teks definisi juga ditampilkan di soal):
  * Sel kosong        : sel yang setelah di-strip tidak berisi karakter apa pun. "-", "N/A", "NULL" BUKAN sel kosong.
  * Tanda "-"          : sel yang isinya tepat "-" (dihitung terpisah dari sel kosong).
  * NIM valid          : tepat 8 digit angka.
      - NIM kosong      : sel kosong.
      - NIM tidak lengkap: tidak kosong, hanya angka, panjang < 8 digit.
      - NIM berformat tidak valid: tidak kosong dan mengandung karakter selain angka.
  * Email tanpa @      : email TIDAK kosong dan tidak mengandung karakter "@".
  * Email tidak valid  : email TIDAK kosong dan tidak cocok pola  ^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$
                         (mencakup 'email tanpa @' sebagai himpunan bagian; email kosong tidak termasuk).
  * Kolom nilai       : Nilai_Tugas, Nilai_UTS, Nilai_UAS.
      - Non-numerik     : tidak kosong, bukan "-", dan tidak dapat dibaca sebagai bilangan (mis. "abc", "N/A", "80a").
      - Di luar rentang : dapat dibaca sebagai bilangan tetapi < 0 atau > 100.
  * Kehadiran di luar rentang : bilangan < 0 atau > 100 (sel kosong dan non-numerik tidak dihitung di sini).
  * Semester di luar rentang  : bilangan bulat di luar 1..8 (sel kosong/non-angka tidak dihitung).
  * Tanggal tidak valid: tidak kosong dan bukan tanggal kalender nyata berformat YYYY-MM-DD.
  * Prodi tidak sesuai daftar: tidak kosong dan tidak termasuk {Sains Data, Teknologi Informasi, Sistem Informasi, Teknik Industri}.
  * Sel bermasalah     : sel yang melanggar SETIDAKNYA SATU aturan kolomnya (kosong, "-", non-numerik, di luar rentang,
                         NIM/Email/Tanggal/Semester/Prodi tidak valid). Satu sel dihitung satu kali.
  * Baris bersih       : baris tanpa satu pun sel bermasalah.
ID_Data dan Nama dianggap tidak punya aturan validasi kecuali tidak boleh kosong (di dataset ini tidak ada yang kosong).
"""
import csv
import re
from datetime import datetime

PRODI_VALID = {"Sains Data", "Teknologi Informasi", "Sistem Informasi", "Teknik Industri"}
NILAI_COLS = ("Nilai_Tugas", "Nilai_UTS", "Nilai_UAS")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _is_number(s):
    v = _num(s)
    return v is not None and v == v and v not in (float("inf"), float("-inf"))


def valid_date(s):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return False
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def cell_problems(col, raw):
    """Daftar label masalah untuk satu sel (kosong jika sel valid)."""
    v = (raw or "").strip()
    out = []
    if v == "":
        return ["kosong"]
    if col == "NIM":
        if not re.fullmatch(r"[0-9]+", v):
            out.append("nim_format")            # mengandung karakter selain angka
        elif len(v) < 8:
            out.append("nim_tidak_lengkap")     # hanya angka tetapi < 8 digit
        elif len(v) > 8:
            out.append("nim_format")            # hanya angka tetapi > 8 digit
    elif col == "Email":
        if not EMAIL_RE.match(v):
            out.append("email_tidak_valid")
            if "@" not in v:
                out.append("email_tanpa_at")
    elif col in NILAI_COLS:
        if v == "-":
            out.append("strip")
        elif not _is_number(v):
            out.append("nonnumerik")
        elif not (0 <= _num(v) <= 100):
            out.append("di_luar_rentang")
    elif col == "Kehadiran":
        if v == "-":
            out.append("strip")
        elif not _is_number(v):
            out.append("nonnumerik")
        elif not (0 <= _num(v) <= 100):
            out.append("kehadiran_luar")
    elif col == "Semester":
        if not _is_number(v) or _num(v) != int(_num(v)):
            out.append("semester_nonangka")
        elif not (1 <= int(_num(v)) <= 8):
            out.append("semester_luar")
    elif col == "Tanggal_Input":
        if not valid_date(v):
            out.append("tanggal_tidak_valid")
    elif col == "Prodi":
        if v not in PRODI_VALID:
            out.append("prodi_tidak_valid")
    return out


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r.fieldnames), list(r)


def audit(path):
    cols, rows = read_rows(path)
    m = {"baris": len(rows), "kolom": cols}
    cnt = lambda pred: sum(1 for r in rows if pred(r))
    m["sel_kosong"] = sum(1 for r in rows for c in cols if (r[c] or "").strip() == "")
    m["nim_kosong"] = cnt(lambda r: (r["NIM"] or "").strip() == "")
    m["nim_tidak_lengkap"] = cnt(lambda r: "nim_tidak_lengkap" in cell_problems("NIM", r["NIM"]))
    m["nim_format"] = cnt(lambda r: "nim_format" in cell_problems("NIM", r["NIM"]))
    m["email_kosong"] = cnt(lambda r: (r["Email"] or "").strip() == "")
    m["email_tanpa_at"] = cnt(lambda r: "email_tanpa_at" in cell_problems("Email", r["Email"]))
    m["email_tidak_valid"] = cnt(lambda r: "email_tidak_valid" in cell_problems("Email", r["Email"]))
    m["uts_strip"] = cnt(lambda r: (r["Nilai_UTS"] or "").strip() == "-")
    m["nilai_strip"] = sum(1 for r in rows for c in NILAI_COLS if (r[c] or "").strip() == "-")
    m["nilai_nonnumerik"] = sum(1 for r in rows for c in NILAI_COLS if "nonnumerik" in cell_problems(c, r[c]))
    m["nilai_luar"] = sum(1 for r in rows for c in NILAI_COLS if "di_luar_rentang" in cell_problems(c, r[c]))
    m["kehadiran_luar"] = cnt(lambda r: "kehadiran_luar" in cell_problems("Kehadiran", r["Kehadiran"]))
    m["semester_luar"] = cnt(lambda r: "semester_luar" in cell_problems("Semester", r["Semester"]))
    m["tanggal_tidak_valid"] = cnt(lambda r: "tanggal_tidak_valid" in cell_problems("Tanggal_Input", r["Tanggal_Input"]))
    m["prodi_tidak_valid"] = cnt(lambda r: "prodi_tidak_valid" in cell_problems("Prodi", r["Prodi"]))
    bad_cells = sum(1 for r in rows for c in cols if cell_problems(c, r[c]))
    m["sel_bermasalah"] = bad_cells
    m["baris_bersih"] = cnt(lambda r: not any(cell_problems(c, r[c]) for c in cols))
    m["baris_bermasalah"] = m["baris"] - m["baris_bersih"]
    return m


def _preamble():
    return "Gunakan dataset student_dataset.csv (baris data = semua baris selain header). "


def build_questions(path):
    """Soal Database Validation: SEMUA kunci berasal dari audit(path). Tipe jawaban: angka."""
    m = audit(path)
    P = _preamble()
    items = [
        ("Berapa jumlah baris data dalam dataset (tidak termasuk baris header)?", m["baris"]),
        ("Berapa jumlah seluruh sel kosong di semua kolom dan semua baris? Definisi: sel kosong = tidak berisi karakter apa pun; tanda \"-\", \"N/A\" atau teks lain BUKAN sel kosong.", m["sel_kosong"]),
        ("Berapa jumlah baris dengan NIM kosong?", m["nim_kosong"]),
        ("Berapa jumlah baris dengan NIM tidak lengkap? Definisi: NIM valid tepat 8 digit angka; NIM tidak lengkap = tidak kosong, hanya berisi angka, dan kurang dari 8 digit.", m["nim_tidak_lengkap"]),
        ("Berapa jumlah baris dengan NIM berformat tidak valid? Definisi: NIM tidak kosong dan mengandung setidaknya satu karakter selain angka.", m["nim_format"]),
        ("Berapa jumlah baris dengan Email kosong?", m["email_kosong"]),
        ("Berapa jumlah baris dengan Email tidak kosong tetapi tidak mengandung karakter @?", m["email_tanpa_at"]),
        ("Berapa jumlah baris dengan Email tidak valid? Definisi: email tidak kosong dan tidak cocok pola teks@domain.akhiran (satu @, ada teks sebelum dan sesudahnya, domain memuat titik). Kategori ini sudah mencakup email tanpa @; email kosong tidak dihitung.", m["email_tidak_valid"]),
        ("Berapa jumlah baris yang kolom Nilai_UTS-nya berisi tanda \"-\" (tepat satu karakter minus)? Sel kosong tidak dihitung.", m["uts_strip"]),
        ("Berapa jumlah SEL pada kolom Nilai_Tugas, Nilai_UTS, dan Nilai_UAS yang non-numerik? Definisi: sel tidak kosong, bukan \"-\", dan tidak dapat dibaca sebagai bilangan (contoh: teks, \"N/A\", \"80a\").", m["nilai_nonnumerik"]),
        ("Berapa jumlah SEL pada kolom Nilai_Tugas, Nilai_UTS, dan Nilai_UAS yang berupa angka tetapi di luar rentang 0 sampai 100 (kurang dari 0 atau lebih dari 100)?", m["nilai_luar"]),
        ("Berapa jumlah baris dengan Kehadiran berupa angka di luar rentang 0 sampai 100? Sel kosong tidak dihitung.", m["kehadiran_luar"]),
        ("Berapa jumlah baris dengan Semester berupa angka di luar rentang 1 sampai 8? Sel kosong tidak dihitung.", m["semester_luar"]),
        ("Berapa jumlah baris dengan Tanggal_Input tidak valid? Definisi: sel tidak kosong dan bukan tanggal kalender nyata berformat YYYY-MM-DD (contoh tidak valid: 2025-02-30, 2025-13-05, 31-12-2025).", m["tanggal_tidak_valid"]),
        ("Berapa jumlah baris dengan Prodi tidak sesuai daftar? Daftar valid: Sains Data, Teknologi Informasi, Sistem Informasi, Teknik Industri (huruf dan ejaan harus sama persis). Sel kosong tidak dihitung.", m["prodi_tidak_valid"]),
        ("Berapa jumlah baris BERSIH, yaitu baris tanpa satu pun sel bermasalah? Sel bermasalah = sel kosong, bertanda \"-\", non-numerik, angka di luar rentang (Nilai 0–100, Kehadiran 0–100, Semester 1–8), NIM bukan tepat 8 digit angka, Email tidak valid, Tanggal_Input tidak valid, atau Prodi tidak sesuai daftar.", m["baris_bersih"]),
    ]
    out = []
    for i, (text, ans) in enumerate(items, start=1):
        out.append(dict(category="Simple Arithmetic", prompt=f"{i}. {P}{text}",
                        answer_type="number", correct_answer=str(ans), points=1))
    return out, m


if __name__ == "__main__":
    import json, sys
    p = sys.argv[1] if len(sys.argv) > 1 else "data/student_dataset.csv"
    print(json.dumps(audit(p), indent=2, ensure_ascii=False))
