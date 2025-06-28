# mHealth – Multi‑Signal Health Monitoring Platform

> **Physiological signals · Secure by design · Research‑grade analytics**

mHealth is a full-stack, research-grade health data platform that allows the seamless ingestion, storage, analysis, and visualization of physiological signals like PPG (heart activity), GSR (stress level), and actigraphy (motion/sleep cycle). Built at IIIT-Delhi, it combines custom hardware with a Django-powered backend and interactive dashboards. It enables researchers and clinicians to extract meaningful insights from raw biosensor data while ensuring user consent, data security, and medical compliance.

---

## 🧾 Summary

- Real-time sensor data is streamed to the backend via Wi-Fi from wearable hardware.
- A user-friendly web interface allows onboarding, consent handling, and data uploads.
- Users can visualize their signals through interactive graphs and download standardized HL7 medical data.
- The system includes optimizations for large-scale datasets (200,000+ rows) and complies with HIPAA and GDPR.
- Secure architecture includes AES encryption, TLS transmission, role-based access, and consent gating.

---

## 🖥️ Application Pages in Detail

### 🏠 Home Page
After login, users land on the central dashboard or "Home Page." This is a control hub that:
- Displays a summary of uploaded files with timestamps
- Provides shortcuts to upload new data
- Links to PPG, GSR, actigraphy graphs, HL7 export, and file viewing options
- Presents user-specific views (based on role — Admin, Researcher, User)

---

### 🔐 Login and Sign-Up Page
- Sign-up form that enforces strong passwords and validates unique usernames
- Login form that verifies credentials securely via Django authentication
- Redirect to consent form on first sign-up

---

### 📝 Consent Form Page
- Explains how physiological data will be used
- Requires agreement to proceed further
- Consent status stored securely

---

### 📤 File Upload Page
- Uploads CSV or links to Google Sheets
- Assigns internal filename
- Automatically organizes files per user

---

### 🗂️ Uploaded Files Page
- Lists all uploaded files with timestamps
- Allows actions: view raw sheet, visualize signals, view/download HL7

---

### 📊 PPG Visualization Page
- Day-wise PPG trends
- Zoom, pan, batch rendering for performance
- Helps track cardiovascular metrics

---

### 📈 GSR Visualization Page
- Time-series of GSR (stress) readings
- Filters by time range
- Multi-day anomaly detection

---

### 💤 Actigraphy Visualization Page
- Motion/rest cycle graphs
- Highlights periods of rest vs movement
- Supports sleep tracking

---

### 📉 Compact Multi-Signal View Page
- Combined GSR, PPG, and Actigraphy in one view
- Toggle signals on/off
- Best for correlation analysis

---

### 📄 HL7 Data View Page
- Shows standardized medical data format
- Includes PID and OBX segments
- Timestamped entries for clinical use

---

### 📋 Raw Data Sheet Viewer Page
- Tabular view of uploaded data
- Search and scroll through original values

---

## ⚙️ Installation and Setup

### 1. Clone the Repository
```bash
git clone https://github.com/YourUser/mhealth-django.git
cd mhealth-django
```

---

### 2. Create Virtual Environment and Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

### 3. Set Up the Database

Edit `mhealth/settings.py`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",  # or "sqlite3"
        "NAME": "mhealth_db",
        "USER": "your_db_user",
        "PASSWORD": "your_db_password",
        "HOST": "localhost",
        "PORT": "3306",
    }
}
```

Or keep the default SQLite database for quick local testing.

---

### 4. Apply Migrations
```bash
python manage.py migrate
```

---

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

Follow the prompts to set username and password.

---

### 6. Run the Development Server
```bash
python manage.py runserver
```

Open in your browser: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---
