"""
app.py — TADJ-INFO Flask app (static-style, no database)
Products are loaded client-side from Google Sheets CSV via products.js
Deployed on Vercel via api/index.py
"""

import os
from flask import Flask, render_template

app = Flask(__name__)  # templates/ and static/ are siblings of app.py


@app.route("/")
def index():
    return render_template("index.html")


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
