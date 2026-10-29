# ============================================================================
#  auth.py
#  - Autentikasi PANITIA: login berbasis session, password di-hash
#    (werkzeug.security), decorator @admin_required untuk melindungi route
#    dashboard & seluruh endpoint admin.
#  - Sesi PESERTA: TANPA login/password — hanya identifikasi kelompok yang
#    disimpan di session Flask (bukan cookie permanen lintas device, hanya
#    supaya peserta tidak perlu memilih ulang kelompok tiap pindah halaman).
#    Decorator @group_required memastikan peserta sudah memilih kelompok
#    sebelum mengakses dashboard/mission, dan mengisolasi data antar kelompok
#    (peserta hanya bisa melihat/mengubah progress kelompok yang mereka pilih).
# ============================================================================

from functools import wraps
from flask import session, redirect, url_for, g, jsonify, render_template, request
from werkzeug.security import check_password_hash

from db_layer.db import query_one


# ---------------------------------------------------------------------------
# ADMIN
# ---------------------------------------------------------------------------

def verify_admin_login(username, password):
    admin = query_one("SELECT * FROM admins WHERE username = ?", (username,))
    if not admin:
        return None
    if not check_password_hash(admin["password_hash"], password):
        return None
    return admin


def current_admin():
    admin_id = session.get("admin_id")
    if not admin_id:
        return None
    return query_one("SELECT id, username, role FROM admins WHERE id = ?", (admin_id,))


# Peran STAFF:
#   - login   : session["admin_id"]   (akun di tabel admins)
#   - role    : session["staff_role"] ('panitia' | 'admin') dipilih setelah login
#   - akun role 'panitia' TIDAK BOLEH memilih/mengakses role 'admin' (dicek di backend).

def allowed_staff_roles(staff):
    return ["panitia", "admin"] if staff and staff["role"] == "admin" else ["panitia"]


def _deny(api, status, reason, redirect_endpoint="staff_login"):
    if api:
        return jsonify({"success": False, "reason": reason}), status
    if status == 403:
        return render_template("forbidden.html"), 403
    return redirect(url_for(redirect_endpoint))


def _role_guard(required_role, api=False):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            staff = current_admin()
            if not staff:
                session.pop("staff_role", None)
                return _deny(api, 401, "not_logged_in")
            active = session.get("staff_role")
            # role aktif harus sesuai DAN akun harus berhak atas role tersebut
            if active != required_role or required_role not in allowed_staff_roles(staff):
                if not active:
                    return _deny(api, 401, "role_not_selected", "staff_roles")
                return _deny(api, 403, "forbidden")
            g.admin = staff
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


def admin_required(view_func):
    return _role_guard("admin")(view_func)


def admin_api_required(view_func):
    return _role_guard("admin", api=True)(view_func)


def panitia_required(view_func):
    return _role_guard("panitia")(view_func)


def panitia_api_required(view_func):
    return _role_guard("panitia", api=True)(view_func)


def staff_login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        staff = current_admin()
        if not staff:
            return redirect(url_for("staff_login"))
        g.admin = staff
        return view_func(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# PESERTA (KELOMPOK)
# ---------------------------------------------------------------------------

def current_group():
    group_id = session.get("group_id")
    if not group_id:
        return None
    return query_one("SELECT * FROM groups WHERE id = ? AND group_number BETWEEN 1 AND 5", (group_id,))


def group_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        group = current_group()
        if not group:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "reason": "not_identified"}), 401
            return redirect(url_for("group_select"))
        g.group = group
        return view_func(*args, **kwargs)
    return wrapped
