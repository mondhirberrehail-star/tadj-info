# TADJ-INFO — موقع المتجر الإلكتروني

**متجر حواسيب وطابعات — تاجنانت، ميلة، الجزائر**

---

## 📦 محتوى المشروع

```
tadj-info/
├── app.py                     # التطبيق الرئيسي Flask
├── database.py                # إدارة قاعدة البيانات SQLite
├── requirements.txt           # مكتبات Python
├── pyqt_integration_example.py # ربط تطبيق الديسكتوب
├── templates/
│   ├── base.html              # القالب الأساسي
│   ├── index.html             # الصفحة الرئيسية
│   ├── admin.html             # لوحة الإدارة
│   └── admin_login.html       # صفحة الدخول
└── static/
    ├── css/style.css          # التصميم الكامل
    ├── js/main.js             # JavaScript
    ├── manifest.json          # إعدادات PWA
    ├── sw.js                  # Service Worker
    └── icons/                 # أيقونات PWA (أضف icon-192.png و icon-512.png)
```

---

## 🚀 التثبيت والتشغيل محلياً

### 1. تثبيت Python

تأكد من تثبيت **Python 3.10+** على جهازك.  
للتحقق: `python --version`

### 2. إنشاء بيئة افتراضية (مستحسن)

```bash
# في مجلد المشروع
python -m venv venv

# تفعيل البيئة
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate
```

### 3. تثبيت المكتبات

```bash
pip install -r requirements.txt
```

### 4. تشغيل الموقع

```bash
python app.py
```

افتح المتصفح على: **http://localhost:5000**

### 5. لوحة الإدارة

الرابط: **http://localhost:5000/admin**  
كلمة المرور الافتراضية: `tadj2024`

لتغيير كلمة المرور، ضع متغير بيئي:
```bash
# Windows (PowerShell):
$env:ADMIN_PASSWORD = "كلمتك_السرية_الجديدة"

# Linux / macOS:
export ADMIN_PASSWORD="كلمتك_السرية_الجديدة"
```

---

## 🔗 الربط مع تطبيق الديسكتوب (PyQt6/PySide6)

### الطريقة الأولى: ملف SQLite مشترك (نفس الجهاز — الأسهل)

```python
# في ملف pyqt_integration_example.py
WEBSITE_DB_PATH = Path(r"C:\path\to\tadj-info\tadj_info.db")
```

- شغّل موقع Flask وتطبيق الديسكتوب على نفس الجهاز
- كلاهما يقرآن/يكتبان في نفس الملف `tadj_info.db`
- الملف يستخدم **WAL mode** لتجنب التعارض بين القراءة والكتابة

```bash
python pyqt_integration_example.py
```

### الطريقة الثانية: API عبر الشبكة (الموقع على الإنترنت)

```python
# في pyqt_integration_example.py
API_BASE_URL = "https://your-app.onrender.com"
```

ستحتاج لإضافة endpoint في `app.py` لإرجاع الطلبات بصيغة JSON:

```python
@app.route("/api/orders", methods=["GET"])
@login_required  # أو استخدم API key
def api_get_orders():
    status = request.args.get("status", "")
    orders = get_all_orders()
    if status:
        orders = [o for o in orders if o["status"] == status]
    return jsonify([dict(o) for o in orders])
```

---

## 🌐 النشر على الإنترنت

### الخيار أ: Render.com (مجاني)

1. ارفع الكود على **GitHub** (repository جديد)
2. اذهب إلى [render.com](https://render.com) → New → Web Service
3. اربطه بـ repository الخاص بك
4. اضبط:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment Variables:**
     - `SECRET_KEY` = (مفتاح عشوائي طويل)
     - `ADMIN_PASSWORD` = (كلمة مرورك)
5. اضغط **Deploy**

> ⚠️ في الخطة المجانية على Render، قاعدة البيانات مؤقتة. لحفظ البيانات بشكل دائم، استخدم Render Disk أو انتقل للخيار ب.

### الخيار ب: PythonAnywhere (مستحسن للمبتدئين)

1. سجّل في [pythonanywhere.com](https://www.pythonanywhere.com) (الخطة المجانية تكفي)
2. من Dashboard → **Files** → ارفع جميع ملفات المشروع
3. من **Web** → Add New Web App:
   - اختر **Flask**
   - اضبط مسار `app.py`
4. في ملف WSGI، اضبط:
   ```python
   import sys
   sys.path.insert(0, '/home/YOUR_USERNAME/tadj-info')
   from app import app as application
   ```
5. اضغط **Reload**

### الخيار ج: Railway.app

```bash
# تثبيت Railway CLI
npm i -g @railway/cli
railway login
railway init
railway up
```

---

## 📱 إضافة الموقع لشاشة الهاتف (PWA)

### أندرويد (Chrome):
1. افتح الموقع في Chrome
2. اضغط على القائمة (⋮) → **إضافة إلى الشاشة الرئيسية**
3. اضغط **إضافة** — سيظهر الموقع كتطبيق

### iPhone (Safari):
1. افتح الموقع في Safari
2. اضغط **مشاركة** (الزر السفلي) → **إضافة إلى الشاشة الرئيسية**
3. اضغط **إضافة**

### للحصول على تجربة تثبيت كاملة، أضف الأيقونات:
- ضع ملفي `icon-192.png` و `icon-512.png` في مجلد `static/icons/`
- الأيقونة يجب أن تكون مربعة (192×192 و 512×512 بكسل)

---

## 🔧 إعدادات متقدمة

### تغيير مسار قاعدة البيانات

```bash
export DB_PATH="/path/to/shared/tadj_info.db"
python app.py
```

### تشغيل بـ Gunicorn (للإنتاج)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### متغيرات البيئة المتاحة

| المتغير | الوصف | الافتراضي |
|---------|-------|-----------|
| `SECRET_KEY` | مفتاح تشفير الجلسات | `tadj-info-change-me-in-production` |
| `ADMIN_PASSWORD` | كلمة مرور لوحة الإدارة | `tadj2024` |
| `DB_PATH` | مسار ملف SQLite | `tadj_info.db` (بجانب app.py) |
| `FLASK_DEBUG` | وضع التطوير (0/1) | `1` |

---

## 📞 الدعم

- **الهاتف:** 0550 24 99 81  
- **واتساب:** [wa.me/213550249981](https://wa.me/213550249981)  
- **العنوان:** حي 533 مسكن، تاجنانت، ميلة، الجزائر
