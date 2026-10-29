"""Bank soal Mission 1 — Python Runtime (materi Python DASAR).

Cakupan (ringkasan panitia): variabel & tipe data (str/int/float/bool), print/input, operator (+ - * / %), kondisi (if/elif/else),
komentar (#), list/tuple/dictionary, perulangan (for/range/while, i += 1), fungsi (def/return), mini project status nilai.
TIDAK dipakai: class, decorator, lambda, exception handling, library eksternal, file I/O, API, database.

FORMAT SOAL (v7): setiap kode ada di blok berpagar ```python ... ``` di dalam prompt, TANPA nomor baris dan TANPA teks lain di
dalam blok, sehingga peserta dapat menyalinnya utuh ke Google Colab dan langsung menjalankannya. Tampilan peserta menyajikan blok itu
dengan tombol "Salin kode". Kode di prompt adalah SATU-SATUNYA sumber: tests/test_w1_bank.py mengekstrak kode dari prompt itu sendiri,
menjalankannya (python -I, stdin sesuai soal) dan membandingkan keluaran/error dengan kunci.

Jenis verifikasi (`verify`):
  run        : jalankan blok kode; keluaran (spasi dirapikan) == kunci
  fixed_run  : blok kode HARUS error (exc) seperti di soal; versi perbaikan (`replace` lama->baru) harus keluar == kunci
  raises_at  : blok kode menimbulkan `exc`; jumlah baris yang sempat tercetak == kunci (indeks pertama yang gagal)
  raises     : blok kode menimbulkan exception bertipe `exc` (kunci = jawaban benar/salah soal)
  syntax_line: blok kode SyntaxError pada baris == kunci
  eval       : ekspresi == nilai
  multi      : beberapa potongan kode, tiap potongan error `exc` (atau valid bila None)
Kunci tidak dihitung saat aplikasi berjalan (tidak ada eksekusi kode peserta).
Pencocokan jawaban isian Python memakai match_mode "space": spasi dirapikan TETAPI huruf besar/kecil dibedakan (keluaran program peka huruf).
"""
import json

TOPICS = ["Variabel dan Tipe Data", "Input dan Output", "Operator", "Kondisi", "Komentar",
          "Struktur Data", "Perulangan", "Fungsi", "Mini Project"]

RUN_INTRO = "Perhatikan kode berikut (dapat disalin dan dijalankan langsung di Google Colab):"


def _prompt(intro, code, ask):
    parts = [intro]
    if code is not None:
        parts.append("```python\n" + code.rstrip("\n") + "\n```")
    parts.append(ask)
    return "\n\n".join(parts)


def _mk(cat, atype, intro, code, ask, key, points, verify, prev, options=None):
    d = dict(category=cat, prompt=_prompt(intro, code, ask), answer_type=atype, correct_answer=key, points=points, verify=verify, code=code, prev_prompt=prev)
    if atype == "text":
        d["match_mode"] = "space"
    if options is not None:
        d["options_json"] = json.dumps(options, ensure_ascii=False)
    return d

PREV = [
 "Kode berikut error, perbaiki lalu jalankan di Colab:\n\ndata = [10, 20, 30]\nfor i in range(len(data) + 1):\n    print(data[i])\n\nApa output SETELAH diperbaiki? (pisahkan dengan spasi)",
 "total = 0\nfor i in range(1, 5):\n    total += i\nprint(total)\n\nApa output program ini?",
 "Kode awal (sebelum diperbaiki):\n\ndata = [10, 20, 30]\nfor i in range(len(data) + 1):\n    print(data[i])\n\nPada nilai i berapa program PERTAMA KALI menimbulkan IndexError? (jawab dengan angka)",
 "Perhatikan: `harga = 3.0`\nTipe data apa yang disimpan variabel harga?",
 "nama = \"Sari\"\numur = 19\nprint(nama, umur + 1)\n\nTuliskan output program ini persis seperti yang tercetak.",
 "Manakah baris Python berikut yang VALID untuk menampilkan tulisan Halo di layar?",
 "nama = input(\"Nama: \")\nprint(\"Halo\", nama)\n\nPengguna mengetik Budi lalu menekan Enter. Tuliskan hanya baris yang dicetak oleh print() (bukan tulisan \"Nama: \").",
 "a = 17\nb = 5\nprint(a % b)\n\nApa output program ini? (jawab dengan angka)",
 "x = 10\nx = x + 5\nx = x - 3\nx = x * 2\nprint(x)\n\nApa output program ini? (jawab dengan angka)",
 "nilai = 72\nif nilai >= 85:\n    print(\"A\")\nelif nilai >= 70:\n    print(\"B\")\nelse:\n    print(\"C\")\n\nApa output program ini? (satu huruf)",
 "Program ini ingin menentukan genap/ganjil tetapi error:\n\nn = 9\nif n % 2 = 0:\n    print(\"genap\")\nelse:\n    print(\"ganjil\")\n\nApa penyebab error-nya?",
 "# print(\"A\")\nprint(\"B\")  # print(\"C\")\nprint(\"D\")\n\nTuliskan output program ini (pisahkan setiap baris keluaran dengan spasi).",
 "buah = [\"apel\", \"jeruk\", \"mangga\"]\nbuah.append(\"pisang\")\nbuah[1] = \"melon\"\nprint(buah[1], buah[3])\n\nTuliskan output program ini persis seperti yang tercetak.",
 "Benar atau Salah: Pada tuple t = (1, 2, 3), perintah t[0] = 9 berhasil mengubah isi tuple.",
 "mhs = {\"nama\": \"Ani\", \"nilai\": 80}\nmhs[\"nilai\"] = 90\nmhs[\"kelas\"] = \"A\"\nprint(mhs[\"nilai\"], mhs[\"kelas\"])\n\nTuliskan output program ini persis seperti yang tercetak.",
 "i = 1\nhasil = 0\nwhile i <= 4:\n    hasil += i * 2\n    i += 1\nprint(hasil)\n\nApa output program ini? (jawab dengan angka)",
 "def kali(a, b):\n    return a * b\n\nprint(kali(3, 4) + 1)\n\nApa output program ini? (jawab dengan angka)",
 "Program status nilai mahasiswa berikut error:\n\n1  nilai = int(input(\"Nilai: \"))\n2  if nilai >= 60:\n3      print(\"Lulus\")\n4  else\n5      print(\"Tidak lulus\")\n\nPada nomor baris berapa kesalahan sintaksnya? (jawab dengan angka)"
]
  # prompt versi v6 (sebelum format blok kode): dipakai migrasi untuk MEMPERBARUI teks soal yang sama (id & riwayat tetap)


def items():
    I = []
    P = PREV

    # ---- soal LAMA (3): dipertahankan; teks dirapikan (kode di blok berpagar) agar bisa disalin ke Colab; id & riwayat tetap ----
    c1 = "data = [10, 20, 30]\nfor i in range(len(data) + 1):\n    print(data[i])"
    I.append(_mk("Perulangan", "text", "Kode berikut error, perbaiki lalu jalankan di Colab:", c1,
                 "Salin kode ke sel Google Colab, perbaiki bagian yang menyebabkan error, lalu jalankan.\nApa output SETELAH diperbaiki? (pisahkan dengan spasi)",
                 "10 20 30", 1, dict(kind="fixed_run", exc="IndexError", replace=["len(data) + 1", "len(data)"]), P[0]))
    c2 = "total = 0\nfor i in range(1, 5):\n    total += i\nprint(total)"
    I.append(_mk("Perulangan", "number", RUN_INTRO, c2, "Apa output program ini? (jawab dengan angka)", "10", 1, dict(kind="run"), P[1]))
    I.append(_mk("Struktur Data", "number", "Kode awal (sebelum diperbaiki):", c1,
                 "Pada nilai i berapa program PERTAMA KALI menimbulkan IndexError? (jawab dengan angka)", "3", 2,
                 dict(kind="raises_at", exc="IndexError"), P[2]))
    # ---- soal BARU ----
    I.append(_mk("Variabel dan Tipe Data", "multiple_choice", RUN_INTRO, "harga = 3.0\nprint(type(harga))",
                 "Tipe data apa yang disimpan variabel harga?", "float", 1, dict(kind="run_contains", contains="<class 'float'>"), P[3],
                 options=["int", "float", "str", "bool"]))
    I.append(_mk("Variabel dan Tipe Data", "text", RUN_INTRO, 'nama = "Sari"\numur = 19\nprint(nama, umur + 1)',
                 "Tuliskan output program ini persis seperti yang tercetak.", "Sari 20", 1, dict(kind="run"), P[4]))
    I.append(_mk("Input dan Output", "multiple_choice",
                 "Manakah baris Python berikut yang VALID (tidak error) untuk menampilkan tulisan Halo di Google Colab?", None,
                 "Pilih satu baris.", 'print("Halo")', 1,
                 dict(kind="multi", cases=[dict(code='print("Halo)', exc="SyntaxError"), dict(code='print("Halo")', exc=None),
                                          dict(code='Print("Halo")', exc="NameError"), dict(code='print "Halo"', exc="SyntaxError")]), P[5],
                 options=['print("Halo)', 'print("Halo")', 'Print("Halo")', 'print "Halo"']))
    I.append(_mk("Input dan Output", "text", RUN_INTRO, 'nama = input("Nama: ")\nprint("Halo", nama)',
                 'Saat dijalankan di Colab, pengguna mengetik Budi lalu menekan Enter. Tuliskan hanya baris yang dicetak oleh print() (bukan tulisan "Nama: ").',
                 "Halo Budi", 1, dict(kind="run", stdin="Budi\n", strip_prompt="Nama: "), P[6]))
    I.append(_mk("Operator", "number", RUN_INTRO, "a = 17\nb = 5\nprint(a % b)", "Apa output program ini? (jawab dengan angka)", "2", 1, dict(kind="run"), P[7]))
    I.append(_mk("Operator", "number", RUN_INTRO, "x = 10\nx = x + 5\nx = x - 3\nx = x * 2\nprint(x)", "Apa output program ini? (jawab dengan angka)", "24", 2, dict(kind="run"), P[8]))
    I.append(_mk("Kondisi", "text", RUN_INTRO, 'nilai = 72\nif nilai >= 85:\n    print("A")\nelif nilai >= 70:\n    print("B")\nelse:\n    print("C")',
                 "Apa output program ini? (satu huruf kapital)", "B", 1, dict(kind="run"), P[9]))
    I.append(_mk("Kondisi", "multiple_choice", "Program berikut ingin menentukan genap/ganjil tetapi menampilkan error saat dijalankan di Google Colab:",
                 'n = 9\nif n % 2 = 0:\n    print("genap")\nelse:\n    print("ganjil")', "Apa penyebab error-nya?",
                 "Operator perbandingan harus == (bukan =)", 1,
                 dict(kind="multi", cases=[dict(code='n = 9\nif n % 2 = 0:\n    print("genap")\nelse:\n    print("ganjil")', exc="SyntaxError"),
                                          dict(code='n = 9\nif n % 2 == 0:\n    print("genap")\nelse:\n    print("ganjil")', exc=None)]), P[10],
                 options=["Operator perbandingan harus == (bukan =)", "Variabel n tidak boleh bernilai 9", "Kata else harus ditulis Else", "print() tidak boleh di dalam if"]))
    I.append(_mk("Komentar", "text", RUN_INTRO, '# print("A")\nprint("B")  # print("C")\nprint("D")',
                 "Tuliskan output program ini (pisahkan setiap baris keluaran dengan spasi).", "B D", 1, dict(kind="run"), P[11]))
    I.append(_mk("Struktur Data", "text", RUN_INTRO, 'buah = ["apel", "jeruk", "mangga"]\nbuah.append("pisang")\nbuah[1] = "melon"\nprint(buah[1], buah[3])',
                 "Tuliskan output program ini persis seperti yang tercetak.", "melon pisang", 2, dict(kind="run"), P[12]))
    I.append(_mk("Struktur Data", "true_false", "Perhatikan kode berikut (dapat disalin dan dijalankan di Google Colab):", "t = (1, 2, 3)\nt[0] = 9\nprint(t)",
                 "Benar atau Salah: Kode tersebut berhasil mengubah isi tuple dan mencetak (9, 2, 3).", "false", 1, dict(kind="raises", exc="TypeError"), P[13]))
    I.append(_mk("Struktur Data", "text", RUN_INTRO, 'mhs = {"nama": "Ani", "nilai": 80}\nmhs["nilai"] = 90\nmhs["kelas"] = "A"\nprint(mhs["nilai"], mhs["kelas"])',
                 "Tuliskan output program ini persis seperti yang tercetak.", "90 A", 2, dict(kind="run"), P[14]))
    I.append(_mk("Perulangan", "number", RUN_INTRO, "i = 1\nhasil = 0\nwhile i <= 4:\n    hasil += i * 2\n    i += 1\nprint(hasil)",
                 "Apa output program ini? (jawab dengan angka)", "20", 2, dict(kind="run"), P[15]))
    I.append(_mk("Fungsi", "number", RUN_INTRO, "def kali(a, b):\n    return a * b\n\nprint(kali(3, 4) + 1)", "Apa output program ini? (jawab dengan angka)", "13", 1, dict(kind="run"), P[16]))
    I.append(_mk("Mini Project", "number", "Program status nilai mahasiswa berikut menampilkan SyntaxError saat dijalankan di Google Colab:",
                 'nilai = int(input("Nilai: "))\nif nilai >= 60:\n    print("Lulus")\nelse\n    print("Tidak lulus")',
                 "Pada baris ke berapa Python melaporkan kesalahan sintaksnya? (baris pertama kode = baris 1; jawab dengan angka)", "4", 2,
                 dict(kind="syntax_line"), P[17]))
    return I


def questions():
    """Bentuk untuk seeding (tanpa kunci verifikasi)."""
    return [{k: v for k, v in q.items() if k not in ("verify", "code", "prev_prompt")} for q in items()]
