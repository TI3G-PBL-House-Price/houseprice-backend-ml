# 🏠 HousePrice Backend & Machine Learning Service

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15_Alpine-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.5.2-F7931E?style=flat&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-2072AF?style=flat&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Pytest-23_Passed-success?style=flat&logo=pytest&logoColor=white)](https://docs.pytest.org/)

Repositori ini memuat implementasi backend RESTful API, orkestrasi basis data PostgreSQL relasional (9 tabel), runtime inferensi *Machine Learning* regresi harga properti DKI Jakarta, dan antarmuka **Web Admin Engineering Console** untuk ekosistem aplikasi **HousePrice** (Proyek *Product-Based Learning* Semester 5 Kelas TI-3G, Politeknik Negeri Malang).

---

## 📌 Daftar Isi
1. [Fitur Utama & Arsitektur](#-fitur-utama--arsitektur)
2. [Prasyarat Sistem (Prerequisites)](#-prasyarat-sistem-prerequisites)
3. [Cara Cepat Menjalankan Proyek (Quick Start)](#-cara-cepat-menjalankan-proyek-quick-start)
4. [Panduan Instalasi Awal (Setup dari Nol)](#-panduan-instalasi-awal-setup-dari-nol)
5. [Menjalankan via Docker Compose](#-menjalankan-via-docker-compose)
6. [Kredensial Default Seeder](#-kredensial-default-seeder)
7. [Daftar Endpoint RESTful API](#-daftar-endpoint-restful-api)
8. [Otomasi Pengujian Mutu (Pytest)](#-otomasi-pengujian-mutu-pytest)
9. [Handover Integrasi Model ML (.pkl)](#-handover-integrasi-model-ml-pkl)
10. [Struktur Direktori Proyek](#-struktur-direktori-proyek)
11. [Tim Pengembang](#-tim-pengembang)

---

## 🚀 Fitur Utama & Arsitektur

* **Flask Application Factory Pattern:** Modularitas kode berbasis `create_app()` pada `app/__init__.py` dengan pemisahan dependensi pada `app/extensions.py`.
* **Strict Gate JWT Authentication:**
  - Enkripsi kata sandi menggunakan Bcrypt dengan *cost factor* 12 (`rounds=12`).
  - Autentikasi stateless menggunakan JSON Web Token (JWT) algoritma HS256 dengan masa aktif terkonfigurasi.
  - Penjagaan rute menggunakan middleware decorator `@token_required`.
* **Skema 9 Tabel Relasional PostgreSQL:**
  - Model relasional lengkap dengan native UUID, *foreign key constraints*, *composite indexes*, *check constraints*, dan *partial unique index* (`idx_ml_models_active`).
  - Manajemen migrasi DDL otomatis menggunakan **Alembic** (`flask db upgrade`).
* **ML Service Layer & Market Heuristics:**
  - Pemuatan artefak biner pipeline Scikit-Learn (`models_artefacts/house_price_xgb_model.pkl`) dengan *in-memory caching*.
  - Mekanisme *fallback* cerdas berbasis statistik rata-rata harga per meter persegi DKI Jakarta saat model biner belum dilatih.
  - Kalkulasi toleransi harga wajar ($\pm 10\%$) dan pencatatan latensi komputasi server ($< 1.500$ ms).
* **Web Admin Engineering Console (`/admin`):**
  - Antarmuka modern bertema *Dark Zinc Engineering Console* dengan font *JetBrains Mono* + *Plus Jakarta Sans*.
  - Pemantauan 4 metrik KPI ($R^2$, MAE, Latensi server, Volume Dataset).
  - 2 grafik interaktif Chart.js dinamis (akurasi model aktif terlatih & sebaran harga pasar per $m^2$ berbasis `MarketStatistic`).
  - *Live Inference Workbench* dengan **Searchable Dropdown Kecamatan** (254 wilayah terfilter dinamis per kota) yang mencatat telemetri ke `prediction_logs`.
  - Format waktu seluruh log telemetri dan audit tersinkronisasi otomatis ke **Waktu Indonesia Barat (WIB / UTC+7)**.
  - Manajemen Unggah Dataset CSV (FR-WEB-03) dengan penentuan rasio *train-test split* dan pratinjau data tabular 10 baris pertama riil dari CSV.
  - Pengalihan model aktif produksi (*switch active model*) dan pencatatan jejak audit aktivitas ke `system_audit_logs`.
* **Arsitektur 100% Bebas Data Dummy:**
  - Seluruh data master wilayah (254 kecamatan), ringkasan statistik pasar (259 entitas), metadata dataset, dan model ML diambil secara murni dan dinamis dari berkas dataset asli (`jakarta_house.csv`) dan berkas model riil (`house_price_xgb_model.pkl` & `hasil_xgb.pkl`).
* **Observabilitas & Pemantauan:**
  - Rute `/health` aktif memverifikasi *heartbeat* koneksi PostgreSQL secara riil.

---

## 💻 Prasyarat Sistem (Prerequisites)

Sebelum menjalankan proyek, pastikan perangkat Anda telah terpasang:
* **Python 3.11 s.d. 3.13** (Dianjurkan Python 3.13)
* **PostgreSQL 15+** atau **Docker Desktop** (untuk menjalankan container database)
* **Git** (CLI version control)

---

## ⚡ Cara Cepat Menjalankan Proyek (Quick Start)

Gunakan 4 langkah praktis ini untuk menjalankan server sehari-hari jika Anda sudah pernah menyelesaikan instalasi awal:

```powershell
# 1. Pastikan aplikasi Docker Desktop sudah dibuka di Windows (Engine running)

# 2. Nyalakan kontainer database PostgreSQL di background
docker-compose up -d db

# 3. Aktifkan virtual environment Python
.\.venv\Scripts\Activate.ps1
# (Atau: .\venv\Scripts\Activate.ps1 jika folder venv Anda bernama venv)

# 4. Jalankan server backend Flask
python run.py
```

Setelah server aktif di `http://127.0.0.1:5000`:
* 🌐 **Web Admin Console:** Akses [http://localhost:5000/admin/login](http://localhost:5000/admin/login) (Kredensial: `admin_hanif` / `Admin@12345`).
* 🩺 **Health Check API:** Akses [http://localhost:5000/health](http://localhost:5000/health) untuk memverifikasi kesiapan server dan database.

> [!NOTE]
> Jika database baru saja dibuat atau datanya kosong, jalankan migrasi dan seeder terlebih dahulu sebelum `python run.py`:
> ```powershell
> flask db upgrade
> python seed.py
> ```

---

## 🛠 Panduan Instalasi Awal (Setup dari Nol)

### Langkah 1: Kloning Repositori
Kloning repositori ini beserta submodule dokumentasinya:
```powershell
git clone --recurse-submodules https://github.com/TI3G-PBL-House-Price/houseprice-backend-ml.git
cd houseprice-backend-ml
```

### Langkah 2: Buat & Aktifkan Virtual Environment
* **Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
* **Linux / macOS (Bash):**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Langkah 3: Instalasi Dependensi
Pasang seluruh paket pustaka Python yang dibutuhkan:
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Langkah 4: Konfigurasi File Environment (`.env`)
Salin file konfigurasi contoh `.env.example` menjadi `.env`:
```powershell
cp .env.example .env
```
Sesuaikan parameter koneksi basis data pada `.env` jika menggunakan konfigurasi non-default:
```ini
FLASK_ENV=development
FLASK_APP=run.py
SECRET_KEY=kunci-rahasia-sesi-admin-minimal-32-karakter-acak
JWT_SECRET_KEY=kunci-jwt-hs256-panjang-dan-sangat-rahasia-minimal-32
JWT_ACCESS_TOKEN_EXPIRES_DAYS=7

DB_HOST=localhost
DB_PORT=5432
DB_NAME=houseprice_db
DB_USER=houseprice_admin
DB_PASSWORD=houseprice_secret_pass

MODEL_PATH=models_artefacts/house_price_xgb_model.pkl
ALLOWED_ORIGINS=*
```

### Langkah 5: Jalankan Basis Data PostgreSQL
Jika menggunakan Docker, jalankan container PostgreSQL secara instan:
```powershell
docker-compose up -d db
```
*(Atau pastikan service PostgreSQL lokal Anda aktif dengan kredensial yang sesuai di `.env`)*.

> [!TIP]
> **Menangani Bentrok Port 5432 (Jika Laptop Memiliki PostgreSQL Lokal):**
> Jika di laptop Anda sudah terpasang PostgreSQL lokal (misal bawaan Windows, Laragon, atau pgAdmin yang sudah memakai port default `5432`), Anda tidak perlu mengubah kode repositori atau `docker-compose.yml`. Cukup sesuaikan parameter `DB_PORT` pada file lokal **`.env`** Anda ke port yang kosong (misal: `5434`):
> ```ini
> DB_PORT=5434
> ```
> Saat menjalankan `docker-compose up -d db`, Docker Compose secara dinamis membaca variabel `${DB_PORT:-5432}` dari file `.env` Anda sehingga port container otomatis terpetakan ke `5434:5432`. Anggota tim lain yang tidak mengalami bentrok tetap dapat menggunakan port default `5432` tanpa saling mengganggu, karena file `.env` bersifat rahasia dan diabaikan oleh Git (`.gitignore`).

### Langkah 6: Jalankan Migrasi Basis Data (Alembic)
Terapkan skema 9 tabel relasional ke basis data PostgreSQL:
```powershell
flask db upgrade
```

### Langkah 7: Jalankan Seeder Basis Data (100% Dinamis)
Inisialisasi basis data secara dinamis dari dataset asli dan model terlatih:
```powershell
python seed.py
```
*(Perintah ini mengekstrak 254 Master Wilayah riil, mengkalkulasi 259 ringkasan statistik pasar langsung dari `jakarta_house.csv`, membaca evaluasi model ML dari `hasil_xgb.pkl`, serta menginisialisasi akun resmi tanpa menyisakan data dummy).*

### Langkah 8: Jalankan Server Pengembangan Flask
Mulai aplikasi backend:
```powershell
python run.py
```
Aplikasi akan aktif di `http://localhost:5000`.

---

## 🐳 Menjalankan via Docker Compose

Untuk menjalankan seluruh stack (PostgreSQL + Flask Backend) secara terisolasi dalam kontainer Docker:

```powershell
# Jalankan seluruh stack
docker-compose up --build -d

# Periksa status kontainer
docker-compose ps

# Eksekusi migrasi & seeding di dalam kontainer
docker-compose exec backend flask db upgrade
docker-compose exec backend python seed.py

# Hentikan stack
docker-compose down
```

---

## 🔑 Kredensial Default Seeder

Setelah menjalankan `python seed.py`, Anda dapat menggunakan akun bawaan berikut untuk pengujian:

### 1. Akun Web Admin Console (`http://localhost:5000/admin/login`)
* **Username / Email:** `admin_hanif` atau `hanif@houseprice.id`
* **Kata Sandi:** `Admin@12345`
* *Tips:* Tersedia tombol cepat **"Isi Otomatis Kredensial Demo"** di halaman login admin untuk kemudahan demonstrasi.

### 2. Akun Pengguna Mobile (Untuk Testing Endpoint API)
* **Akun 1:** `budi.santoso@gmail.com` / `Password123!`
* **Akun 2:** `siti.rahma@gmail.com` / `Password123!`
* **Akun 3:** `kevin.wijaya@gmail.com` / `Password123!`

---

## 📡 Daftar Endpoint RESTful API

Seluruh endpoint di bawah ini mengacu secara ketat pada kontrak spesifikasi OpenAPI 3.0 (`docs/docs/api/openapi.yaml`):

### 🔐 1. Authentication & Profile (`/api/v1/auth`)
| Method | Endpoint | Proteksi | Deskripsi |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/v1/auth/register` | Publik | Registrasi akun pengguna baru (Bcrypt 12 rounds, validasi confirm password). |
| `POST` | `/api/v1/auth/login` | Publik | Otentikasi masuk pengguna & penerbitan Bearer Token JWT (HS256). |
| `GET` | `/api/v1/auth/me` | Bearer Token | Mengambil identitas profil pengguna yang sedang login. |
| `PUT` | `/api/v1/auth/profile` | Bearer Token | Memperbarui nama, telepon, atau alur ganti password (verifikasi sandi lama). |
| `POST` | `/api/v1/auth/fcm-token` | Bearer Token | Menyimpan token perangkat Firebase Cloud Messaging untuk push notification. |
| `POST` | `/api/v1/auth/logout` | Bearer Token | Keluar dari sesi aplikasi mobile dan mengosongkan FCM token. |

### 🧠 2. Prediction & Intelligence (`/api/v1/predict`)
| Method | Endpoint | Proteksi | Deskripsi |
| :---: | :--- | :---: | :--- |
| `POST` | `/api/v1/predict` | Bearer Token | Inferensi estimasi harga properti, kalkulasi rentang wajar $\pm 10\%$, dan rekam telemetri ke `prediction_logs`. |
| `GET` | `/api/v1/predict/history` | Bearer Token | Mengambil riwayat estimasi pengguna aktif (paginasi `limit` & `offset`, isolasi data aman). |

### 📍 3. Master Data & Market Statistics (`/api/v1`)
| Method | Endpoint | Proteksi | Deskripsi |
| :---: | :--- | :---: | :--- |
| `GET` | `/api/v1/locations` | Publik | Data 254 kecamatan riil dikelompokkan ke dalam 5 kota administratif DKI Jakarta. |
| `GET` | `/api/v1/market-statistics` | Publik | Rata-rata harga pasar properti per $m^2$ dengan filter query parameter `?city=` dan `?district=`. |

### 🔔 4. In-App Notifications (`/api/v1/notifications`)
| Method | Endpoint | Proteksi | Deskripsi |
| :---: | :--- | :---: | :--- |
| `GET` | `/api/v1/notifications` | Bearer Token | Mengambil riwayat pesan notifikasi beserta kalkulasi dinamis `unread_count`. |
| `PATCH` | `/api/v1/notifications/<uuid:id>/read` | Bearer Token | Menandai pesan notifikasi telah dibaca (terisolasi per akun pemohon). |

### ⚙️ 5. Monitoring, Health & Web Admin (`/admin` & `/health`)
| Method | Endpoint | Proteksi | Deskripsi |
| :---: | :--- | :---: | :--- |
| `GET` | `/health` | Publik | Healthcheck backend & validasi *heartbeat query* koneksi PostgreSQL (`SELECT 1`). |
| `GET` | `/admin/login` | Publik | Halaman login sesi administrator. |
| `GET` | `/admin/dashboard` | Admin Session | Dashboard pemantauan metrik model ML, visualisasi grafik, workbench, dan penjelajah data. |
| `POST` | `/admin/dataset/upload` | Admin Session | Unggah dataset CSV, penentuan rasio split (80:20, dll), dan pratinjau tabel tabular. |
| `POST` | `/admin/switch-model/<uuid:id>` | Admin Session | Mengalihkan model inferensi aktif produksi. |
| `POST` | `/admin/retrain` | Admin / API | Memicu retraining model (mendukung respon UI Flash & JSON `202 Accepted`). |

---

## 🧪 Otomasi Pengujian Mutu (Pytest)

Pengujian otomatis mencakup seluruh aspek fungsional API, validasi skema masukan (*Boundary Value Analysis*), penolakan tanpa token, isolasi hak akses antarpengguna, operasi Web Admin, hingga pemeriksaan konektivitas database.

Untuk menjalankan seluruh test suite:
```powershell
pytest -v tests/
```

### Hasil Ringkasan Pengujian:
```text
====================== 23 passed, 33 warnings in 19.21s =======================
- tests/test_admin_dataset.py: 4 passed
- tests/test_auth_api.py: 4 passed (termasuk verifikasi healthcheck DB)
- tests/test_market_api.py: 4 passed
- tests/test_notifications_and_profile_api.py: 6 passed
- tests/test_predict_api.py: 5 passed
Tingkat Kelulusan: 100% LULUS (23 dari 23 skenario uji)
```

---

## 📦 Handover Integrasi Model ML (.pkl)

Layer `MLService` pada `app/services/ml_service.py` telah dirancang bersifat modular dan *plug-and-play*:

1. Model terbaik hasil eksperimen repositori `ml-model-testing` menggunakan algoritma **XGBoost Regressor (Tuned dengan GridSearchCV)** dengan performa testing $R^2 = 83{,}08\%$, MAE = $0{,}2230$, dan RMSE = $0{,}3350$.
2. Pipeline biner model lengkap (termasuk *ColumnTransformer* One-Hot Encoding dan regressor XGBoost) tersimpan pada direktori:
   ```text
   models_artefacts/house_price_xgb_model.pkl
   models_artefacts/hasil_xgb.pkl
   ```
3. Saat aplikasi Flask dijalankan, `MLService` otomatis mendeteksi dan memuat berkas biner tersebut. `MLService` juga secara cerdas mendeteksi skala logaritmik $\log(1 + \text{harga})$ dan melakukan konversi kembali ke nominal Rupiah asli menggunakan $\exp(y) - 1$ (`np.expm1`).
4. Jika berkas model tidak ditemukan atau mengalami kendala masukan tak lazim, `MLService` secara otomatis beralih (*graceful fallback*) ke kalkulasi estimasi harga berbasis agregasi statistik pasar per meter persegi DKI Jakarta.

---

## 📂 Struktur Direktori Proyek

```text
houseprice-backend-ml/
├── .github/                  # Konfigurasi otomasi CI/CD GitHub Actions
│   └── workflows/
│       └── backend-ci.yml    # Pipeline otomatis linter (flake8), database, & pytest
├── app/
│   ├── blueprints/           # Modular route controllers
│   │   ├── admin/            # Web Admin console (/admin)
│   │   ├── auth/             # Autentikasi JWT & profil (/api/v1/auth)
│   │   ├── market/           # Master lokasi & statistik pasar (/api/v1)
│   │   ├── notifications/    # Notifikasi in-app (/api/v1/notifications)
│   │   └── predict/          # Inferensi ML & riwayat (/api/v1/predict)
│   ├── middlewares/          # Security & JWT guards (@token_required)
│   ├── models/               # SQLAlchemy PostgreSQL schema models (9 tabel)
│   ├── services/             # ML runtime & business service (MLService)
│   ├── templates/admin/      # Antarmuka Web Admin (login.html, dashboard.html)
│   ├── __init__.py           # Flask Application Factory (create_app)
│   ├── config.py             # Konfigurasi environment & secrets
│   └── extensions.py         # Ekstensi SQLAlchemy, Bcrypt, Migrate, CORS
├── docs/                     # Submodule Git dokumentasi PBL (PRD, OpenAPI, dll)
├── migrations/               # Berkas migrasi DDL Alembic
├── models_artefacts/         # Direktori penyimpanan biner model & evaluasi ML
├── tests/                    # Pytest automated test suites (23 test cases)
├── uploads/datasets/         # Direktori penyimpanan unggahan dataset CSV
├── .env.example              # Template variabel lingkungan publik
├── .gitignore                # Aturan penyaringan file sensitif Git
├── docker-compose.yml        # Orkestrasi Docker multi-service (db & backend)
├── Dockerfile                # Konfigurasi container Gunicorn Flask
├── README.md                 # Panduan instalasi dan dokumentasi teknis ini
├── requirements.txt          # Daftar dependensi paket Python
├── run.py                    # Entrypoint eksekusi lokal server Flask
└── seed.py                   # Skrip seeder mandiri 9 tabel basis data
```

---

## 👥 Tim Pengembang (PBL TI-3G Polinema)

* **Abdul Rahman Hanif Darmawan (@abdulrahmanhanif)** — *Project Manager, QA Integration, Backend & Database Lead*
* **Muhammad Nuril Huda (@nurilhuda)** — *Machine Learning & Networking Engineer*
* **Naufal Abid Aurizky (@naufalabid)** — *Data Preprocessing & Business Logic Engineer*
* **Nurfinka Lailasari (@nurfinkalailasari)** — *QA Lead & Local Storage Engineer*
* **Jasmine Nasywa Nabilah (@jasminenasywa)** — *Mobile UI Designer & Slicing Engineer*

---

<p align="center">
  <b>HousePrice Ecosystem</b> • Dibuat untuk memenuhi evaluasi Proyek Berbasis Produk (PBL) Semester 5<br>
  Jurusan Teknologi Informasi — <b>Politeknik Negeri Malang</b>
</p>
