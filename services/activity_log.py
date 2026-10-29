# ============================================================================
#  services/activity_log.py
#  Pencatatan Activity Log — dipanggil dari route participant & admin.
# ============================================================================

from db_layer.db import execute


def log_activity(action, group_id=None, mission_id=None, admin_id=None, detail=""):
    execute(
        "INSERT INTO activity_logs (group_id, mission_id, admin_id, action, detail) VALUES (?, ?, ?, ?, ?)",
        (group_id, mission_id, admin_id, action, detail),
    )
