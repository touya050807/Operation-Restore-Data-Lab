"""Membuat data/student_dataset.csv (dataset Mission 3 — Database Validation).

Deterministik (seed tetap): menjalankan ulang menghasilkan CSV yang sama persis.
Skrip ini HANYA membuat data (bersih + masalah yang disuntikkan). Jawaban soal TIDAK ditulis di sini;
jawaban dihitung dari CSV hasilnya oleh services/dataset_audit.py.
Jika CSV diubah/dibuat ulang, jalankan ulang seed (python seed.py) atau hapus soal Database lama
supaya kunci jawaban mengikuti CSV.
"""
import csv
import os
import random

N_ROWS = 150
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "student_dataset.csv")

FIRST = ["Adit", "Alya", "Bagas", "Bunga", "Citra", "Dimas", "Dewi", "Eko", "Fajar", "Gita", "Hana", "Indra",
         "Intan", "Joko", "Kirana", "Laras", "Maya", "Nadia", "Oka", "Putri", "Rangga", "Sinta", "Tegar",
         "Umar", "Vina", "Wahyu", "Yudi", "Zahra", "Rizki", "Salsa"]
LAST = ["Pratama", "Saputra", "Wijaya", "Lestari", "Hidayat", "Nugraha", "Putri", "Kusuma", "Ramadhan",
        "Santoso", "Maharani", "Firmansyah", "Permata", "Wibowo", "Anggraini", "Setiawan", "Utami", "Hakim"]
PRODI = ["Sains Data", "Teknologi Informasi", "Sistem Informasi", "Teknik Industri"]
HEADER = ["ID_Data", "NIM", "Nama", "Email", "Prodi", "Semester", "Nilai_Tugas", "Nilai_UTS", "Nilai_UAS",
          "Kehadiran", "Tanggal_Input"]


def make_clean(rnd):
    rows, used = [], set()
    for i in range(1, N_ROWS + 1):
        while True:
            nm = f"{rnd.choice(FIRST)} {rnd.choice(LAST)}"
            if nm not in used:
                used.add(nm)
                break
        email = nm.lower().replace(" ", ".") + "@student.itsb.ac.id"
        rows.append({
            "ID_Data": f"D{i:03d}", "NIM": str(23100000 + i), "Nama": nm, "Email": email,
            "Prodi": rnd.choice(PRODI), "Semester": str(rnd.randint(1, 8)),
            "Nilai_Tugas": str(rnd.randint(55, 100)), "Nilai_UTS": str(rnd.randint(50, 100)),
            "Nilai_UAS": str(rnd.randint(50, 100)), "Kehadiran": str(rnd.randint(60, 100)),
            "Tanggal_Input": f"2025-{rnd.randint(1, 12):02d}-{rnd.randint(1, 28):02d}",
        })
    return rows


def inject(rows, rnd):
    idx = list(range(N_ROWS))

    def pick(k):
        return rnd.sample(idx, k)

    for i in pick(6):  rows[i]["NIM"] = ""                                   # NIM kosong
    for i in pick(7):  rows[i]["NIM"] = rows[i]["NIM"][:rnd.randint(5, 7)]    # NIM tidak lengkap (hanya angka, < 8 digit)
    for i in pick(5):  rows[i]["NIM"] = rows[i]["NIM"][:4] + rnd.choice("ABXO") + rows[i]["NIM"][5:]  # NIM berisi huruf
    for i in pick(8):  rows[i]["Email"] = ""                                 # email kosong
    for i in pick(9):  rows[i]["Email"] = rows[i]["Email"].replace("@", "")   # email tanpa @
    for i in pick(4):  rows[i]["Email"] = rows[i]["Nama"].split()[0].lower() + "@"   # ada @ tapi pola salah
    for i in pick(6):  rows[i]["Nilai_UTS"] = "-"                            # tanda "-"
    for i in pick(3):  rows[i]["Nilai_UAS"] = "-"
    for i in pick(4):  rows[i]["Nilai_Tugas"] = ""                           # nilai kosong
    for i in pick(3):  rows[i]["Nilai_UTS"] = ""
    for i in pick(5):  rows[i][rnd.choice(["Nilai_Tugas", "Nilai_UTS", "Nilai_UAS"])] = rnd.choice(["tujuh puluh", "abc", "N/A", "80a"])
    for i in pick(6):  rows[i][rnd.choice(["Nilai_Tugas", "Nilai_UTS", "Nilai_UAS"])] = rnd.choice(["105", "120", "-5", "150", "101"])
    for i in pick(5):  rows[i]["Kehadiran"] = rnd.choice(["110", "-10", "150", "101"])
    for i in pick(2):  rows[i]["Kehadiran"] = ""
    for i in pick(5):  rows[i]["Tanggal_Input"] = rnd.choice(["2025-02-30", "2025-13-05", "31-12-2025", "2025/04/10", "2025-00-12"])
    for i in pick(2):  rows[i]["Tanggal_Input"] = ""
    for i in pick(6):  rows[i]["Semester"] = rnd.choice(["0", "9", "10", "12"])
    for i in pick(3):  rows[i]["Semester"] = ""
    for i in pick(5):  rows[i]["Prodi"] = rnd.choice(["Sains Dta", "Kedokteran", "Informatika", "-"])
    for i in pick(2):  rows[i]["Prodi"] = ""
    return rows


def main():
    rnd = random.Random(20260926)
    rows = inject(make_clean(rnd), rnd)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    print(f"Tulis {len(rows)} baris -> {OUT}")


if __name__ == "__main__":
    main()
