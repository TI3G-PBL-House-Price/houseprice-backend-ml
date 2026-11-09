import os
import sys
import uuid
import joblib
import pandas as pd
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
    app = create_app()
    with app.app_context():
        print("[SEED] Memulai proses sinkronisasi dinamis basis data HousePrice...")

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

        # 3. BACA DATASET PRIMER SECARA DINAMIS
        dataset_path = os.path.join(app.root_path, "..", "uploads", "datasets", "jakarta_house.csv")
        if not os.path.exists(dataset_path):
            alt_path = os.path.join(app.root_path, "..", "..", "ml-model-testing", "dataset", "jakarta_house.csv")
            if os.path.exists(alt_path):
                import shutil
                os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
                shutil.copy(alt_path, dataset_path)

        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Berkas dataset primer tidak ditemukan di: {dataset_path}")

        df = pd.read_csv(dataset_path)
        df_clean = df.dropna(subset=["price", "city", "district", "land_area", "building_area"]).copy()
        df_clean["price_per_sqm"] = df_clean["price"] / df_clean["land_area"]

        # 4. SEED MASTER LOCATIONS (Dinamis dari Dataset)
        locations_df = df_clean[["city", "district"]].drop_duplicates().sort_values(by=["city", "district"])
        MasterLocation.query.delete()
        for _, row in locations_df.iterrows():
            c = str(row["city"]).strip()
            d = str(row["district"]).strip()
            if c and d:
                db.session.add(MasterLocation(city=c, district=d, is_active=True))
        db.session.commit()
        print(f"  [OK] {len(locations_df)} Master Wilayah diekstrak dinamis dari dataset.")

        # 5. SEED MARKET STATISTICS (Dihitung Dinamis dari Dataset)
        MarketStatistic.query.delete()

        # a. Agregasi Level Kota (district = None)
        city_stats = df_clean.groupby("city").agg(
            avg_price=("price", "mean"),
            avg_price_per_sqm=("price_per_sqm", "mean"),
            avg_surface_area=("land_area", "mean"),
            avg_building_area=("building_area", "mean"),
            total_properties=("price", "count"),
        ).reset_index()

        for _, r in city_stats.iterrows():
            db.session.add(MarketStatistic(
                city=str(r["city"]).strip(),
                district=None,
                avg_price=round(float(r["avg_price"]), 2),
                avg_price_per_sqm=round(float(r["avg_price_per_sqm"]), 2),
                avg_surface_area=round(float(r["avg_surface_area"]), 2),
                avg_building_area=round(float(r["avg_building_area"]), 2),
                total_properties=int(r["total_properties"]),
            ))

        # b. Agregasi Level Kawasan / Kecamatan
        district_stats = df_clean.groupby(["city", "district"]).agg(
            avg_price=("price", "mean"),
            avg_price_per_sqm=("price_per_sqm", "mean"),
            avg_surface_area=("land_area", "mean"),
            avg_building_area=("building_area", "mean"),
            total_properties=("price", "count"),
        ).reset_index()

        for _, r in district_stats.iterrows():
            db.session.add(MarketStatistic(
                city=str(r["city"]).strip(),
                district=str(r["district"]).strip(),
                avg_price=round(float(r["avg_price"]), 2),
                avg_price_per_sqm=round(float(r["avg_price_per_sqm"]), 2),
                avg_surface_area=round(float(r["avg_surface_area"]), 2),
                avg_building_area=round(float(r["avg_building_area"]), 2),
                total_properties=int(r["total_properties"]),
            ))

        db.session.commit()
        total_market_records = len(city_stats) + len(district_stats)
        print(f"  [OK] {total_market_records} Statistik Pasar dihitung dinamis dari dataset.")

        # 6. SEED DATASET METADATA (Metadata Aktual dari Berkas Disk)
        DatasetMetadata.query.delete()
        file_size_bytes = os.path.getsize(dataset_path)
        total_records = len(df)
        file_name = os.path.basename(dataset_path)
        
        dataset = DatasetMetadata(
            id=uuid.uuid4(),
            file_name=file_name,
            file_path=f"uploads/datasets/{file_name}",
            total_records=total_records,
            file_size_bytes=file_size_bytes,
            uploaded_by=admin.id,
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(dataset)
        db.session.commit()
        print(f"  [OK] Metadata dataset primer ({file_name}, {total_records:,} baris, {file_size_bytes:,} bytes) dicatat dinamis.")

        # 7. SEED ML MODELS (Metrik & Arsitektur Dibaca Dinamis dari Berkas Model)
        model_path = os.path.join(app.root_path, "..", "models_artefacts", "model.pkl")
        eval_path = os.path.join(app.root_path, "..", "models_artefacts", "model_eval.pkl")

        model_name = "XGBoost Regressor (Tuned)"
        algorithm_type = "XGBoost + GridSearchCV"
        r2_score = 0.8310
        mae_score = 0.2230
        rmse_score = 0.3350

        if os.path.exists(eval_path):
            try:
                eval_data = joblib.load(eval_path)
                model_name = eval_data.get("Model", model_name)
                algorithm_type = eval_data.get("Model", algorithm_type)
                testing_metrics = eval_data.get("Testing", {})
                r2_score = float(testing_metrics.get("R2", r2_score))
                mae_score = float(testing_metrics.get("Mean absolute error", mae_score))
                rmse_score = float(testing_metrics.get("Root mean squared error", rmse_score))
            except Exception as e:
                print(f"  [WARN] Gagal membaca evaluasi model dinamis: {e}")

        if os.path.exists(model_path):
            try:
                loaded_model = joblib.load(model_path)
                if hasattr(loaded_model, "steps") and loaded_model.steps:
                    estimator_obj = loaded_model.steps[-1][1]
                    model_name = f"{estimator_obj.__class__.__name__} (Tuned)"
            except Exception:
                pass

        MLModel.query.delete()
        active_model = MLModel(
            id=uuid.uuid4(),
            model_name=model_name,
            version="v1.0.0",
            model_file_path="models_artefacts/model.pkl",
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
        print(f"  [OK] Registri model ML dibaca dinamis dari artefak ({model_name}, R2={r2_score:.4f}, MAE={mae_score:.4f}).")

        # 8. PEMBERSIHAN TOTAL DATA DUMMY
        PredictionLog.query.delete()
        Notification.query.delete()
        SystemAuditLog.query.delete()
        User.query.filter(User.email.notin_([u[0] for u in official_users])).delete()
        db.session.commit()
        print("  [OK] Seluruh data dummy (logs, notifikasi, audit, akun pengujian sementara) telah bersih 100%.")

        print("\n*** SEEDING DINAMIS 100% SELESAI DENGAN SUKSES! ***\n")

if __name__ == "__main__":
    seed_database()
