"""
app.py — تطبيق Flask الرئيسي لمتجر TADJ-INFO
Application Flask principale pour TADJ-INFO
"""

import os
import json
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from database import init_db, get_products, insert_order, get_all_orders, update_order_status

app = Flask(__name__)

# المفتاح السري — clé secrète (changez-la en production !)
app.secret_key = os.environ.get("SECRET_KEY", "tadj-info-change-me-in-production")

# كلمة مرور الإدارة — à définir via ADMIN_PASSWORD en production (jamais en dur)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "tadj2024")

# ── تهيئة قاعدة البيانات عند بدء التطبيق ───────────────────────
with app.app_context():
    init_db()


# ── حماية لوحة الإدارة ──────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════════
#  الصفحة الرئيسية — Page d'accueil
# ══════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    """يعرض الصفحة الرئيسية مع قائمة المنتجات للنموذج"""
    products = get_products()
    # تجميع المنتجات حسب الفئة لعرض أجمل
    categories = {}
    for p in products:
        cat = p["category"]
        categories.setdefault(cat, []).append(dict(p))
    return render_template("index.html", products=products, categories=categories)


# ══════════════════════════════════════════════════════════════════
#  API الطلبات — API Commandes
# ══════════════════════════════════════════════════════════════════
@app.route("/api/orders", methods=["POST"])
def api_orders():
    """استقبال طلب جديد من النموذج وحفظه في قاعدة البيانات"""
    try:
        # دعم JSON و form-data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        customer_name = (data.get("customer_name") or "").strip()
        phone         = (data.get("phone") or "").strip()
        address       = (data.get("address") or "").strip()
        product       = (data.get("product") or "").strip()
        order_type    = (data.get("order_type") or "").strip()
        note          = (data.get("note") or "").strip()

        # التحقق من الحقول المطلوبة
        errors = []
        if not customer_name:
            errors.append("الاسم واللقب مطلوب")
        if not phone:
            errors.append("رقم الهاتف مطلوب")
        if not product:
            errors.append("يرجى اختيار منتج أو خدمة")
        if order_type not in ("بيع", "تصليح"):
            errors.append("نوع الطلب غير صالح")

        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        order_id = insert_order(customer_name, phone, address, product, order_type, note)
        return jsonify({"success": True, "order_id": order_id}), 201

    except Exception as e:
        app.logger.error(f"خطأ في حفظ الطلب: {e}")
        return jsonify({"success": False, "errors": ["حدث خطأ داخلي، يرجى المحاولة لاحقاً"]}), 500


# ══════════════════════════════════════════════════════════════════
#  لوحة الإدارة — Panneau d'administration
# ══════════════════════════════════════════════════════════════════
@app.route("/admin", methods=["GET"])
@login_required
def admin():
    """لوحة التحكم: عرض كل الطلبات مع إمكانية تغيير الحالة"""
    orders = get_all_orders()
    status_filter = request.args.get("status", "")
    if status_filter:
        orders = [o for o in orders if o["status"] == status_filter]
    return render_template("admin.html", orders=orders, status_filter=status_filter)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """صفحة تسجيل دخول المسؤول"""
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        error = "كلمة المرور غير صحيحة"
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.route("/admin/update-status", methods=["POST"])
@login_required
def admin_update_status():
    """تحديث حالة الطلب من لوحة الإدارة"""
    order_id   = request.form.get("order_id")
    new_status = request.form.get("status")
    if order_id and new_status in ("جديد", "قيد المعالجة", "مكتمل"):
        update_order_status(int(order_id), new_status)
        flash("تم تحديث حالة الطلب بنجاح ✓", "success")
    else:
        flash("بيانات غير صالحة", "error")
    return redirect(url_for("admin"))


# ══════════════════════════════════════════════════════════════════
#  PWA manifest + service worker
# ══════════════════════════════════════════════════════════════════
@app.route("/manifest.json")
def manifest():
    return app.send_static_file("manifest.json")


@app.route("/sw.js")
def service_worker():
    response = app.send_static_file("sw.js")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


if __name__ == "__main__":
    # للتطوير المحلي فقط — Render يستخدم gunicorn مباشرة
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, host="0.0.0.0", port=port)
