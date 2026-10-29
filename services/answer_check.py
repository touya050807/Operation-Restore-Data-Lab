# ============================================================================
#  services/answer_check.py
#  Pengecekan jawaban di BACKEND (bukan hanya frontend) untuk seluruh tipe
#  soal: text, number, essay, true_false, multiple_choice, multiple_select,
#  ordering, matching.
# ============================================================================

import json


def _norm_space(s):
    return " ".join(str(s).split())


def _norm_lower(s):
    return _norm_space(s).strip().lower()


def _same(a, b):
    """Perbandingan untuk nilai yang dipilih dari daftar opsi (pilihan ganda/ceklis/urutan/pasangan): PERSIS (hanya tepi dipangkas).
    Huruf besar/kecil dan spasi dalam opsi adalah bagian dari isi opsi (mis. print("Halo") vs Print("Halo") adalah opsi berbeda);
    peserta tidak mengetik nilai ini, browser mengirim kembali nilai opsi dari server sehingga tidak perlu toleransi."""
    return str(a).strip() == str(b).strip()


def is_blank(question, value):
    """True bila jawaban belum lengkap (kosong). Jawaban kosong/setengah terisi BUKAN jawaban salah:
    ia tidak dinilai dan tidak dicatat sebagai percobaan."""
    t = question["answer_type"]
    if value is None:
        return True
    if t in ("multiple_select", "ordering"):
        return not isinstance(value, list) or len(value) == 0
    if t == "matching":
        return (not isinstance(value, dict) or len(value) == 0
                or any(str(v).strip() == "" for v in value.values()))
    return str(value).strip() == ""


def check_answer(question, submitted_value):
    """question: dict (row dari tabel questions). submitted_value: jawaban
    dari peserta — bentuknya tergantung tipe soal (string untuk text/number/
    multiple_choice/true_false, list untuk multiple_select/ordering, dict
    untuk matching)."""
    qtype = question["answer_type"]
    correct = question.get("correct_answer", "") or ""

    if qtype == "essay":
        # Essay dinilai otomatis SELESAI begitu diisi dengan layak (tidak ada
        # jawaban baku) — panitia dapat menilai isinya lewat Activity Log /
        # Bank Soal jika diperlukan, tapi progress tidak menahan peserta.
        return len(str(submitted_value or "").strip()) >= 5

    if qtype == "number":
        try:
            return abs(float(str(submitted_value).strip()) - float(correct.strip())) < 1e-6
        except (ValueError, AttributeError, TypeError):
            return False

    if qtype == "multiple_choice":
        return _same(submitted_value or "", correct)

    if qtype == "true_false":
        truthy = {"true", "benar", "ya", "1", "yes"}
        falsy = {"false", "salah", "tidak", "0", "no"}
        sub_norm = str(submitted_value or "").strip().lower()
        sub_bool = "true" if sub_norm in truthy else ("false" if sub_norm in falsy else None)
        return sub_bool is not None and sub_bool == correct.strip().lower()

    if qtype == "multiple_select":
        try:
            correct_set = {str(x).strip() for x in json.loads(correct)}
        except (ValueError, TypeError):
            correct_set = set()
        submitted_list = submitted_value if isinstance(submitted_value, list) else []
        submitted_set = {str(x).strip() for x in submitted_list}
        return len(correct_set) > 0 and submitted_set == correct_set

    if qtype == "ordering":
        try:
            correct_list = [str(x).strip() for x in json.loads(correct)]
        except (ValueError, TypeError):
            correct_list = []
        submitted_list = submitted_value if isinstance(submitted_value, list) else []
        submitted_norm = [str(x).strip() for x in submitted_list]
        return len(correct_list) > 0 and submitted_norm == correct_list

    if qtype == "matching":
        try:
            correct_map = {str(k).strip(): str(v).strip() for k, v in json.loads(correct).items()}
        except (ValueError, TypeError, AttributeError):
            correct_map = {}
        submitted_map = submitted_value if isinstance(submitted_value, dict) else {}
        submitted_norm = {str(k).strip(): str(v).strip() for k, v in submitted_map.items()}
        return len(correct_map) > 0 and submitted_norm == correct_map

    # default: text
    match_mode = question.get("match_mode", "case_insensitive")
    submitted = "" if submitted_value is None else str(submitted_value)
    if match_mode == "exact":
        return submitted == correct
    if match_mode == "trim":
        return submitted.strip() == correct.strip()
    if match_mode == "space":          # spasi/baris baru dirapikan, HURUF BESAR/KECIL DIBEDAKAN (keluaran program Python peka huruf)
        return _norm_space(submitted) == _norm_space(correct)
    # case_insensitive (default) — juga merapikan spasi ganda supaya jawaban
    # berbentuk daftar/urutan (mis. "a, b, c") tetap toleran terhadap spasi.
    return _norm_lower(submitted) == _norm_lower(correct)
