# ============================================================================
#  OPERATION: RESTORE DATA LAB
#  app.py — entry point Flask (mekanisme Challenge Day AXIS 2026)
# ----------------------------------------------------------------------------
#  PESERTA  : tanpa login — pilih/identifikasi kelompok lalu langsung main.
#  PANITIA  : wajib login (password di-hash) untuk mengakses Dashboard Panitia.
#  Seluruh validasi jawaban, Mission Code, dan Final Code dilakukan di
#  BACKEND (lihat /services), bukan hanya di JavaScript.
# ============================================================================

import os
import json
import urllib.request

from flask import (
    Flask, render_template, request, session, redirect, url_for, jsonify,
    send_from_directory, send_file, g,
)

from db_layer.db import init_db, query_all, query_one, execute
from auth import (
    verify_admin_login, current_admin, admin_required, allowed_staff_roles,
    staff_login_required, panitia_required, panitia_api_required, admin_api_required,
    current_group, group_required,
)
from services.reset_service import reset_group, group_overview, get_epoch
from services import cooldown_service
from services.activity_log import log_activity
from services.group_access import MAX_GROUPS, group_code, code_is_default, parse_group_number, verify_group_code
from services.mission_service import (
    get_active_missions, get_mission_by_key, get_active_questions,
    get_group_progress_map, get_group_mission_codes, group_mission_code, ensure_progress_row,
    submit_mission_answers, serialize_question_for_frontend, saved_answers_map,
)
from services.final_service import verify_final_station
from services.codes import (
    get_code, set_code, code_source, get_final_code, fingerprint, init_codes, DEFAULT_CODES,
)

EXTERNAL_MISSIONS = {"knowledge"}   # Mission 5 (Knowledge Core) -> Website 2; bank soalnya TIDAK ada di Website 1

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ganti-dengan-random-secret-key-axis-2026-restore-data-lab")

with app.app_context():
    init_db()
    if not query_one("SELECT 1 FROM admins WHERE role = 'admin' LIMIT 1"):
        from seed import seed as _seed   # DB baru/kosong (mis. setelah redeploy) -> isi otomatis
        _seed()
    else:
        from seed import ensure_missions as _ensure   # database lama: selaraskan urutan/mode misi (idempoten)
        _ensure()
    init_codes()


# ============================================================================
# LINK WEBSITE 2 (Mission 5) & WEBSITE 3 (Final Mission) — satu tempat konfigurasi
# ============================================================================

LINK_ENV = {"w2": "WEBSITE2_URL", "w3": "WEBSITE3_URL"}
# target -> (website, path tujuan, label)
GO_TARGETS = {
    "mission5": ("w2", "", "Mission 5 — Knowledge Core (Website 2)"),
    "mission5-panitia": ("w2", "/panitia", "Pantau Knowledge Core (Website 2)"),
    "final": ("w3", "", "Final Mission (Website 3)"),
}


def ext_url(name):
    """URL dari env var (prioritas) atau pengaturan Admin. '' jika belum dikonfigurasi."""
    val = (os.environ.get(LINK_ENV[name]) or "").strip()
    if not val:
        row = query_one("SELECT value FROM challenge_settings WHERE key = ?", (f"website_url_{name}",))
        val = (row["value"] if row else "").strip()
    return val.rstrip("/")


@app.context_processor
def inject_links():
    return {"ext_w2": ext_url("w2"), "ext_w3": ext_url("w3")}


@app.route("/go/<target>")
def go_external(target):
    spec = GO_TARGETS.get(target)
    if not spec:
        return redirect(url_for("index"))
    name, path, label = spec
    url = ext_url(name)
    if not url or not url.startswith(("http://", "https://")):
        return render_template("external_missing.html", label=label), 503
    return redirect(url + path)


# ============================================================================
# HALAMAN PESERTA
# ============================================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/group")
def group_select():
    # Peserta yang sudah punya sesi kelompok tidak bisa kembali memilih kelompok lain.
    if current_group():
        return redirect(url_for("dashboard"))
    groups = query_all(
        "SELECT group_number, name FROM groups WHERE group_number BETWEEN 1 AND ? ORDER BY group_number",
        (MAX_GROUPS,),
    )
    return render_template("group_select.html", groups=groups)


@app.route("/group/select", methods=["POST"])
def group_select_submit():
    """Masuk ke kelompok dengan KODE AKSES. Setelah masuk, identitas dikunci di
    session server; permintaan lain (kelompok berbeda) ditolak."""
    if _group_fails() >= 40:
        return jsonify({"success": False, "reason": "too_many_attempts"}), 429
    payload = request.get_json(silent=True) or {}
    number = parse_group_number(payload.get("group_number"))
    access_code = str(payload.get("access_code", "")).strip()

    if number is None:
        return jsonify({"success": False, "reason": "not_found"})
    group = query_one("SELECT * FROM groups WHERE group_number = ?", (number,))
    if not group:
        return jsonify({"success": False, "reason": "not_found"})

    locked = session.get("group_id")
    if locked and locked != group["id"]:
        log_activity("group_switch_blocked", group_id=locked, detail=f"coba pindah ke kelompok {number}")
        return jsonify({"success": False, "reason": "already_identified"}), 403

    if not verify_group_code(number, access_code):
        _group_fails(add=True)
        log_activity("group_access_failed", group_id=group["id"], detail="Kode akses salah")
        return jsonify({"success": False, "reason": "wrong_access_code"})

    session["group_id"] = group["id"]
    log_activity("group_identified", group_id=group["id"], detail=f"{group['name']} mulai sesi")
    return jsonify({"success": True})


_GROUP_FAILS = {}


def _group_fails(add=False, window=300):
    """Hitung percobaan kode akses GAGAL per IP (satu Wi-Fi acara dipakai banyak peserta, jadi hanya kegagalan yang dihitung)."""
    import time
    ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "?").split(",")[0].strip()
    now = time.time()
    lst = [t for t in _GROUP_FAILS.get(ip, []) if now - t < window]
    if add:
        lst.append(now)
    _GROUP_FAILS[ip] = lst
    if len(_GROUP_FAILS) > 500:
        for k in [k for k, v in _GROUP_FAILS.items() if not v or now - v[-1] > window]:
            _GROUP_FAILS.pop(k, None)
    return len(lst)


@app.route("/dashboard")
@group_required
def dashboard():
    group = g.group
    missions = get_active_missions()
    progress_map = get_group_progress_map(group["id"])
    codes_map = get_group_mission_codes(group["id"])

    return render_template(
        "group_dashboard.html",
        group=group, missions=missions, progress_map=progress_map, codes_map=codes_map,
    )


@app.route("/mission/<key>")
@group_required
def mission_page(key):
    group = g.group
    mission = get_mission_by_key(key)
    if not mission or not mission["is_active"]:
        return redirect(url_for("dashboard"))
    if mission["mission_key"] in EXTERNAL_MISSIONS:
        return redirect(url_for("go_external", target="mission5"))
    if mission["station_mode"]:
        # Mission 1/3 dikerjakan di meja panitia, bukan self-serve peserta.
        return redirect(url_for("dashboard"))

    progress = ensure_progress_row(group["id"], mission["id"])
    questions = get_active_questions(mission["id"])

    saved = saved_answers_map(group["id"])
    questions_json = [
        serialize_question_for_frontend(q, saved.get(q["id"], (False, None))[0], group["id"], saved.get(q["id"], (False, None))[1]) for q in questions
    ]

    mission_code = group_mission_code(group["id"], mission)

    return render_template(
        "mission_page.html",
        group=group, mission=mission, questions_json=questions_json,
        progress=progress,
        mission_code=mission_code, reset_epoch=get_epoch(group["group_number"]),
        cooldown_remaining=cooldown_service.remaining(group["id"], mission["mission_key"], mission["id"]),
    )


def _parse_answers(payload):
    """Validasi bentuk payload submit -> (answers dict, error_reason)."""
    if not isinstance(payload, dict) or not isinstance(payload.get("answers"), dict):
        return None, "bad_request"
    answers = payload["answers"]
    if not answers:
        return None, "no_answers"
    if len(answers) > 200:
        return None, "bad_request"
    return answers, None


@app.route("/api/mission/<key>/submit", methods=["POST"])
@group_required
def api_mission_submit(key):
    mission = get_mission_by_key(key)
    if not mission or not mission["is_active"] or mission["mission_key"] in EXTERNAL_MISSIONS:
        return jsonify({"success": False, "reason": "inactive"})

    answers, err = _parse_answers(request.get_json(silent=True))
    if err:
        return jsonify({"success": False, "reason": err}), 400
    res = submit_mission_answers(g.group, mission, answers)
    return (jsonify(res), 429) if res.get("reason") == "cooldown" else jsonify(res)


@app.route("/download/dataset")
@group_required
def download_dataset():
    return send_from_directory(DATA_DIR, "student_dataset.csv", as_attachment=True)


_DATASET_CACHE = {"mtime": None, "cols": [], "rows": []}


@app.route("/dataset")
def dataset_view():
    """Tampilan tabel CSV (baca-saja). Dibaca sekali lalu di-cache sampai file berubah."""
    from services.dataset_audit import read_rows
    path = os.path.join(DATA_DIR, "student_dataset.csv")
    mtime = os.path.getmtime(path)
    if _DATASET_CACHE["mtime"] != mtime:
        cols, rows = read_rows(path)
        _DATASET_CACHE.update(mtime=mtime, cols=cols, rows=rows)
    return render_template("dataset_view.html", cols=_DATASET_CACHE["cols"], rows=_DATASET_CACHE["rows"])


@app.route("/download/dataset-public")
def download_dataset_public():
    """Sama seperti /download/dataset tapi tanpa syarat sesi kelompok — dipakai
    di halaman Station (meja panitia) yang tidak memiliki sesi peserta."""
    return send_from_directory(DATA_DIR, "student_dataset.csv", as_attachment=True)


# ============================================================================
# STATION MODE — Mission 1 dan 3 dikerjakan di meja panitia (password +
# pergantian kelompok cepat tanpa reload/logout).
# ============================================================================

def _station_session_key(mission_key):
    return f"station_auth_{mission_key}"


@app.route("/station/<key>", methods=["GET"])
@panitia_required
def station_page(key):
    mission = get_mission_by_key(key)
    if not mission or not mission["station_mode"]:
        return redirect(url_for("index"))

    unlocked = bool(session.get(_station_session_key(key)))
    all_groups = query_all("SELECT id, group_number, name FROM groups WHERE group_number BETWEEN 1 AND 5 ORDER BY group_number")

    return render_template(
        "station_page.html", mission=mission, unlocked=unlocked, groups=all_groups,
    )


@app.route("/api/station/<key>/auth", methods=["POST"])
@panitia_api_required
def api_station_auth(key):
    mission = get_mission_by_key(key)
    if not mission or not mission["station_mode"]:
        return jsonify({"success": False, "reason": "not_station"})

    payload = request.get_json(force=True) or {}
    password = str(payload.get("password", ""))

    if not mission["station_password"] or password != mission["station_password"]:
        log_activity("station_auth_failed", mission_id=mission["id"], detail=f"key={key}")
        return jsonify({"success": False, "reason": "wrong_password"})

    session[_station_session_key(key)] = True
    log_activity("station_auth_success", mission_id=mission["id"], detail=f"key={key}")
    return jsonify({"success": True})


@app.route("/station/<key>/lock")
@panitia_required
def station_lock(key):
    session.pop(_station_session_key(key), None)
    return redirect(url_for("station_page", key=key))


@app.route("/api/station/<key>/state")
@panitia_api_required
def api_station_state(key):
    mission = get_mission_by_key(key)
    if not mission or not mission["station_mode"]:
        return jsonify({"success": False, "reason": "not_station"})
    if not session.get(_station_session_key(key)):
        return jsonify({"success": False, "reason": "locked"})

    group_id = request.args.get("group_id", type=int)
    grp = query_one("SELECT * FROM groups WHERE id = ? AND group_number BETWEEN 1 AND 5", (group_id,)) if group_id else None
    if not grp:
        return jsonify({"success": False, "reason": "invalid_group"})

    progress = ensure_progress_row(grp["id"], mission["id"])
    questions = get_active_questions(mission["id"])
    saved = saved_answers_map(grp["id"])           # HANYA data kelompok yang diminta (id divalidasi di atas), bukan state klien
    questions_json = [
        serialize_question_for_frontend(q, saved.get(q["id"], (False, None))[0], grp["id"], saved.get(q["id"], (False, None))[1]) for q in questions
    ]

    mission_code = group_mission_code(grp["id"], mission)

    resp = jsonify({
        "success": True,
        "group": {"id": grp["id"], "group_number": grp["group_number"], "name": grp["name"]},
        "questions": questions_json,
        "progress": {"correct_points": progress["correct_points"], "status": progress["status"]},
        "requirement_points": mission["requirement_points"],
        "mission_code": mission_code,
    })
    resp.headers["Cache-Control"] = "no-store"      # jangan pernah menyajikan state kelompok dari cache perantara/peramban
    return resp


@app.route("/api/station/<key>/submit", methods=["POST"])
@panitia_api_required
def api_station_submit(key):
    mission = get_mission_by_key(key)
    if not mission or not mission["station_mode"]:
        return jsonify({"success": False, "reason": "not_station"})
    if not session.get(_station_session_key(key)):
        return jsonify({"success": False, "reason": "locked"})

    payload = request.get_json(silent=True) or {}
    group_id = payload.get("group_id")
    grp = query_one("SELECT * FROM groups WHERE id = ? AND group_number BETWEEN 1 AND 5", (group_id,)) if group_id else None
    if not grp:
        return jsonify({"success": False, "reason": "invalid_group"})

    answers, err = _parse_answers(payload)
    if err:
        return jsonify({"success": False, "reason": err}), 400
    res = submit_mission_answers(grp, mission, answers)
    res["group_id"] = grp["id"]                       # klien memeriksa bahwa respons memang untuk kelompok yang sedang dipilih
    return jsonify(res)


# ============================================================================
# PANITIA — AUTH
# ============================================================================

@app.route("/staff/login", methods=["GET", "POST"])
def staff_login():
    if request.method == "GET":
        if current_admin():
            return redirect(url_for("staff_roles"))
        return render_template("admin_login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    staff = verify_admin_login(username, password)
    if not staff:
        log_activity("admin_login_failed", detail=f"username={username}")
        return render_template("admin_login.html", error="Username atau password salah.")

    session.clear()                       # cegah session fixation / sisa role lama
    session["admin_id"] = staff["id"]     # role BELUM dipilih -> wajib lewat SELECT STAFF ROLE
    log_activity("admin_login", admin_id=staff["id"], detail=staff["username"])
    return redirect(url_for("staff_roles"))


@app.route("/staff/roles")
@staff_login_required
def staff_roles():
    session.pop("staff_role", None)
    return render_template("staff_roles.html", allowed=allowed_staff_roles(g.admin))


@app.route("/staff/roles/select", methods=["POST"])
@staff_login_required
def staff_role_select():
    role = request.form.get("role", "")
    if role not in allowed_staff_roles(g.admin):
        log_activity("role_denied", admin_id=g.admin["id"], detail=f"requested={role}")
        return render_template("forbidden.html"), 403
    session["staff_role"] = role
    log_activity("role_selected", admin_id=g.admin["id"], detail=role)
    return redirect(url_for("admin_dashboard" if role == "admin" else "panitia_operations"))


@app.route("/staff/panitia")
@panitia_required
def panitia_operations():
    stations = query_all(
        """SELECT mission_key, name, icon, description FROM missions
           WHERE station_mode = 1 AND is_active = 1
             AND mission_key IN ('python', 'database') ORDER BY sort_order""")
    kc = get_mission_by_key("knowledge")
    return render_template("panitia_operations.html", stations=stations,
                           kc=kc if kc and kc["is_active"] else None)


@app.route("/admin/login")
def legacy_admin_login():
    return redirect(url_for("staff_login"))


@app.route("/admin/logout")
def legacy_admin_logout():
    return redirect(url_for("staff_logout"))


@app.route("/staff/logout")
def staff_logout():
    staff = current_admin()
    if staff:
        log_activity("admin_logout", admin_id=staff["id"])
    session.clear()                       # hapus login, role, dan seluruh sesi station
    return redirect(url_for("index"))


# ============================================================================
# PANITIA — DASHBOARD OVERVIEW
# ============================================================================

@app.route("/admin")
@admin_required
def admin_dashboard():
    total_groups = query_one("SELECT COUNT(*) c FROM groups WHERE group_number BETWEEN 1 AND 5")["c"]
    active_groups = query_one("SELECT COUNT(*) c FROM groups WHERE group_number BETWEEN 1 AND 5 AND status = 'in_progress'")["c"]
    completed_groups = query_one("SELECT COUNT(*) c FROM groups WHERE group_number BETWEEN 1 AND 5 AND status = 'completed'")["c"]

    missions = get_active_missions()
    mission_stats = []
    for m in missions:
        completed = query_one(
            "SELECT COUNT(*) c FROM mission_progress WHERE mission_id = ? AND status = 'completed'",
            (m["id"],),
        )["c"]
        mission_stats.append({"mission": m, "completed": completed})

    local_ids = [m["id"] for m in missions if m["mission_key"] not in EXTERNAL_MISSIONS]
    all_codes_count = query_one(
        f"""SELECT COUNT(*) c FROM (
              SELECT group_id FROM mission_progress WHERE status = 'completed' AND mission_id IN ({",".join("?" for _ in local_ids) or "NULL"})
              GROUP BY group_id HAVING COUNT(DISTINCT mission_id) = ?
            )""",
        (*local_ids, len(local_ids)),
    )["c"]

    return render_template(
        "admin_dashboard.html",
        total_groups=total_groups, active_groups=active_groups, completed_groups=completed_groups,
        mission_stats=mission_stats, all_codes_count=all_codes_count,
        
    )


# ============================================================================
# PANITIA — KELOMPOK
# ============================================================================

@app.route("/admin/groups")
@admin_required
def admin_groups():
    groups = query_all("SELECT * FROM groups WHERE group_number BETWEEN 1 AND 5 ORDER BY group_number")
    missions = [m for m in get_active_missions() if m["mission_key"] not in EXTERNAL_MISSIONS]

    monitor_rows = []
    for grp in groups:
        progress_map = get_group_progress_map(grp["id"])
        monitor_rows.append({
            "group": grp,
            "mission_status": [progress_map.get(m["mission_key"], {}).get("status", "locked") for m in missions],
            "group_codes": get_group_mission_codes(grp["id"]),
        })

    access_codes = {r["group"]["group_number"]: {"code": group_code(r["group"]["group_number"]),
                    "default": code_is_default(r["group"]["group_number"])} for r in monitor_rows}
    return render_template("admin_groups.html", missions=missions, monitor_rows=monitor_rows, access_codes=access_codes)


@app.route("/admin/groups/add", methods=["POST"])
@admin_required
def admin_groups_add():
    # Jumlah kelompok dikunci pada lima (Kelompok 1-5).
    return redirect(url_for("admin_groups"))


@app.route("/admin/groups/<int:group_id>")
@admin_required
def admin_group_detail(group_id):
    grp = query_one("SELECT * FROM groups WHERE id = ? AND group_number BETWEEN 1 AND 5", (group_id,))
    if not grp:
        return redirect(url_for("admin_groups"))

    missions = [m for m in get_active_missions() if m["mission_key"] not in EXTERNAL_MISSIONS]
    progress_map = get_group_progress_map(grp["id"])
    codes_map = get_group_mission_codes(grp["id"])

    return render_template(
        "admin_group_detail.html",
        group=grp, missions=missions, progress_map=progress_map, codes_map=codes_map,
    )


@app.route("/admin/groups/<int:group_id>/update", methods=["POST"])
@admin_required
def admin_group_update(group_id):
    name = request.form.get("name", "").strip()
    status = request.form.get("status", "not_started")
    if status not in ("not_started", "in_progress", "completed"):
        status = "not_started"
    # Kode akses TIDAK disimpan di database: bersumber dari environment (lihat services/group_access.py).
    execute(
        "UPDATE groups SET name = ?, status = ? WHERE id = ?",
        (name, status, group_id),
    )
    log_activity("group_updated", group_id=group_id, admin_id=g.admin["id"], detail=name)
    return redirect(url_for("admin_group_detail", group_id=group_id))


@app.route("/admin/reset")
@admin_required
def admin_reset_page():
    """Reset seluruh pengerjaan SATU kelompok pada Website 1 (bukan per misi/per jawaban/global)."""
    groups = query_all("SELECT group_number, name FROM groups WHERE group_number BETWEEN 1 AND 5 ORDER BY group_number")
    for gr in groups:
        gr["overview"] = group_overview(gr["group_number"])
    return render_template("admin_reset.html", groups=groups, preselect=request.args.get("group", type=int))


@app.route("/api/admin/reset", methods=["POST"])
@admin_api_required
def api_admin_reset():
    """JSON: {group_number, confirm_group}. Kelompok divalidasi 1-5 di backend; konfirmasi harus sama dengan kelompok."""
    p = request.get_json(silent=True)
    gn = p.get("group_number") if isinstance(p, dict) else None
    if isinstance(gn, str) and gn.isdigit():
        gn = int(gn)
    if not isinstance(gn, int) or isinstance(gn, bool) or not 1 <= gn <= 5:
        return jsonify({"success": False, "reason": "invalid_group"}), 400
    conf = p.get("confirm_group")
    if isinstance(conf, str) and conf.isdigit():
        conf = int(conf)
    if conf != gn:
        return jsonify({"success": False, "reason": "not_confirmed"}), 400
    try:
        res = reset_group(gn, admin_id=g.admin["id"])
    except ValueError:
        return jsonify({"success": False, "reason": "invalid_group"}), 400
    except Exception:
        app.logger.exception("reset gagal")
        return jsonify({"success": False, "reason": "server_error"}), 500
    return jsonify({"success": True, **res, "overview": group_overview(gn)})


# ============================================================================
# PANITIA — MISSION
# ============================================================================

@app.route("/admin/missions")
@admin_required
def admin_missions():
    missions = query_all("SELECT * FROM missions ORDER BY sort_order")
    return render_template("admin_missions.html", missions=missions)


@app.route("/admin/missions/<int:mission_id>/update", methods=["POST"])
@admin_required
def admin_mission_update(mission_id):
    name = request.form.get("name", "").strip()
    icon = request.form.get("icon", "").strip() or "🛰"
    description = request.form.get("description", "").strip()
    instructions = request.form.get("instructions", "").strip()
    is_active = 1 if request.form.get("is_active") == "on" else 0
    requirement_points = int(request.form.get("requirement_points") or 0)
    mission_code_prefix = request.form.get("mission_code_prefix", "MC").strip().upper() or "MC"

    mission_row = query_one("SELECT station_mode, station_password FROM missions WHERE id = ?", (mission_id,))
    station_password = None
    if mission_row and mission_row["station_mode"]:
        password_input = request.form.get("station_password", "").strip()
        station_password = password_input or mission_row["station_password"]

    execute(
        """UPDATE missions SET name=?, icon=?, description=?, instructions=?, is_active=?,
           requirement_points=?, mission_code_prefix=?,
           station_password = CASE WHEN station_mode = 1 THEN ? ELSE station_password END
           WHERE id=?""",
        (name, icon, description, instructions, is_active, requirement_points,
         mission_code_prefix, station_password, mission_id),
    )
    log_activity("mission_settings_updated", mission_id=mission_id, admin_id=g.admin["id"], detail=name)
    return redirect(url_for("admin_missions"))


# ============================================================================
# PANITIA — BANK SOAL (PERTANYAAN)
# ============================================================================

@app.route("/admin/questions")
@admin_required
def admin_questions():
    missions = query_all("SELECT * FROM missions WHERE mission_key NOT IN ('knowledge') ORDER BY sort_order")
    categories = query_all("SELECT * FROM categories ORDER BY name")

    mission_filter = request.args.get("mission", "")
    category_filter = request.args.get("category", "")
    search = request.args.get("q", "").strip()
    active_filter = request.args.get("active", "")

    sql = """SELECT q.*, m.name AS mission_name, m.mission_key FROM questions q
              JOIN missions m ON m.id = q.mission_id WHERE m.mission_key != 'knowledge'"""
    params = []
    if mission_filter:
        sql += " AND m.mission_key = ?"
        params.append(mission_filter)
    if category_filter:
        sql += " AND q.category = ?"
        params.append(category_filter)
    if search:
        sql += " AND q.prompt LIKE ?"
        params.append(f"%{search}%")
    if active_filter == "active":
        sql += " AND q.is_active = 1"
    elif active_filter == "inactive":
        sql += " AND q.is_active = 0"
    sql += " ORDER BY m.sort_order, q.sort_order, q.id"

    questions = query_all(sql, tuple(params))
    for q in questions:
        q["options"] = json.loads(q["options_json"]) if q["options_json"] else []

    return render_template(
        "admin_questions.html", missions=missions, categories=categories, questions=questions,
        mission_filter=mission_filter, category_filter=category_filter, search=search, active_filter=active_filter,
        error=request.args.get("error", ""),
    )


def _validate_question_key(answer_type, correct_answer, options_json):
    """Kunci jawaban HARUS konsisten dengan opsi, karena penilaian membandingkan nilai opsi yang dipilih dengan kunci.
    Mengembalikan None (valid), tuple ("fix", kunci_kanonik) atau pesan error."""
    opts = json.loads(options_json) if options_json else None
    if answer_type == "multiple_choice":
        if not opts or len(opts) < 2 or len(set(opts)) != len(opts):
            return "pilihan ganda butuh minimal 2 opsi yang berbeda."
        if correct_answer in opts:
            return None
        ci = [o for o in opts if " ".join(o.split()).lower() == " ".join(correct_answer.split()).lower()]
        if len(ci) == 1:
            return ("fix", ci[0])
        return "kunci jawaban harus sama persis dengan salah satu opsi."
    if answer_type == "multiple_select":
        key = json.loads(correct_answer) if correct_answer.startswith("[") else []
        if not opts or len(opts) < 2 or not key or not set(key) <= set(opts) or len(set(key)) != len(key):
            return "multiple select: kunci harus berisi minimal satu opsi, tanpa duplikat, dan semuanya ada di daftar opsi."
        return None
    if answer_type == "ordering":
        key = json.loads(correct_answer) if correct_answer.startswith("[") else []
        if not opts or len(opts) < 2 or sorted(key) != sorted(opts) or len(set(opts)) != len(opts):
            return "ordering: urutan benar harus memuat semua item (tanpa duplikat) tepat satu kali."
        return None
    if answer_type == "matching":
        key = json.loads(correct_answer) if correct_answer.startswith("{") else {}
        if not key or set(key) != set(opts["left"]) or not set(key.values()) <= set(opts["right"]):
            return "matching: pasangan tidak lengkap."
        return None
    if answer_type == "number":
        try:
            float(correct_answer)
        except ValueError:
            return "kunci angka harus berupa bilangan (gunakan titik untuk desimal)."
        return None
    if answer_type == "true_false":
        if correct_answer not in ("true", "false"):
            return "kunci benar/salah harus true atau false."
        return None
    if answer_type == "text" and not correct_answer:
        return "kunci jawaban isian tidak boleh kosong."
    return None


@app.route("/admin/questions/save", methods=["POST"])
@admin_required
def admin_question_save():
    question_id = request.form.get("id")
    mission_id = int(request.form.get("mission_id"))
    category = request.form.get("category", "General Knowledge").strip()
    prompt = request.form.get("prompt", "").replace("\r\n", "\n").replace("\r", "\n").strip()
    answer_type = request.form.get("answer_type", "text")
    correct_answer = request.form.get("correct_answer", "").strip()
    match_mode = request.form.get("match_mode", "case_insensitive")
    points = int(request.form.get("points") or 1)
    is_active = 1 if request.form.get("is_active") == "on" else 0

    if query_one("SELECT 1 FROM missions WHERE id = ? AND mission_key = 'knowledge'", (mission_id,)):
        return redirect(url_for("admin_questions", error="Soal Mission 5 (Knowledge Core) dikelola di Website 2."))
    # Category wajib berasal dari Category Management (bukan teks bebas)
    if not query_one("SELECT id FROM categories WHERE name = ?", (category,)):
        return redirect(url_for("admin_questions", error="Kategori tidak valid. Pilih dari daftar kategori."))

    options_json = None

    if answer_type in ("multiple_choice", "multiple_select"):
        options_raw = request.form.get("options", "").strip()
        options_list = [o.strip() for o in options_raw.split("\n") if o.strip()]
        options_json = json.dumps(options_list)
        if answer_type == "multiple_select":
            selected_raw = request.form.get("multi_correct", "").strip()
            correct_list = [o.strip() for o in selected_raw.split("\n") if o.strip()]
            correct_answer = json.dumps(correct_list)

    elif answer_type == "true_false":
        correct_answer = correct_answer.strip().lower()

    elif answer_type == "ordering":
        items_raw = request.form.get("ordering_items", "").strip()
        correct_order_raw = request.form.get("ordering_correct", "").strip()
        items_list = [o.strip() for o in items_raw.split("\n") if o.strip()]
        correct_list = [o.strip() for o in correct_order_raw.split("\n") if o.strip()]
        options_json = json.dumps(items_list)
        correct_answer = json.dumps(correct_list)

    elif answer_type == "matching":
        pairs_raw = request.form.get("matching_pairs", "").strip()
        left_items, right_items, pair_map = [], [], {}
        for line in pairs_raw.split("\n"):
            if "=>" in line:
                left, right = line.split("=>", 1)
                left, right = left.strip(), right.strip()
                if left and right:
                    left_items.append(left)
                    if right not in right_items:
                        right_items.append(right)
                    pair_map[left] = right
        options_json = json.dumps({"left": left_items, "right": right_items})
        correct_answer = json.dumps(pair_map)

    elif answer_type == "essay":
        correct_answer = ""

    problem = _validate_question_key(answer_type, correct_answer, options_json)
    if isinstance(problem, tuple):                 # kunci disesuaikan ke nilai opsi yang tepat (mis. beda huruf besar/kecil)
        correct_answer = problem[1]
    elif problem:
        return redirect(url_for("admin_questions", error="Soal tidak disimpan: " + problem))

    if question_id:
        execute(
            """UPDATE questions SET mission_id=?, category=?, prompt=?, answer_type=?, correct_answer=?,
               match_mode=?, options_json=?, points=?, is_active=? WHERE id=?""",
            (mission_id, category, prompt, answer_type, correct_answer, match_mode,
             options_json, points, is_active, question_id),
        )
        log_activity("question_updated", mission_id=mission_id, admin_id=g.admin["id"], detail=prompt[:80])
    else:
        execute(
            """INSERT INTO questions (mission_id, category, prompt, answer_type, correct_answer,
               match_mode, options_json, points, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (mission_id, category, prompt, answer_type, correct_answer, match_mode,
             options_json, points, is_active),
        )
        log_activity("question_added", mission_id=mission_id, admin_id=g.admin["id"], detail=prompt[:80])

    return redirect(url_for("admin_questions"))


@app.route("/admin/questions/<int:question_id>/delete", methods=["POST"])
@admin_required
def admin_question_delete(question_id):
    execute("DELETE FROM question_progress WHERE question_id = ?", (question_id,))
    execute("DELETE FROM questions WHERE id = ?", (question_id,))
    log_activity("question_deleted", admin_id=g.admin["id"], detail=f"question_id={question_id}")
    return redirect(url_for("admin_questions"))


@app.route("/admin/questions/<int:question_id>/toggle", methods=["POST"])
@admin_required
def admin_question_toggle(question_id):
    q = query_one("SELECT is_active FROM questions WHERE id = ?", (question_id,))
    if q:
        execute("UPDATE questions SET is_active = ? WHERE id = ?", (0 if q["is_active"] else 1, question_id))
        log_activity("question_toggled", admin_id=g.admin["id"], detail=f"question_id={question_id}")
    return redirect(url_for("admin_questions"))


# ============================================================================
# PANITIA — PENGATURAN CHALLENGE (kategori + konten Final Mission)
# ============================================================================

@app.route("/admin/settings")
@admin_required
def admin_settings():
    categories = query_all("SELECT * FROM categories ORDER BY name")
    return render_template(
        "admin_settings.html", categories=categories, cooldown_enabled=cooldown_service.is_enabled(),
        cooldown_seconds=cooldown_service.COOLDOWN_SECONDS, msg=request.args.get("ok"),
        final_station_password=_get_final_station_password(),
    )


@app.route("/admin/settings/final-station-password/update", methods=["POST"])
@admin_required
def admin_final_station_password_update():
    new_password = request.form.get("final_station_password", "").strip()
    if new_password:
        execute(
            """INSERT INTO challenge_settings (key, value) VALUES ('final_station_password', ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
            (new_password,),
        )
        log_activity("final_station_password_updated", admin_id=g.admin["id"])
    return redirect(url_for("admin_settings"))


@app.route("/admin/settings/wrong-cooldown/update", methods=["POST"])
@admin_required
def admin_wrong_cooldown_update():
    """Aktif/nonaktif jeda jawaban salah (hanya Mission 2 & 4). Dicek di backend: hanya admin."""
    val = request.form.get("enabled", "")
    if val not in ("0", "1"):
        return redirect(url_for("admin_settings", ok="Nilai tidak valid; pengaturan tidak diubah."))
    cooldown_service.set_enabled(val == "1")
    log_activity("wrong_cooldown_" + ("enabled" if val == "1" else "disabled"), admin_id=g.admin["id"])
    return redirect(url_for("admin_settings", ok="Jeda jawaban salah " + ("DIAKTIFKAN" if val == "1" else "DINONAKTIFKAN") + "."))


# ---- Knowledge Core -> Categories (Category Management) ----

@app.route("/admin/categories")
@admin_required
def admin_categories():
    categories = query_all(
        """SELECT c.*, (SELECT COUNT(*) FROM questions q WHERE q.category = c.name) AS question_count
           FROM categories c ORDER BY c.name""")
    return render_template("admin_categories.html", categories=categories,
                           msg=request.args.get("msg", ""), err=request.args.get("err", ""))


@app.route("/admin/categories/save", methods=["POST"])
@admin_required
def admin_category_save():
    cid = request.form.get("id", type=int)
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    is_active = 1 if request.form.get("status", "active") == "active" else 0
    if not name:
        return redirect(url_for("admin_categories", err="Nama kategori wajib diisi."))
    dup = query_one("SELECT id FROM categories WHERE LOWER(name) = LOWER(?) AND id != ?", (name, cid or 0))
    if dup:
        return redirect(url_for("admin_categories", err="Nama kategori sudah dipakai."))

    if cid:
        old = query_one("SELECT name FROM categories WHERE id = ?", (cid,))
        if not old:
            return redirect(url_for("admin_categories", err="Kategori tidak ditemukan."))
        execute("UPDATE categories SET name=?, description=?, is_active=? WHERE id=?",
                (name, description, is_active, cid))
        if old["name"] != name:  # soal mengacu ke nama kategori -> ikut diperbarui
            execute("UPDATE questions SET category = ? WHERE category = ?", (name, old["name"]))
        log_activity("category_updated", admin_id=g.admin["id"], detail=name)
    else:
        execute("INSERT INTO categories (name, description, is_active) VALUES (?, ?, ?)",
                (name, description, is_active))
        log_activity("category_added", admin_id=g.admin["id"], detail=name)
    return redirect(url_for("admin_categories", msg="Kategori disimpan."))


@app.route("/admin/categories/<int:category_id>/delete", methods=["POST"])
@admin_required
def admin_category_delete(category_id):
    cat = query_one("SELECT * FROM categories WHERE id = ?", (category_id,))
    if not cat:
        return redirect(url_for("admin_categories", err="Kategori tidak ditemukan."))
    used = query_one("SELECT COUNT(*) c FROM questions WHERE category = ?", (cat["name"],))["c"]
    if used:
        # kategori masih dipakai: wajib pindahkan soal ke kategori lain (tidak ada hapus diam-diam)
        target_id = request.form.get("move_to", type=int)
        target = query_one("SELECT * FROM categories WHERE id = ? AND id != ?", (target_id, category_id)) if target_id else None
        if not target:
            return redirect(url_for("admin_categories",
                err=f"This category is currently used by {used} questions. Pilih kategori tujuan untuk memindahkan soal."))
        execute("UPDATE questions SET category = ? WHERE category = ?", (target["name"], cat["name"]))
    execute("DELETE FROM categories WHERE id = ?", (category_id,))
    log_activity("category_deleted", admin_id=g.admin["id"], detail=f"{cat['name']} ({used} soal dipindah)")
    return redirect(url_for("admin_categories", msg="Kategori dihapus."))


# endpoint lama (Pengaturan Challenge) diarahkan ke halaman Categories yang baru
@app.route("/admin/settings/categories/add", methods=["POST"])
@admin_required
def admin_category_add():
    return admin_category_save()


# ============================================================================
# ADMIN — MISSION CODE, FINAL CODE & LINK WEBSITE 2/3 + BACKUP
# ============================================================================

def _remote_fingerprints(base_url):
    """Ambil sidik jari kode dari website lain (timeout pendek, gagal -> None)."""
    if not base_url:
        return None, "URL belum dikonfigurasi"
    try:
        with urllib.request.urlopen(base_url + "/api/fingerprint", timeout=4) as r:
            return json.loads(r.read().decode()), None
    except Exception as exc:  # jaringan/cold start/format salah -> jangan merusak halaman
        return None, f"Tidak dapat dihubungi ({type(exc).__name__}). Website mungkin sedang cold start."


@app.route("/admin/codes")
@admin_required
def admin_codes():
    missions = get_active_missions()
    codes = [{"mission": m, "code": get_code(m["mission_key"]), "locked": code_source(m["mission_key"]) == "env"}
             for m in missions]
    final = {"code": get_final_code(), "locked": code_source("final") == "env"}
    check = None
    if request.args.get("check"):
        check = {}
        w2, err2 = _remote_fingerprints(ext_url("w2"))
        w3, err3 = _remote_fingerprints(ext_url("w3"))
        check["w2"] = {"error": err2, "match": bool(w2 and w2.get("mission5") == fingerprint(get_code("knowledge")))}
        check["w3"] = {"error": err3, "match": bool(w3 and w3.get("final") == fingerprint(get_final_code()))}
    links = {n: {"value": ext_url(n), "locked": bool((os.environ.get(LINK_ENV[n]) or "").strip())} for n in ("w2", "w3")}
    return render_template("admin_codes.html", codes=codes, final=final, links=links, check=check,
                           msg=request.args.get("msg", ""))


@app.route("/admin/codes/save", methods=["POST"])
@admin_required
def admin_codes_save():
    for m in get_active_missions():
        val = request.form.get(f"code_{m['mission_key']}")
        if val is not None:
            set_code(m["mission_key"], val)
    if request.form.get("final_code") is not None:
        set_code("final", request.form.get("final_code"))
    for n in ("w2", "w3"):
        val = request.form.get(f"url_{n}")
        if val is not None and not (os.environ.get(LINK_ENV[n]) or "").strip():
            val = val.strip()
            if val and not val.startswith(("http://", "https://")):
                return redirect(url_for("admin_codes", msg="URL harus diawali http:// atau https://"))
            execute("""INSERT INTO challenge_settings (key, value) VALUES (?, ?)
                       ON CONFLICT(key) DO UPDATE SET value = excluded.value""", (f"website_url_{n}", val))
    log_activity("codes_updated", admin_id=g.admin["id"], detail="Mission Code / Final Code / link diperbarui")
    return redirect(url_for("admin_codes", msg="Tersimpan."))


@app.route("/admin/backup")
@admin_required
def admin_backup():
    """Unduh salinan konsisten database (SQLite online backup). Hanya unduh data ke komputer admin."""
    import sqlite3, tempfile
    from db_layer.db import DB_PATH
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    src = sqlite3.connect(DB_PATH); dst = sqlite3.connect(tmp.name)
    with dst:
        src.backup(dst)
    src.close(); dst.close()
    log_activity("backup_downloaded", admin_id=g.admin["id"])
    return send_file(tmp.name, as_attachment=True, download_name="restore_data_lab_backup.db")


@app.route("/healthz")
def healthz():
    return "ok", 200


# ============================================================================
# FINAL MISSION STATION (di luar Admin — sejajar dengan station panitia
# lainnya). Di sini panitia memasukkan Mission Code 1-5 milik SATU kelompok
# yang sedang diproses untuk menghasilkan Final Code.
# ============================================================================

FINAL_STATION_KEY = "final"


def _get_final_station_password():
    row = query_one("SELECT value FROM challenge_settings WHERE key = 'final_station_password'")
    return row["value"] if row else None


@app.route("/station/final", methods=["GET"])
@panitia_required
def final_station_page():
    unlocked = bool(session.get(_station_session_key(FINAL_STATION_KEY)))
    return render_template("final_station.html", unlocked=unlocked, missions=get_active_missions())


@app.route("/api/station/final/auth", methods=["POST"])
@panitia_api_required
def api_final_station_auth():
    payload = request.get_json(force=True) or {}
    password = str(payload.get("password", ""))
    expected = _get_final_station_password()

    if not expected or password != expected:
        log_activity("station_auth_failed", detail="key=final")
        return jsonify({"success": False, "reason": "wrong_password"})

    session[_station_session_key(FINAL_STATION_KEY)] = True
    log_activity("station_auth_success", detail="key=final")
    return jsonify({"success": True})


@app.route("/station/final/lock")
@panitia_required
def final_station_lock():
    session.pop(_station_session_key(FINAL_STATION_KEY), None)
    return redirect(url_for("final_station_page"))


@app.route("/api/station/final/verify", methods=["POST"])
@panitia_api_required
def api_final_station_verify():
    if not session.get(_station_session_key(FINAL_STATION_KEY)):
        return jsonify({"success": False, "reason": "locked"})

    payload = request.get_json(force=True) or {}
    result = verify_final_station([payload.get(f"code{i}", "") for i in range(1, 6)])
    return jsonify(result)


# ============================================================================
# PANITIA — ACTIVITY LOG
# ============================================================================

@app.route("/admin/logs")
@admin_required
def admin_logs():
    group_filter = request.args.get("group", "")
    sql = """SELECT al.*, g.name AS group_name, m.name AS mission_name, a.username AS admin_username
             FROM activity_logs al
             LEFT JOIN groups g ON g.id = al.group_id
             LEFT JOIN missions m ON m.id = al.mission_id
             LEFT JOIN admins a ON a.id = al.admin_id
             WHERE 1=1"""
    params = []
    if group_filter:
        sql += " AND al.group_id = ?"
        params.append(group_filter)
    sql += " ORDER BY al.ts DESC LIMIT 200"

    logs = query_all(sql, tuple(params))
    groups = query_all("SELECT id, name FROM groups WHERE group_number BETWEEN 1 AND 5 ORDER BY group_number")
    return render_template("admin_logs.html", logs=logs, groups=groups, group_filter=group_filter)


if __name__ == "__main__":
    app.run(debug=True)
