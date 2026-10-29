# ============================================================================
#  services/final_service.py — Final Code Station (Website 1).
#  Dislok memasukkan Mission Code 1-5 (urutan bebas). Bila kelimanya cocok dengan
#  Mission Code global -> tampilkan SATU Final Code global. Tidak ada kode per
#  kelompok. Final Mission (jawaban, presentasi, PPTX) ada di Website 3.
# ============================================================================
from services.mission_service import get_active_missions
from services.activity_log import log_activity
from services.codes import get_code, get_final_code, norm


def verify_final_station(codes):
    codes = [norm(c) for c in codes if c and str(c).strip()]
    expected = [get_code(m["mission_key"]) for m in get_active_missions()]

    if len(codes) != len(expected):
        log_activity("final_verify_failed", detail="jumlah kode tidak lengkap")
        return {"success": False, "reason": "incomplete"}
    if any(c not in expected for c in codes):
        log_activity("final_verify_failed", detail="ada kode tidak dikenal")
        return {"success": False, "reason": "invalid_code"}
    if sorted(codes) != sorted(expected):
        log_activity("final_verify_failed", detail="duplikat / ada misi yang belum tercakup")
        return {"success": False, "reason": "missing_mission"}

    log_activity("final_code_shown", detail="5 Mission Code valid -> Final Code global ditampilkan")
    return {"success": True, "final_code": get_final_code()}
