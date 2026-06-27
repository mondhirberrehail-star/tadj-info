"""
pyqt_integration_example.py
════════════════════════════════════════════════════════════════════
مثال توضيحي: كيف يقرأ تطبيق PyQt6/PySide6 الطلبات الواردة من الموقع
Exemple: comment l'appli PyQt6/PySide6 lit les commandes du site web

طريقتان للتكامل:
  1. ملف SQLite مشترك على نفس الجهاز (الأسهل)
  2. استدعاء API عبر الشبكة (للنشر على الإنترنت)

Deux modes d'intégration:
  1. Fichier SQLite partagé sur la même machine (le plus simple)
  2. Appel API réseau (pour hébergement distant)
════════════════════════════════════════════════════════════════════
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# ── تجربة PyQt6 ثم PySide6 ──────────────────────────────────────
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTableWidget, QTableWidgetItem, QLabel, QPushButton, QComboBox,
        QHeaderView, QStatusBar, QTabWidget, QLineEdit, QMessageBox,
        QFrame, QSizePolicy,
    )
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
    from PyQt6.QtGui import QColor, QFont, QPalette
    PYQT = 6
except ImportError:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTableWidget, QTableWidgetItem, QLabel, QPushButton, QComboBox,
        QHeaderView, QStatusBar, QTabWidget, QLineEdit, QMessageBox,
        QFrame, QSizePolicy,
    )
    from PySide6.QtCore import Qt, QTimer, QThread, Signal as pyqtSignal
    from PySide6.QtGui import QColor, QFont, QPalette
    PYQT = 6


# ════════════════════════════════════════════════════════════════
#  الإعدادات — Configuration
# ════════════════════════════════════════════════════════════════

# ── المسار إلى قاعدة بيانات الموقع (نفس الجهاز) ────────────────
# غيّر هذا المسار إلى موقع ملف tadj_info.db على جهازك
WEBSITE_DB_PATH = Path(__file__).parent / "tadj_info.db"

# ── أو: رابط API إذا كان الموقع منشوراً على الإنترنت ────────────
# API_BASE_URL = "https://your-app.onrender.com"
API_BASE_URL = "http://localhost:5000"

# تحديث تلقائي كل كم ثانية — rafraîchissement automatique (secondes)
AUTO_REFRESH_SECONDS = 30


# ════════════════════════════════════════════════════════════════
#  طبقة الوصول للبيانات — Data Access Layer
# ════════════════════════════════════════════════════════════════

class OrdersDB:
    """قراءة الطلبات من ملف SQLite المشترك — Lecture depuis SQLite partagé"""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # WAL يسمح للقراءة أثناء كتابة Flask
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def get_orders(self, status_filter: str = "") -> list[dict]:
        """جلب الطلبات، مع إمكانية التصفية حسب الحالة"""
        if not self.db_path.exists():
            return []
        conn = self._connect()
        try:
            query = "SELECT * FROM orders"
            params = []
            if status_filter:
                query += " WHERE status = ?"
                params.append(status_filter)
            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_status(self, order_id: int, new_status: str) -> bool:
        """تحديث حالة الطلب من تطبيق الديسكتوب"""
        valid = ("جديد", "قيد المعالجة", "مكتمل")
        if new_status not in valid:
            return False
        conn = self._connect()
        try:
            conn.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
            conn.commit()
            return True
        finally:
            conn.close()

    def count_by_status(self) -> dict:
        """إحصاء الطلبات حسب الحالة"""
        if not self.db_path.exists():
            return {}
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM orders GROUP BY status"
            ).fetchall()
            return {r["status"]: r["cnt"] for r in rows}
        finally:
            conn.close()


class OrdersAPI:
    """جلب الطلبات عبر HTTP API — Récupération via API HTTP"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def get_orders(self, status_filter: str = "") -> list[dict]:
        """
        مثال: GET /api/orders?status=جديد
        ستحتاج لإضافة هذا الـ endpoint في app.py
        """
        import urllib.request
        import urllib.parse
        params = {}
        if status_filter:
            params["status"] = status_filter
        url = self.base_url + "/api/orders"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                return json.loads(r.read())
        except Exception as e:
            print(f"API error: {e}")
            return []

    def update_status(self, order_id: int, new_status: str) -> bool:
        import urllib.request
        import urllib.parse
        data = urllib.parse.urlencode({
            "order_id": order_id,
            "status":   new_status,
        }).encode()
        try:
            req = urllib.request.Request(
                self.base_url + "/api/orders/status",
                data=data, method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read()).get("success", False)
        except Exception as e:
            print(f"API error: {e}")
            return False


# ════════════════════════════════════════════════════════════════
#  واجهة PyQt — Interface PyQt
# ════════════════════════════════════════════════════════════════

STATUS_COLORS = {
    "جديد":          "#1E9FE0",
    "قيد المعالجة": "#f59e0b",
    "مكتمل":         "#22c55e",
}
COLUMNS = ["#", "الاسم", "الهاتف", "المنتج / الخدمة", "النوع", "الحالة", "التاريخ", "ملاحظة"]


class OrdersWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TADJ-INFO — طلبات الموقع")
        self.resize(1100, 700)

        # استخدم DB المحلي إذا موجود، وإلا API
        if WEBSITE_DB_PATH.exists():
            self.backend = OrdersDB(WEBSITE_DB_PATH)
            mode = f"قاعدة بيانات محلية: {WEBSITE_DB_PATH}"
        else:
            self.backend = OrdersAPI(API_BASE_URL)
            mode = f"API: {API_BASE_URL}"

        self._build_ui()
        self.statusBar().showMessage(f"الوضع: {mode}")
        self.refresh()

        # تحديث تلقائي
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(AUTO_REFRESH_SECONDS * 1000)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Header row ──
        header = QHBoxLayout()
        title = QLabel("📋  طلبات موقع TADJ-INFO")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        header.addWidget(title)
        header.addStretch()

        # فلتر الحالة
        self.status_filter = QComboBox()
        self.status_filter.addItems(["الكل", "جديد", "قيد المعالجة", "مكتمل"])
        self.status_filter.currentTextChanged.connect(self.refresh)
        header.addWidget(QLabel("تصفية:"))
        header.addWidget(self.status_filter)

        refresh_btn = QPushButton("🔄  تحديث")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # ── Stats bar ──
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666; font-size:12px;")
        layout.addWidget(self.stats_label)

        # ── Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # ── Status update row ──
        update_row = QHBoxLayout()
        update_row.addWidget(QLabel("تغيير حالة الطلب المحدد:"))
        self.new_status_combo = QComboBox()
        self.new_status_combo.addItems(["جديد", "قيد المعالجة", "مكتمل"])
        update_row.addWidget(self.new_status_combo)
        save_btn = QPushButton("💾  حفظ")
        save_btn.clicked.connect(self.update_selected_status)
        update_row.addWidget(save_btn)
        update_row.addStretch()
        layout.addLayout(update_row)

    def refresh(self):
        chosen = self.status_filter.currentText()
        status_filter = "" if chosen == "الكل" else chosen
        orders = self.backend.get_orders(status_filter)
        self._populate_table(orders)

        # إحصاءات
        if hasattr(self.backend, 'count_by_status'):
            counts = self.backend.count_by_status()
            total = sum(counts.values())
            new_c = counts.get("جديد", 0)
            self.stats_label.setText(
                f"المجموع: {total}  |  جديد: {new_c}  |  "
                f"قيد المعالجة: {counts.get('قيد المعالجة', 0)}  |  "
                f"مكتمل: {counts.get('مكتمل', 0)}  "
                f"— آخر تحديث: {datetime.now().strftime('%H:%M:%S')}"
            )

    def _populate_table(self, orders: list[dict]):
        self.table.setRowCount(len(orders))
        self._order_ids = []
        for row, o in enumerate(orders):
            self._order_ids.append(o["id"])
            vals = [
                str(o["id"]),
                o["customer_name"],
                o["phone"],
                o["product"],
                o["order_type"],
                o["status"],
                o.get("created_at", "")[:16],
                o.get("note", "") or "",
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                # لون الحالة
                if col == 5:
                    color = STATUS_COLORS.get(val, "#aaa")
                    item.setForeground(QColor(color))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.table.setItem(row, col, item)

    def update_selected_status(self):
        rows = self.table.selectedItems()
        if not rows:
            QMessageBox.information(self, "تنبيه", "يرجى تحديد طلب أولاً")
            return
        row = self.table.currentRow()
        order_id   = self._order_ids[row]
        new_status = self.new_status_combo.currentText()
        ok = self.backend.update_status(order_id, new_status)
        if ok:
            QMessageBox.information(self, "✓", f"تم تحديث حالة الطلب #{order_id} إلى: {new_status}")
            self.refresh()
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم التحديث، تحقق من الاتصال")


# ════════════════════════════════════════════════════════════════
#  التشغيل — Lancement
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setStyle("Fusion")

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(22, 27, 37))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(232, 237, 245))
    palette.setColor(QPalette.ColorRole.Base,            QColor(13, 17, 23))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(26, 34, 51))
    palette.setColor(QPalette.ColorRole.Text,            QColor(232, 237, 245))
    palette.setColor(QPalette.ColorRole.Button,          QColor(11, 77, 162))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(30, 159, 224))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    win = OrdersWindow()
    win.show()
    sys.exit(app.exec())
