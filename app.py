"""
app.py — TADJ-INFO Flask app (static-style, no database)
Deployed on Vercel via api/index.py
"""

import os
from flask import Flask, render_template

app = Flask(__name__)  # templates/ and static/ are siblings of app.py

# Product catalogue — static list (no DB needed)
PRODUCTS = [
    {"name_ar": "حاسوب مكتبي Core i5 الجيل 12", "name_fr": "PC Bureau Core i5 12ème Gen", "price": 85000, "category": "computers"},
    {"name_ar": "حاسوب مكتبي Core i3 الجيل 10", "name_fr": "PC Bureau Core i3 10ème Gen", "price": 55000, "category": "computers"},
    {"name_ar": "لابتوب Core i5 SSD 256Go",       "name_fr": "Laptop Core i5 SSD 256Go",   "price": 95000, "category": "computers"},
    {"name_ar": "طابعة HP LaserJet P1102",         "name_fr": "Imprimante HP LaserJet P1102","price": 28000, "category": "printers"},
    {"name_ar": "طابعة Epson L3250 ملونة",         "name_fr": "Imprimante Epson L3250 Couleur","price": 35000,"category": "printers"},
    {"name_ar": "حبر Epson T664 أسود",             "name_fr": "Encre Epson T664 Noir",       "price": 800,  "category": "ink"},
    {"name_ar": "حبر HP 678 ملون",                 "name_fr": "Encre HP 678 Couleur",        "price": 1200, "category": "ink"},
    {"name_ar": "لوحة مفاتيح + فأرة",              "name_fr": "Clavier + Souris",            "price": 2500, "category": "accessories"},
    {"name_ar": "ذاكرة USB 64Go",                  "name_fr": "Clé USB 64Go",                "price": 1500, "category": "accessories"},
    {"name_ar": "هارد ديسك خارجي 1To",            "name_fr": "Disque Dur Externe 1To",      "price": 8500, "category": "accessories"},
    {"name_ar": "تصليح طابعة",                    "name_fr": "Réparation Imprimante",        "price": None, "category": "repair"},
    {"name_ar": "تصليح حاسوب",                    "name_fr": "Réparation PC",                "price": None, "category": "repair"},
    {"name_ar": "تركيب ويندوز + برامج",           "name_fr": "Installation Windows + Logiciels","price": None,"category": "repair"},
]


@app.route("/")
def index():
    categories = {}
    for p in PRODUCTS:
        categories.setdefault(p["category"], []).append(p)
    return render_template("index.html", products=PRODUCTS, categories=categories)


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
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
