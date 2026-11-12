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


def seed_database():
    """Inisialisasi data sektor inti (admins, users, ml_models) tanpa dependensi file CSV."""
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

        # 3. KOSONGKAN DATA DATASET, LOKASI & STATISTIK PASAR (Inisiasi Mandiri via Web Admin Upload)
        MasterLocation.query.delete()
        MarketStatistic.query.delete()
        DatasetMetadata.query.delete()
        db.session.commit()
        print("  [OK] Tabel dataset, lokasi & statistik pasar dikosongkan untuk unggah mandiri di Web Admin.")

        # 4. SEED ML MODELS (Metrik & Arsitektur Dibaca Dinamis dari Berkas Model)
        model_path = os.path.join(app.root_path, "..", "models_artefacts", "house_price_xgb_model.pkl")
        eval_path = os.path.join(app.root_path, "..", "models_artefacts", "hasil_xgb.pkl")

        if os.path.exists(eval_path) and os.path.exists(model_path):
            eval_data = joblib.load(eval_path)
            algorithm_type = eval_data.get("Model", "XGBoost Regressor")
            testing_metrics = eval_data.get("Testing", {})
            r2_score = float(testing_metrics.get("R2", 0.8308))
            mae_score = float(testing_metrics.get("Mean absolute error", 0.2230))
            rmse_score = float(testing_metrics.get("Root mean squared error", 0.3350))

            loaded_model = joblib.load(model_path)
            if hasattr(loaded_model, "steps") and loaded_model.steps:
                estimator_obj = loaded_model.steps[-1][1]
                model_name = f"{estimator_obj.__class__.__name__} (Tuned)"
            else:
                model_name = f"{loaded_model.__class__.__name__} (Tuned)"
        else:
            algorithm_type = "XGBoost Regressor"
            model_name = "XGBRegressor (Tuned)"
            r2_score = 0.8308
            mae_score = 0.2230
            rmse_score = 0.3350

        MLModel.query.delete()
        active_model = MLModel(
            id=uuid.uuid4(),
            model_name=model_name,
            version="v1.0.0",
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
        print(f"  [OK] Registri model ML aktif ({model_name}, R2={r2_score:.4f}, MAE={mae_score:.4f}).")

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
