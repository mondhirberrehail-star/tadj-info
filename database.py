"""
database.py — إدارة قاعدة البيانات SQLite لمتجر TADJ-INFO
Gestion de la base de données SQLite pour TADJ-INFO
"""

import sqlite3
import os
from datetime import datetime

# مسار قاعدة البيانات — chemin vers la base de données
# في الإنتاج: DATABASE_PATH=/data/tadj_info.db (Render Persistent Disk)
# محلياً: tadj_info.db في مجلد المشروع
_default_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tadj_info.db")
DB_PATH = os.environ.get("DATABASE_PATH", _default_db)


def get_db():
    """فتح اتصال بقاعدة البيانات — Ouvre une connexion à la BDD"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # الوصول للأعمدة بالاسم
    conn.execute("PRAGMA journal_mode=WAL")  # أداء أفضل مع التطبيقات المتعددة
    return conn


def init_db():
    """
    إنشاء الجداول وملء البيانات الأولية إذا كانت فارغة
    Crée les tables et insère les données initiales si vides
    """
    conn = get_db()
    cur = conn.cursor()

    # ── جدول المنتجات ──────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ar   TEXT    NOT NULL,
            name_fr   TEXT    NOT NULL,
            price     REAL,
            category  TEXT    NOT NULL
        )
    """)

    # ── جدول الطلبات ───────────────────────────────────────────
    # مصمم ليكون قابلاً للقراءة من تطبيق PyQt الموجود
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT    NOT NULL,
            phone         TEXT    NOT NULL,
            address       TEXT,
            product       TEXT    NOT NULL,
            order_type    TEXT    NOT NULL CHECK(order_type IN ('بيع','تصليح')),
            note          TEXT,
            status        TEXT    NOT NULL DEFAULT 'جديد'
                          CHECK(status IN ('جديد','قيد المعالجة','مكتمل')),
            created_at    TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ── بيانات أولية للمنتجات إذا كان الجدول فارغاً ──────────
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        sample_products = [
            # (name_ar, name_fr, price, category)
            ("حاسوب مكتبي Core i5 الجيل 12", "PC Bureau Core i5 12ème Gen", 85000, "computers"),
            ("حاسوب مكتبي Core i3 الجيل 10", "PC Bureau Core i3 10ème Gen", 55000, "computers"),
            ("لابتوب Core i5 SSD 256Go",      "Laptop Core i5 SSD 256Go",   95000, "computers"),
            ("طابعة HP LaserJet P1102",       "Imprimante HP LaserJet P1102",28000, "printers"),
            ("طابعة Epson L3250 ملونة",       "Imprimante Epson L3250 Couleur",35000,"printers"),
            ("حبر Epson T664 أسود",           "Encre Epson T664 Noir",        800, "ink"),
            ("حبر HP 678 ملون",               "Encre HP 678 Couleur",        1200, "ink"),
            ("لوحة مفاتيح + فأرة",            "Clavier + Souris",            2500, "accessories"),
            ("ذاكرة USB 64Go",                "Clé USB 64Go",                1500, "accessories"),
            ("هارد ديسك خارجي 1To",          "Disque Dur Externe 1To",      8500, "accessories"),
            ("تصليح طابعة",                  "Réparation Imprimante",        None, "repair"),
            ("تصليح حاسوب",                  "Réparation PC",                None, "repair"),
            ("تركيب ويندوز + برامج",         "Installation Windows + Logiciels", None, "repair"),
        ]
        cur.executemany(
            "INSERT INTO products (name_ar, name_fr, price, category) VALUES (?,?,?,?)",
            sample_products
        )

    conn.commit()
    conn.close()


def get_products():
    """جلب كل المنتجات مرتبة حسب الفئة — Retourne tous les produits triés par catégorie"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name_ar, name_fr, price, category FROM products ORDER BY category, name_ar"
    ).fetchall()
    conn.close()
    return rows


def insert_order(customer_name, phone, address, product, order_type, note):
    """حفظ طلب جديد — Enregistre une nouvelle commande"""
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO orders (customer_name, phone, address, product, order_type, note)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (customer_name, phone, address, product, order_type, note or "")
    )
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id


def get_all_orders():
    """جلب كل الطلبات للوحة الإدارة — Retourne toutes les commandes pour l'admin"""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM orders ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return rows


def update_order_status(order_id, new_status):
    """تحديث حالة الطلب — Met à jour le statut d'une commande"""
    conn = get_db()
    conn.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (new_status, order_id)
    )
    conn.commit()
    conn.close()
