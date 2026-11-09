import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Pastikan UTF-8 encoding untuk output Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app import create_app
from app.extensions import db, bcrypt
from app.models import (
    Admin,
    User,
    MasterLocation,
    MarketStatistic,
    DatasetMetadata,
    MLModel,
    PredictionLog,
    Notification,
    SystemAuditLog,
)

def seed_database():
    app = create_app()
    with app.app_context():
        print("[SEED] Memulai proses seeding database HousePrice...")

        # 1. SEED ADMINS
        admin = Admin.query.filter_by(email="hanif@houseprice.id").first()
        if not admin:
            admin = Admin(
                id=uuid.uuid4(),
                username="admin_hanif",
                email="hanif@houseprice.id",
                password_hash=bcrypt.generate_password_hash("Admin123!", rounds=12).decode("utf-8"),
                full_name="Abdul Rahman Hanif Darmawan",
                is_active=True,
            )
            db.session.add(admin)
            db.session.commit()
            print("  [OK] Admin default (admin_hanif) berhasil dibuat.")
        else:
            print("  [INFO] Admin default sudah ada.")

        # 2. SEED USERS (Mobile Users)
        user1 = User.query.filter_by(email="budi.santoso@gmail.com").first()
        if not user1:
            user1 = User(
                id=uuid.uuid4(),
                full_name="Budi Santoso",
                email="budi.santoso@gmail.com",
                password_hash=bcrypt.generate_password_hash("Password123!", rounds=12).decode("utf-8"),
                phone_number="081234567890",
                is_active=True,
            )
            db.session.add(user1)

        user2 = User.query.filter_by(email="siti.rahma@gmail.com").first()
        if not user2:
            user2 = User(
                id=uuid.uuid4(),
                full_name="Siti Rahma",
                email="siti.rahma@gmail.com",
                password_hash=bcrypt.generate_password_hash("Password123!", rounds=12).decode("utf-8"),
                phone_number="081987654321",
                is_active=True,
            )
            db.session.add(user2)

        user3 = User.query.filter_by(email="kevin.wijaya@gmail.com").first()
        if not user3:
            user3 = User(
                id=uuid.uuid4(),
                full_name="Kevin Wijaya",
                email="kevin.wijaya@gmail.com",
                password_hash=bcrypt.generate_password_hash("Password123!", rounds=12).decode("utf-8"),
                phone_number="085712345678",
                is_active=True,
            )
            db.session.add(user3)
        db.session.commit()
        print("  [OK] User mobile sampel berhasil diverifikasi.")

        # 3. SEED MASTER LOCATIONS (5 Kota Administrasi DKI Jakarta & Kecamatan)
        locations_data = [
            # Jakarta Selatan
            ("Jakarta Selatan", "Kebayoran Baru"),
            ("Jakarta Selatan", "Kebayoran Lama"),
            ("Jakarta Selatan", "Cilandak"),
            ("Jakarta Selatan", "Pesanggrahan"),
            ("Jakarta Selatan", "Pasar Minggu"),
            ("Jakarta Selatan", "Jagakarsa"),
            ("Jakarta Selatan", "Mampang Prapatan"),
            ("Jakarta Selatan", "Pancoran"),
            ("Jakarta Selatan", "Tebet"),
            ("Jakarta Selatan", "Setiabudi"),
            # Jakarta Barat
            ("Jakarta Barat", "Citra Garden"),
            ("Jakarta Barat", "Cengkareng"),
            ("Jakarta Barat", "Grogol Petamburan"),
            ("Jakarta Barat", "Taman Sari"),
            ("Jakarta Barat", "Tambora"),
            ("Jakarta Barat", "Kebon Jeruk"),
            ("Jakarta Barat", "Kalideres"),
            ("Jakarta Barat", "Palmerah"),
            ("Jakarta Barat", "Kembangan"),
            ("Jakarta Barat", "Puri Indah"),
            # Jakarta Pusat
            ("Jakarta Pusat", "Menteng"),
            ("Jakarta Pusat", "Gambir"),
            ("Jakarta Pusat", "Tanah Abang"),
            ("Jakarta Pusat", "Senen"),
            ("Jakarta Pusat", "Cempaka Putih"),
            ("Jakarta Pusat", "Johar Baru"),
            ("Jakarta Pusat", "Kemayoran"),
            ("Jakarta Pusat", "Sawah Besar"),
            # Jakarta Timur
            ("Jakarta Timur", "Matraman"),
            ("Jakarta Timur", "Pulo Gadung"),
            ("Jakarta Timur", "Jatinegara"),
            ("Jakarta Timur", "Duren Sawit"),
            ("Jakarta Timur", "Kramat Jati"),
            ("Jakarta Timur", "Makasar"),
            ("Jakarta Timur", "Pasar Rebo"),
            ("Jakarta Timur", "Ciracas"),
            ("Jakarta Timur", "Cipayung"),
            ("Jakarta Timur", "Cakung"),
            # Jakarta Utara
            ("Jakarta Utara", "Kelapa Gading"),
            ("Jakarta Utara", "Tanjung Priok"),
            ("Jakarta Utara", "Koja"),
            ("Jakarta Utara", "Cilincing"),
            ("Jakarta Utara", "Pademangan"),
            ("Jakarta Utara", "Penjaringan"),
            ("Jakarta Utara", "Pluit"),
            ("Jakarta Utara", "Sunter"),
        ]

        if MasterLocation.query.count() == 0:
            for city, district in locations_data:
                loc = MasterLocation(city=city, district=district, is_active=True)
                db.session.add(loc)
            db.session.commit()
            print(f"  [OK] {len(locations_data)} Master Wilayah DKI Jakarta berhasil diisi.")
        else:
            print("  [INFO] Master Wilayah sudah terisi.")

        # 4. SEED MARKET STATISTICS
        market_stats_data = [
            ("Jakarta Selatan", None, 3850000000.00, 24500000.00, 155.00, 180.00, 1420),
            ("Jakarta Barat", None, 2450000000.00, 18500000.00, 125.50, 140.00, 1150),
            ("Jakarta Pusat", None, 4200000000.00, 28000000.00, 140.00, 165.00, 780),
            ("Jakarta Timur", None, 1850000000.00, 14200000.00, 118.00, 120.00, 1260),
            ("Jakarta Utara", None, 2950000000.00, 21000000.00, 135.00, 150.00, 890),
            ("Jakarta Barat", "Citra Garden", 2650000000.00, 19200000.00, 130.00, 145.00, 210),
            ("Jakarta Selatan", "Tebet", 3400000000.00, 23500000.00, 140.00, 160.00, 185),
            ("Jakarta Utara", "Kelapa Gading", 3650000000.00, 24000000.00, 150.00, 175.00, 240),
            ("Jakarta Pusat", "Menteng", 8500000000.00, 38500000.00, 220.00, 260.00, 95),
        ]

        if MarketStatistic.query.count() == 0:
            for city, dist, price, price_sqm, surf, bld, total in market_stats_data:
                ms = MarketStatistic(
                    city=city,
                    district=dist,
                    avg_price=price,
                    avg_price_per_sqm=price_sqm,
                    avg_surface_area=surf,
                    avg_building_area=bld,
                    total_properties=total,
                )
                db.session.add(ms)
            db.session.commit()
            print(f"  [OK] {len(market_stats_data)} Statistik Pasar properti berhasil diisi.")
        else:
            print("  [INFO] Statistik Pasar sudah terisi.")

        # 5. SEED DATASET METADATA
        if DatasetMetadata.query.count() == 0:
            dataset = DatasetMetadata(
                id=uuid.uuid4(),
                file_name="jakarta_house_v1.csv",
                file_path="/uploads/datasets/jakarta_house_v1.csv",
                total_records=10000,
                file_size_bytes=845620,
                uploaded_by=admin.id,
            )
            db.session.add(dataset)
            db.session.commit()
            print("  [OK] Metadata dataset properti berhasil dicatat.")

        # 6. SEED ML MODELS
        if MLModel.query.count() == 0:
            # Model Aktif: XGBoost Regressor (Tuned dengan GridSearchCV)
            xgb_model = MLModel(
                id=uuid.uuid4(),
                model_name="XGBoost Regressor (Tuned)",
                version="v1.0.0",
                model_file_path="models_artefacts/model.pkl",
                algorithm_type="XGBoost + GridSearchCV",
                r2_score=0.8310,
                mae_score=0.2230,
                rmse_score=0.3350,
                is_active=True,
                trained_by=admin.id,
            )
            db.session.add(xgb_model)

            # Model Pembanding: Baseline Linear Regression
            lr_model = MLModel(
                id=uuid.uuid4(),
                model_name="Multiple Linear Regression",
                version="v0.9.0",
                model_file_path="models_artefacts/linear_baseline.pkl",
                algorithm_type="Linear",
                r2_score=0.6840,
                mae_score=1680500200.00,
                rmse_score=2450120000.00,
                is_active=False,
                trained_by=admin.id,
            )
            db.session.add(lr_model)
            db.session.commit()
            print("  [OK] Registri model ML (XGBoost v1.0.0 & Linear v0.9.0) berhasil disimpan.")

        # 7. SEED PREDICTION LOGS
        if PredictionLog.query.count() == 0:
            now = datetime.now(timezone.utc)
            sample_logs = [
                (user1.id, "Jakarta Barat", "Citra Garden", 130.0, 145.0, 3, 2, 1, 2650000000.00, "v1.0.0", 112, "182.253.120.45", now - timedelta(hours=2)),
                (user1.id, "Jakarta Selatan", "Tebet", 140.0, 160.0, 4, 3, 2, 3450000000.00, "v1.0.0", 124, "182.253.120.45", now - timedelta(hours=5)),
                (user2.id, "Jakarta Utara", "Kelapa Gading", 150.0, 180.0, 4, 3, 2, 3700000000.00, "v1.0.0", 118, "114.124.210.15", now - timedelta(hours=14)),
                (user2.id, "Jakarta Barat", "Cengkareng", 90.0, 75.0, 2, 1, 1, 1450000000.00, "v1.0.0", 108, "114.124.210.15", now - timedelta(days=1)),
                (user3.id, "Jakarta Selatan", "Cilandak", 200.0, 240.0, 5, 4, 2, 5200000000.00, "v1.0.0", 132, "36.85.102.77", now - timedelta(days=1, hours=4)),
                (user3.id, "Jakarta Pusat", "Menteng", 250.0, 300.0, 5, 5, 3, 9800000000.00, "v1.0.0", 145, "36.85.102.77", now - timedelta(days=2)),
                (None, "Jakarta Timur", "Duren Sawit", 120.0, 110.0, 3, 2, 1, 1850000000.00, "v1.0.0", 115, "180.252.164.21", now - timedelta(days=2, hours=8)),
            ]
            for uid, city, dist, surf, bld, bed, bath, carp, price, ver, lat, ip, dt in sample_logs:
                plog = PredictionLog(
                    id=uuid.uuid4(),
                    user_id=uid,
                    city=city,
                    district=dist,
                    surface_area=surf,
                    building_area=bld,
                    bed=bed,
                    bath=bath,
                    carport=carp,
                    predicted_price=price,
                    model_version=ver,
                    latency_ms=lat,
                    client_ip=ip,
                    created_at=dt,
                )
                db.session.add(plog)
            db.session.commit()
            print(f"  [OK] {len(sample_logs)} Telemetri Prediction Logs berhasil diisi.")

        # 8. SEED NOTIFICATIONS
        if Notification.query.count() == 0:
            notifs = [
                (user1.id, "Tren Pasar Properti Cengkareng", "Rata-rata harga rumah di wilayah Cengkareng mengalami penyesuaian +2.8% bulan ini.", "MARKET_TREND", False),
                (user1.id, "Model Inferensi v1.0.0 Aktif", "Sistem telah diperbarui menggunakan model Ensemble Random Forest dengan akurasi R2 82.72%.", "SYSTEM", True),
                (user2.id, "Pembaruan Harga Kelapa Gading", "Wilayah Kelapa Gading mencatat rata-rata harga Rp 24,0 Juta per meter persegi.", "MARKET_TREND", False),
            ]
            for uid, title, msg, ntype, is_read in notifs:
                notif = Notification(
                    id=uuid.uuid4(),
                    user_id=uid,
                    title=title,
                    message=msg,
                    type=ntype,
                    is_read=is_read,
                )
                db.session.add(notif)
            db.session.commit()
            print("  [OK] Notifikasi in-app berhasil diisi.")

        # 9. SEED SYSTEM AUDIT LOGS
        if SystemAuditLog.query.count() == 0:
            now = datetime.now(timezone.utc)
            audits = [
                (admin.id, "UPLOAD_DATASET", "DATASET_MANAGER", "Mengunggah dataset primer jakarta_house_v1.csv (10.000 baris data)", "127.0.0.1", now - timedelta(days=3)),
                (admin.id, "TRAIN_MODEL", "ML_REGISTRY", "Melatih model Random Forest Regressor v1.0.0 (R2=0.8272, MAE=Rp 1.06 M)", "127.0.0.1", now - timedelta(days=2)),
                (admin.id, "SWITCH_MODEL", "ML_REGISTRY", "Menetapkan model Random Forest v1.0.0 sebagai mesin inferensi aktif produksi", "127.0.0.1", now - timedelta(days=2)),
                (admin.id, "INIT_STRICT_GATE", "SECURITY", "Inisialisasi sistem Strict Gate JWT Authentication HS256", "127.0.0.1", now - timedelta(hours=10)),
            ]
            for aid, atype, mname, desc, ip, dt in audits:
                alog = SystemAuditLog(
                    id=uuid.uuid4(),
                    admin_id=aid,
                    action_type=atype,
                    module_name=mname,
                    description=desc,
                    ip_address=ip,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
                    created_at=dt,
                )
                db.session.add(alog)
            db.session.commit()
            print("  [OK] System Audit Logs berhasil dicatat.")

        print("\n*** SEEDING DATABASE SELESAI DENGAN SUKSES! ***\n")

if __name__ == "__main__":
    seed_database()
