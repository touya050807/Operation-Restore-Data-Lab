# Website 1 — Main Website (Operation: Restore Data Lab)
Flask + SQLite. Menangani **Mission 1, 2, 3, 4 (Algorithm Engine)**, Dashboard Panitia/Admin, **Final Code Station**, dan konfigurasi tautan ke Website 2/3.
Mission 5 (Knowledge Core) dikerjakan di **Website 2** — bank soalnya sengaja tidak ada di sini agar website ini tetap ringan.

**Windows PowerShell** (jalankan satu per satu; `&&` dan `VAR=nilai perintah` TIDAK dikenal PowerShell):
```powershell
pip install -r requirements.txt
$env:WEBSITE2_URL = "http://127.0.0.1:5002"
$env:WEBSITE3_URL = "http://127.0.0.1:5003"
$env:MISSION5_CODE = "KC-AXIS"
$env:FINAL_CODE = "RESTORE-AXIS-2026"
python -m flask --app app run --port 5000
```
**macOS / Linux (bash)**:
```bash
pip install -r requirements.txt
export WEBSITE2_URL="http://127.0.0.1:5002"
export WEBSITE3_URL="http://127.0.0.1:5003"
export MISSION5_CODE="KC-AXIS"
export FINAL_CODE="RESTORE-AXIS-2026"
python -m flask --app app run --port 5000
```
Variabel `$env:` / `export` hanya berlaku di jendela terminal yang sama. Bila `pip` tidak dikenali: `python -m pip install -r requirements.txt`.

(Port 5000 adalah bawaan Flask; URL W2/W3 untuk uji lokal memakai `http://`.) Database dibuat & di-seed otomatis saat kosong; database lama otomatis diselaraskan (urutan misi, mode station, 5 algoritma sehari-hari; kolom timer lama dibuang). Tidak ada timer/cooldown/batas waktu di mana pun.

Akun awal (GANTI lewat env `ADMIN_PASSWORD` / `PANITIA_PASSWORD`): `admin / axis2026`, `panitia / panitia2026`.
Password station: Python `python123`, Database `database123`, Final `final123` (ubah di Admin → Missions).
Kelompok dibaca dari `data/groups.json`. Lihat `../README_DEPLOY.md`.
