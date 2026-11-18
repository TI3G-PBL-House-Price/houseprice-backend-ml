import os
import sys
import uuid
import joblib
from datetime import datetime, timezone

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
from app.services.dataset_service import DatasetService


def seed_database():
    """Inisialisasi data sektor inti (admins, users, ml_models) dan sinkronisasi
    dataset jakarta_house_v3 (dengan kolom NJOP) ke master_locations & market_statistics."""
    app = create_app()
    with app.app_context():
        print("[SEED] Memulai inisialisasi sektor inti basis data HousePrice...")

        # 1. SEED ADMINS (Login Resmi)
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
            print("  [OK] Admin default (admin_hanif) diverifikasi.")
        else:
            print("  [INFO] Admin default sudah ada.")

        # 2. SEED USERS (Mobile Users Resmi)
        official_users = [
            ("budi.santoso@gmail.com", "Budi Santoso", "081234567890"),
            ("siti.rahma@gmail.com", "Siti Rahma", "081987654321"),
            ("kevin.wijaya@gmail.com", "Kevin Wijaya", "085712345678"),
        ]
        for email, name, phone in official_users:
            u = User.query.filter_by(email=email).first()
            if not u:
                u = User(
                    id=uuid.uuid4(),
                    full_name=name,
                    email=email,
                    password_hash=bcrypt.generate_password_hash("Password123!", rounds=12).decode("utf-8"),
                    phone_number=phone,
                    is_active=True,
                )
                db.session.add(u)
        db.session.commit()
        print("  [OK] Akun user mobile resmi berhasil diverifikasi.")

        # 3. SEED DATASET, LOKASI & STATISTIK PASAR dari jakarta_house_v3
        # Dataset v3 sudah mengandung kolom njop/m2 yang akan disimpan ke master_locations
        dataset_filename = "jakarta_house_v3.csv"
        dataset_path = os.path.join(
            app.root_path, "..", "uploads", "datasets", dataset_filename
        )

        DatasetMetadata.query.delete()
        db.session.commit()

        if os.path.exists(dataset_path):
            try:
                print(f"  [INFO] Mensinkronisasi dataset '{dataset_filename}' ke DB...")
                total_records, total_locations, total_market_records = (
                    DatasetService.sync_locations_and_stats_from_csv(dataset_path)
                )

                file_size_bytes = os.path.getsize(dataset_path)
                new_dataset = DatasetMetadata(
                    id=uuid.uuid4(),
                    file_name=dataset_filename,
                    file_path=f"uploads/datasets/{dataset_filename}",
                    total_records=total_records,
                    file_size_bytes=file_size_bytes,
                    uploaded_by=admin.id,
                    created_at=datetime.now(timezone.utc),
                )
                db.session.add(new_dataset)
                db.session.commit()
                print(
                    f"  [OK] Dataset '{dataset_filename}' tersinkronisasi: "
                    f"{total_records:,} baris, {total_locations} wilayah, "
                    f"{total_market_records} statistik pasar, {file_size_bytes/1024:.1f} KB."
                )
            except Exception as e:
                db.session.rollback()
                print(f"  [WARN] Gagal mensinkronisasi dataset: {e}")
                print("  [INFO] Tabel lokasi & statistik pasar dikosongkan — unggah via Web Admin.")
        else:
            MasterLocation.query.delete()
            MarketStatistic.query.delete()
            db.session.commit()
            print(
                f"  [WARN] File '{dataset_filename}' tidak ditemukan di uploads/datasets/. "
                "Tabel lokasi & statistik pasar dikosongkan — unggah via Web Admin."
            )

        # 4. SEED ML MODELS (Metrik & Arsitektur Dibaca Dinamis dari Berkas Model v2)
        model_path = os.path.join(app.root_path, "..", "models_artefacts", "house_price_xgb_model.pkl")
        eval_path = os.path.join(app.root_path, "..", "models_artefacts", "hasil_xgb.pkl")

        if os.path.exists(eval_path) and os.path.exists(model_path):
            eval_data = joblib.load(eval_path)
            algorithm_type = eval_data.get("Model", "XGBoost + GridSearchCV")
            testing_metrics = eval_data.get("Testing", {})
            r2_score = float(testing_metrics.get("R2", 0.8893))
            mae_score = float(testing_metrics.get("Mean absolute error", 0.2466))
            rmse_score_val = testing_metrics.get("Root mean squared error", 0.3639)
            # Tangani tipe numpy float64
            rmse_score = float(rmse_score_val) if hasattr(rmse_score_val, '__float__') else float(rmse_score_val)

            loaded_model = joblib.load(model_path)
            if hasattr(loaded_model, "steps") and loaded_model.steps:
                estimator_obj = loaded_model.steps[-1][1]
                model_name = f"{estimator_obj.__class__.__name__} (Tuned)"
            else:
                model_name = f"{loaded_model.__class__.__name__} (Tuned)"
        else:
            algorithm_type = "XGBoost + GridSearchCV"
            model_name = "XGBRegressor (Tuned)"
            r2_score = 0.8893
            mae_score = 0.2466
            rmse_score = 0.3639

        MLModel.query.delete()
        active_model = MLModel(
            id=uuid.uuid4(),
            model_name=model_name,
            version="v2.0.0",
            model_file_path="models_artefacts/house_price_xgb_model.pkl",
            algorithm_type=algorithm_type,
            r2_score=round(r2_score, 4),
            mae_score=round(mae_score, 4),
            rmse_score=round(rmse_score, 4),
            is_active=True,
            trained_by=admin.id,
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(active_model)
        db.session.commit()
        print(
            f"  [OK] Registri model ML aktif ({model_name} v2.0.0, "
            f"R2={r2_score:.4f}, MAE={mae_score:.4f}, RMSE={rmse_score:.4f})."
        )

        # 5. PEMBERSIHAN DATA LOG & AKUN SEMENTARA
        PredictionLog.query.delete()
        Notification.query.delete()
        SystemAuditLog.query.delete()
        User.query.filter(User.email.notin_([u[0] for u in official_users])).delete()
        db.session.commit()
        print("  [OK] Log prediksi, notifikasi, audit & akun sementara dibersihkan.")

        print("\n*** INISIALISASI SEKTOR INTI BASIS DATA SELESAI! ***\n")


if __name__ == "__main__":
    seed_database()
