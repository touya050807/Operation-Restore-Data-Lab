"""Bank soal Mission 2 — Problem Analysis Center: logika & penalaran dengan jawaban PASTI.

Setiap kunci yang bisa dihitung dihasilkan oleh kode di bawah (bukan diketik dari dugaan), dan
tests/test_w1.py memverifikasi ulang secara terpisah. Soal bersifat objektif: premis lengkap,
satu jawaban benar, tanpa pendapat pribadi.

Struktur v6: TEPAT 20 soal aktif = 5 topik x 4 soal (kolom `category` = nama topik):
Decomposition, Pattern Recognition, Abstraction, Algorithm Design, Logical Reasoning.
Antarmuka peserta tetap satu daftar soal (topik hanya tampil sebagai label kecil di kartu).
"""
import json

TOPICS = ["Decomposition", "Pattern Recognition", "Abstraction", "Algorithm Design", "Logical Reasoning"]


def _series_double_plus_one():
    seq = [3]
    for _ in range(5):
        seq.append(seq[-1] * 2 + 1)
    return seq[:5], seq[5]              # tampil 5 suku, kunci = suku ke-6


def _series_n_times_n_plus_1():
    seq = [n * (n + 1) for n in range(1, 7)]
    return seq[:5], seq[5]


def _is_prime(n):
    return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))


def questions():
    s1, a1 = _series_double_plus_one()
    s2, a2 = _series_n_times_n_plus_1()

    machines, rate, total = 3, 45, 1350
    a_time = total // (machines * rate)
    assert total % (machines * rate) == 0

    total_txt = f"{total:,}".replace(",", ".")
    scores = [72, 85, 90, 69]
    assert sum(scores) % len(scores) == 0
    a_avg = sum(scores) // len(scores)

    frac = {"0,75": 0.75, "5/6": 5 / 6, "7/8": 7 / 8, "0,8": 0.8}
    shown_order = ["7/8", "0,75", "5/6", "0,8"]
    key_order = sorted(frac, key=frac.get)
    assert len(set(frac.values())) == 4

    nums = [17, 21, 29, 33]
    prime_map = {str(n): ("Prima" if _is_prime(n) else "Bukan prima") for n in nums}

    opts = [12, 18, 20, 27, 30]
    ms_key = [str(n) for n in opts if n % 2 == 0 and n % 3 == 0]

    def caesar(word, k):
        return "".join(chr((ord(c) - 65 + k) % 26 + 65) for c in word)
    a_cipher = caesar("DATA", 2)

    base = [
        dict(category="Decomposition", prompt=(
            "Laboratorium sering bentrok jadwal peminjaman. Manakah TAHAP Computational Thinking yang "
            "tepat untuk memecah masalah ini menjadi bagian-bagian kecil?"),
            answer_type="multiple_choice",
            options_json=json.dumps(["Decomposition", "Compilation", "Debugging", "Deployment"]),
            correct_answer="Decomposition", points=1),
        dict(category="Abstraction", prompt=(
            "Benar atau Salah: Abstraction berarti mengabaikan detail yang tidak penting dan fokus "
            "pada informasi yang relevan."),
            answer_type="true_false", correct_answer="true", points=1),
        dict(category="Pattern Recognition", prompt=(
            f"Deret bilangan: {', '.join(map(str, s1))}, ... Setiap suku diperoleh dari suku sebelumnya dengan aturan yang tetap. "
            "Berapa suku berikutnya? (jawab dengan angka)"),
            answer_type="number", correct_answer=str(a1), points=1),
        dict(category="Pattern Recognition", prompt=(
            f"Deret bilangan: {', '.join(map(str, s2))}, ... Berapa suku berikutnya? (jawab dengan angka)"),
            answer_type="number", correct_answer=str(a2), points=1),
        dict(category="Logical Reasoning", prompt=(
            "Premis 1: Semua server di Lab A memakai sistem operasi Linux.\n"
            "Premis 2: Sebagian server di Lab A berada di Rak 2.\n"
            "Manakah kesimpulan yang PASTI benar berdasarkan kedua premis?"),
            answer_type="multiple_choice",
            options_json=json.dumps([
                "Semua server di Rak 2 memakai Linux",
                "Sebagian server di Rak 2 memakai Linux",
                "Tidak ada server di Rak 2 yang memakai Linux",
                "Semua server Linux berada di Lab A"]),
            correct_answer="Sebagian server di Rak 2 memakai Linux", points=2),
        dict(category="Logical Reasoning", prompt=(
            "Benar atau Salah: Diberikan dua pernyataan — (1) Jika data valid, maka laporan dikirim. (2) Laporan tidak dikirim. "
            "Kesimpulan: data tidak valid. Apakah kesimpulan tersebut pasti benar?"),
            answer_type="true_false", correct_answer="true", points=1),
        dict(category="Decomposition", prompt=(
            f"Sebuah proses memerlukan {total_txt} data diproses. Tersedia {machines} mesin identik; setiap mesin memproses "
            f"{rate} data per menit secara terus-menerus, ketiganya bekerja bersamaan sejak menit pertama, dan tidak ada waktu jeda. "
            "Berapa menit yang dibutuhkan sampai seluruh data selesai? (jawab dengan angka)"),
            answer_type="number", correct_answer=str(a_time), points=2),
        dict(category="Algorithm Design", prompt=(
            "Urutkan bilangan berikut dari yang TERKECIL ke yang TERBESAR (urutan paling atas = terkecil). "
            "Tanda koma pada 0,75 dan 0,8 adalah koma desimal."),
            answer_type="ordering", options_json=json.dumps(shown_order),
            correct_answer=json.dumps(key_order), points=2),
        dict(category="Algorithm Design", prompt=(
            "Klasifikasikan setiap bilangan berikut berdasarkan aturan: bilangan prima adalah bilangan bulat lebih dari 1 "
            "yang hanya habis dibagi 1 dan dirinya sendiri. Pilih pasangan yang tepat untuk setiap bilangan."),
            answer_type="matching",
            options_json=json.dumps({"left": [str(n) for n in nums], "right": ["Prima", "Bukan prima"]}),
            correct_answer=json.dumps(prime_map), points=2),
        dict(category="Logical Reasoning", prompt=(
            "Manakah bilangan berikut yang merupakan bilangan genap DAN habis dibagi 3? (pilih semua yang benar)"),
            answer_type="multiple_select", options_json=json.dumps([str(n) for n in opts]),
            correct_answer=json.dumps(ms_key), points=2),
        dict(category="Algorithm Design", prompt=(
            "Aturan sandi: setiap huruf kapital digeser 2 huruf ke depan dalam alfabet A–Z (A menjadi C, B menjadi D, dst.; "
            "Y menjadi A, Z menjadi B). Tuliskan hasil sandi untuk kata DATA dengan huruf kapital."),
            answer_type="text", correct_answer=a_cipher, match_mode="case_insensitive", points=2),
    ]

    # ------------------------------------------------------------ soal baru v6 (kunci dihitung kode / dinyatakan eksplisit di soal)
    pages = 5 * 4 * 2                                   # 5 bab x 4 subbab x 2 halaman
    rp = lambda n: "Rp" + f"{n:,}".replace(",", ".")
    prices = {"A": 20000, "B": 35000, "C": 45000}
    price_diff = max(prices.values()) - min(prices.values())
    team = [("Ani", 72, 160), ("Budi", 85, 171), ("Cici", 90, 155), ("Dedi", 69, 168)]
    assert sum(t[1] for t in team) % len(team) == 0
    team_avg = sum(t[1] for t in team) // len(team)
    letters = [chr(ord("A") + 2 * i) for i in range(5)]
    letter_next = chr(ord("A") + 2 * 5)
    lamps = ["Merah", "Hijau", "Kuning"]
    lamp_50 = lamps[(50 - 1) % 3]
    x = 5
    for _ in range(3):
        x = x * 2 - 1
    people = {"Ani": (False, True, False), "Budi": (False, True, True), "Cici": (True, False, False), "Dedi": (False, False, True)}
    access = [n for n, (adm, mem, login) in people.items() if adm or (mem and login)]
    tasks = ["Mengumpulkan data nilai", "Menghitung rata-rata", "Menentukan grade", "Mencetak laporan"]
    extra = [
        dict(category="Decomposition", prompt=(
            "Program laporan nilai dipecah menjadi 4 sub-tugas: (a) Mengumpulkan data nilai, (b) Menghitung rata-rata, "
            "(c) Menentukan grade, (d) Mencetak laporan.\n"
            "Aturan: sub-tugas (b) memerlukan hasil (a); (c) memerlukan hasil (b); (d) memerlukan hasil (c). "
            "Sub-tugas hanya boleh dikerjakan setelah sub-tugas yang hasilnya ia perlukan selesai.\n"
            "Urutkan sub-tugas dari yang HARUS dikerjakan pertama (paling atas) sampai terakhir."),
            answer_type="ordering", options_json=json.dumps([tasks[2], tasks[0], tasks[3], tasks[1]]),
            correct_answer=json.dumps(tasks), points=2),
        dict(category="Decomposition", prompt=(
            "Sebuah laporan dipecah menjadi 5 bab. Setiap bab dipecah lagi menjadi 4 subbab, dan setiap subbab ditulis sebanyak 2 halaman. "
            "Berapa total halaman laporan tersebut? (jawab dengan angka)"),
            answer_type="number", correct_answer=str(pages), points=1),
        dict(category="Pattern Recognition", prompt=(
            f"Pola huruf: {', '.join(letters)}, ... Setiap huruf bergeser dengan jarak yang sama dalam urutan alfabet dari huruf sebelumnya. "
            "Huruf kapital apa yang berikutnya?"),
            answer_type="text", correct_answer=letter_next, match_mode="case_insensitive", points=1),
        dict(category="Pattern Recognition", prompt=(
            "Lampu lalu lintas menyala berulang dengan urutan tetap: Merah, Hijau, Kuning, lalu kembali ke Merah, dan seterusnya "
            "(nyala ke-1 = Merah, nyala ke-2 = Hijau, nyala ke-3 = Kuning, nyala ke-4 = Merah, ...). "
            "Lampu apa yang menyala pada nyala ke-50?"),
            answer_type="multiple_choice", options_json=json.dumps(lamps), correct_answer=lamp_50, points=1),
        dict(category="Abstraction", prompt=(
            "Tujuan: menghitung TOTAL HARGA belanja. Data yang tersedia untuk setiap barang: nama barang, harga satuan, jumlah dibeli, "
            "warna kemasan, nama kasir. Pilih semua data yang RELEVAN untuk tujuan tersebut."),
            answer_type="multiple_select", options_json=json.dumps(["Nama barang", "Harga satuan", "Jumlah dibeli", "Warna kemasan", "Nama kasir"]),
            correct_answer=json.dumps(["Harga satuan", "Jumlah dibeli"]), points=2),
        dict(category="Abstraction", prompt=(
            f"Sebuah toko menjual tiga buku: Buku A {rp(prices['A'])} (sampul biru), Buku B {rp(prices['B'])} (sampul merah), "
            f"Buku C {rp(prices['C'])} (sampul hijau)." +
            " Untuk menghitung selisih harga buku TERMURAH dan TERMAHAL, warna sampul tidak diperlukan. "
            "Berapa selisihnya dalam rupiah? (jawab dengan angka saja)"),
            answer_type="number", correct_answer=str(price_diff), points=1),
        dict(category="Abstraction", prompt=(
            "Data empat anggota tim (nama, nilai, tinggi badan): " + "; ".join(f"{n}, {v}, {t} cm" for n, v, t in team) + ". "
            "Tinggi badan tidak relevan untuk menghitung rata-rata nilai. Berapa rata-rata NILAI tim? (jawab dengan angka)"),
            answer_type="number", correct_answer=str(team_avg), points=1),
        dict(category="Algorithm Design", prompt=(
            "Pseudocode:\n\nx <- 5\nulangi 3 kali:\n    x <- x * 2 - 1\ntampilkan x\n\n"
            "Berapa nilai yang ditampilkan? (jawab dengan angka)"),
            answer_type="number", correct_answer=str(x), points=2),
        dict(category="Logical Reasoning", prompt=(
            "Aturan akses: seseorang mendapat akses jika dia ADMIN, ATAU dia ANGGOTA dan sudah LOGIN.\n"
            "Ani: anggota, belum login. Budi: anggota, sudah login. Cici: admin, belum login. Dedi: bukan anggota dan bukan admin, sudah login.\n"
            "Siapa saja yang mendapat akses? (pilih semua yang benar)"),
            answer_type="multiple_select", options_json=json.dumps(list(people)), correct_answer=json.dumps(access), points=2),
    ]
    out = base + extra
    order = {t: i for i, t in enumerate(TOPICS)}
    out.sort(key=lambda q: order[q["category"]])          # stabil: urutan relatif soal lama dipertahankan
    return out
