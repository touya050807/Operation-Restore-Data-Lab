# Database Validation — definisi & kunci (UNTUK PANITIA, rahasia)

File: `data/student_dataset.csv` — **150 baris data**, 11 kolom: ID_Data, NIM, Nama, Email, Prodi, Semester, Nilai_Tugas, Nilai_UTS, Nilai_UAS, Kehadiran, Tanggal_Input.

Semua angka di bawah dihitung otomatis oleh `services/dataset_audit.py` dari CSV tersebut. Jika CSV diubah: jalankan ulang `python seed.py` (atau restart aplikasi pada database baru) agar kunci mengikuti.

## Definisi

```
Audit kualitas data untuk Mission 3 — Database Validation.

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
  * Email tidak valid  : email TIDAK kosong dan tidak cocok pola  ^[^@\s]+@[^@\s]+\.[^@\s]+$
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
```

## Pertanyaan dan kunci

| No | Pertanyaan | Kunci |
|---|---|---|
| 1 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris data dalam dataset (tidak termasuk baris header)? | **150** |
| 2 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah seluruh sel kosong di semua kolom dan semua baris? Definisi: sel kosong = tidak berisi karakter apa pun; tanda "-", "N/A" atau teks lain BUKAN sel kosong. | **30** |
| 3 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris dengan NIM kosong? | **6** |
| 4 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris dengan NIM tidak lengkap? Definisi: NIM valid tepat 8 digit angka; NIM tidak lengkap = tidak kosong, hanya berisi angka, dan kurang dari 8 digit. | **6** |
| 5 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris dengan NIM berformat tidak valid? Definisi: NIM tidak kosong dan mengandung setidaknya satu karakter selain angka. | **5** |
| 6 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris dengan Email kosong? | **8** |
| 7 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris dengan Email tidak kosong tetapi tidak mengandung karakter @? | **8** |
| 8 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris dengan Email tidak valid? Definisi: email tidak kosong dan tidak cocok pola teks@domain.akhiran (satu @, ada teks sebelum dan sesudahnya, domain memuat titik). Kategori ini sudah mencakup email tanpa @; email kosong tidak dihitung. | **12** |
| 9 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris yang kolom Nilai_UTS-nya berisi tanda "-" (tepat satu karakter minus)? Sel kosong tidak dihitung. | **6** |
| 10 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah SEL pada kolom Nilai_Tugas, Nilai_UTS, dan Nilai_UAS yang non-numerik? Definisi: sel tidak kosong, bukan "-", dan tidak dapat dibaca sebagai bilangan (contoh: teks, "N/A", "80a"). | **5** |
| 11 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah SEL pada kolom Nilai_Tugas, Nilai_UTS, dan Nilai_UAS yang berupa angka tetapi di luar rentang 0 sampai 100 (kurang dari 0 atau lebih dari 100)? | **6** |
| 12 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris dengan Kehadiran berupa angka di luar rentang 0 sampai 100? Sel kosong tidak dihitung. | **5** |
| 13 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris dengan Semester berupa angka di luar rentang 1 sampai 8? Sel kosong tidak dihitung. | **6** |
| 14 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris dengan Tanggal_Input tidak valid? Definisi: sel tidak kosong dan bukan tanggal kalender nyata berformat YYYY-MM-DD (contoh tidak valid: 2025-02-30, 2025-13-05, 31-12-2025). | **5** |
| 15 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris dengan Prodi tidak sesuai daftar? Daftar valid: Sains Data, Teknologi Informasi, Sistem Informasi, Teknik Industri (huruf dan ejaan harus sama persis). Sel kosong tidak dihitung. | **5** |
| 16 | Gunakan dataset student_dataset.csv (baris data = semua baris selain header). Berapa jumlah baris BERSIH, yaitu baris tanpa satu pun sel bermasalah? Sel bermasalah = sel kosong, bertanda "-", non-numerik, angka di luar rentang (Nilai 0–100, Kehadiran 0–100, Semester 1–8), NIM bukan tepat 8 digit angka, Email tidak valid, Tanggal_Input tidak valid, atau Prodi tidak sesuai daftar. | **77** |

Catatan: kunci ke-9 hanya menghitung baris dengan Nilai_UTS = "-"; total tanda "-" pada ketiga kolom nilai = 9 (tidak ditanyakan).
