"""Menulis data/DATASET_DEFINISI.md dari CSV + hasil audit (dokumen untuk panitia; JANGAN dibagikan ke peserta
karena memuat jawaban). Jalankan ulang setiap CSV berubah: python tools/write_dataset_doc.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.dataset_audit import build_questions, __doc__ as DEFS

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csvp = os.path.join(BASE, "data", "student_dataset.csv")
qs, m = build_questions(csvp)
lines = ["# Database Validation — definisi & kunci (UNTUK PANITIA, rahasia)", "",
         f"File: `data/student_dataset.csv` — **{m['baris']} baris data**, {len(m['kolom'])} kolom: {', '.join(m['kolom'])}.", "",
         "Semua angka di bawah dihitung otomatis oleh `services/dataset_audit.py` dari CSV tersebut. "
         "Jika CSV diubah: jalankan ulang `python seed.py` (atau restart aplikasi pada database baru) agar kunci mengikuti.", "",
         "## Definisi", "", "```", DEFS.strip(), "```", "", "## Pertanyaan dan kunci", "",
         "| No | Pertanyaan | Kunci |", "|---|---|---|"]
for i, q in enumerate(qs, 1):
    lines.append(f"| {i} | {q['prompt'].split('. ', 1)[1].replace('|', '/')} | **{q['correct_answer']}** |")
lines += ["", "Catatan: kunci ke-9 hanya menghitung baris dengan Nilai_UTS = \"-\"; total tanda \"-\" pada ketiga kolom nilai = "
          f"{m['nilai_strip']} (tidak ditanyakan).", ""]
open(os.path.join(BASE, "data", "DATASET_DEFINISI.md"), "w", encoding="utf-8").write("\n".join(lines))
print("ok")
