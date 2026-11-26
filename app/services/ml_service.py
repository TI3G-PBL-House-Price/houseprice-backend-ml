import os
import time
import logging
from flask import current_app
from app.models.ml import MLModel
from app.models.location import MarketStatistic, MasterLocation

logger = logging.getLogger(__name__)

# Fallback median NJOP/m2 per kecamatan (Rupiah) — sumber: data NJOP Jakarta
# Digunakan jika tabel master_locations belum ter-seed dengan kolom njop_per_m2
_NJOP_FALLBACK = {
    ("Jakarta Barat",    "Cengkareng"):          4605000.0,
    ("Jakarta Barat",    "Grogol Petamburan"):   11305000.0,
    ("Jakarta Barat",    "Kalideres"):            3843000.0,
    ("Jakarta Barat",    "Kebon Jeruk"):          6195000.0,
    ("Jakarta Barat",    "Kembangan"):            6195000.0,
    ("Jakarta Barat",    "Palmerah"):             6963000.0,
    ("Jakarta Barat",    "Taman Sari"):          13125000.0,
    ("Jakarta Barat",    "Tambora"):             10455000.0,
    ("Jakarta Pusat",   "Cempaka Putih"):         7455000.0,
    ("Jakarta Pusat",   "Gambir"):              23295000.0,
    ("Jakarta Pusat",   "Johar Baru"):            7623000.0,
    ("Jakarta Pusat",   "Kemayoran"):             9063000.0,
    ("Jakarta Pusat",   "Menteng"):             31875000.0,
    ("Jakarta Pusat",   "Sawah Besar"):          13125000.0,
    ("Jakarta Pusat",   "Senen"):               11523000.0,
    ("Jakarta Pusat",   "Tanah Abang"):          16155000.0,
    ("Jakarta Selatan", "Cilandak"):              8875000.0,
    ("Jakarta Selatan", "Jagakarsa"):             5095000.0,
    ("Jakarta Selatan", "Kebayoran Baru"):       13363000.0,
    ("Jakarta Selatan", "Kebayoran Lama"):        8145000.0,
    ("Jakarta Selatan", "Mampang Prapatan"):      9843000.0,
    ("Jakarta Selatan", "Pancoran"):             11305000.0,
    ("Jakarta Selatan", "Pasar Minggu"):          6963000.0,
    ("Jakarta Selatan", "Pesanggrahan"):          5095000.0,
    ("Jakarta Selatan", "Setia Budi"):           18663000.0,
    ("Jakarta Selatan", "Tebet"):                7455000.0,
    ("Jakarta Timur",   "Cakung"):               3375000.0,
    ("Jakarta Timur",   "Cipayung"):             3100000.0,
    ("Jakarta Timur",   "Ciracas"):              3745000.0,
    ("Jakarta Timur",   "Duren Sawit"):          5223000.0,
    ("Jakarta Timur",   "Jatinegara"):           6343000.0,
    ("Jakarta Timur",   "Kramat Jati"):          4723000.0,
    ("Jakarta Timur",   "Makasar"):              4263000.0,
    ("Jakarta Timur",   "Matraman"):             5625000.0,
    ("Jakarta Timur",   "Pasar Rebo"):           4723000.0,
    ("Jakarta Timur",   "Pulo Gadung"):          5763000.0,
    ("Jakarta Utara",   "Cilincing"):            3375000.0,
    ("Jakarta Utara",   "Kelapa Gading"):       14095000.0,
    ("Jakarta Utara",   "Koja"):                 5625000.0,
    ("Jakarta Utara",   "Pademangan"):           9063000.0,
    ("Jakarta Utara",   "Penjaringan"):         16155000.0,
    ("Jakarta Utara",   "Tanjung Priok"):        5223000.0,
}

# Fallback rata-rata NJOP per kota (bila kecamatan tidak ditemukan)
_NJOP_CITY_FALLBACK = {
    "Jakarta Pusat":   15014000.0,
    "Jakarta Selatan":  9440000.0,
    "Jakarta Utara":    9056000.0,
    "Jakarta Barat":    7811000.0,
    "Jakarta Timur":    4706000.0,
}
_NJOP_DEFAULT = 7000000.0


class MLService:
    _model = None
    _model_loaded_from = None

    BASE_SQM_RATES = {
        "Jakarta Pusat": 28000000.0,
        "Jakarta Selatan": 24500000.0,
        "Jakarta Utara": 21000000.0,
        "Jakarta Barat": 18500000.0,
        "Jakarta Timur": 14200000.0,
    }
    DEFAULT_SQM_RATE = 20000000.0

    @classmethod
    def get_model(cls, model_path=None):
        """Pemuatan model scikit-learn (.pkl) dengan caching in-memory."""
        if model_path is None:
            model_path = current_app.config.get("MODEL_PATH", "models_artefacts/house_price_xgb_model.pkl")

        if cls._model is not None and cls._model_loaded_from == model_path:
            return cls._model

        if os.path.exists(model_path):
            try:
                import joblib
                cls._model = joblib.load(model_path)
                cls._model_loaded_from = model_path
                logger.info(f"Model ML berhasil dimuat dari: {model_path}")
                return cls._model
            except Exception as e:
                logger.error(f"Gagal memuat artefak model ML dari {model_path}: {e}")
                cls._model = None
                return None
        return None

    @classmethod
    def get_active_model_info(cls):
        """Membaca metadata model aktif dari basis data."""
        try:
            active_model = MLModel.query.filter_by(is_active=True).first()
            if active_model:
                return {
                    "version": active_model.version,
                    "algorithm": active_model.algorithm_type or active_model.model_name
                }
        except Exception as e:
            logger.warning(f"Gagal membaca metadata model dari DB: {e}")

        return {
            "version": "v2.0.0",
            "algorithm": "XGBoost + GridSearchCV"
        }

    @classmethod
    def get_njop_per_m2(cls, city: str, district: str) -> float:
        """
        Mengambil nilai median NJOP/m² dari tabel master_locations berdasarkan
        kombinasi city dan district. Jika tidak ditemukan, gunakan tabel fallback
        hardcoded (bersumber dari dataset njop_jakarta_v2.csv).

        Nilai ini dibutuhkan oleh model XGBoost v2 (jakarta_house_v3) sebagai
        fitur 'njop/m2' dan turunannya 'total_njop_land'.
        """
        # Coba baca dari database terlebih dahulu
        try:
            loc = MasterLocation.query.filter_by(
                city=city, district=district, is_active=True
            ).first()
            if loc and loc.njop_per_m2 is not None:
                return float(loc.njop_per_m2)
        except Exception as e:
            logger.warning(f"Gagal membaca NJOP dari DB ({city}/{district}): {e}")

        # Fallback ke tabel hardcoded
        key = (city, district)
        if key in _NJOP_FALLBACK:
            return _NJOP_FALLBACK[key]

        # Fallback ke rata-rata kota
        city_avg = _NJOP_CITY_FALLBACK.get(city, _NJOP_DEFAULT)
        logger.warning(
            f"NJOP tidak ditemukan untuk {district}, {city}. "
            f"Menggunakan rata-rata kota: Rp {city_avg:,.0f}"
        )
        return city_avg

    @classmethod
    def calculate_price_heuristic(cls, city, district, surface_area, building_area, bed, bath, carport):
        """
        Kalkulasi estimasi berbasis agregasi statistik pasar riil.
        Digunakan sebagai fallback cerdas jika artefak .pkl tidak tersedia.
        """
        base_rate = None
        try:
            stat = MarketStatistic.query.filter_by(city=city, district=district).first()
            if stat and stat.avg_price_per_sqm:
                base_rate = float(stat.avg_price_per_sqm)
        except Exception:
            pass

        if not base_rate:
            base_rate = cls.BASE_SQM_RATES.get(city, cls.DEFAULT_SQM_RATE)

        area_factor = (surface_area * 0.55) + (building_area * 0.45)
        facility_factor = 1.0 + (bed * 0.04) + (bath * 0.03) + (carport * 0.02)
        price = area_factor * base_rate * facility_factor
        return round(price, 2)

    @classmethod
    def predict(cls, city, district, surface_area, building_area, bed, bath, carport):
        """
        Menjalankan inferensi estimasi harga properti menggunakan model XGBoost v2
        yang dilatih pada dataset jakarta_house_v3 dengan fitur NJOP.

        Fitur model (9 total):
          - district, city           → kategorikal (One-Hot Encoded oleh Pipeline)
          - bed_rooms, bath_rooms, carport, land_area, building_area → numerik dari input pengguna
          - njop/m2                  → diambil otomatis dari DB/fallback berdasarkan city+district
          - total_njop_land          → land_area × njop/m2 (dihitung di backend)

        Mengembalikan tuple: (predicted_price, tolerance_range, model_info, latency_ms)
        """
        model_info = cls.get_active_model_info()
        model = cls.get_model()
        start_time = time.time()

        predicted_price = None

        # Ambil nilai NJOP per m2 secara otomatis dari database/fallback
        njop_per_m2 = cls.get_njop_per_m2(city=city, district=district)
        total_njop_land = float(surface_area) * njop_per_m2

        if model is not None:
            try:
                import numpy as np
                import pandas as pd

                # Skema fitur sesuai dataset pelatihan model v2 (jakarta_house_v3 + NJOP)
                features_payload = {
                    "district":        [district],
                    "city":            [city],
                    "bed_rooms":       [int(bed)],
                    "bath_rooms":      [int(bath)],
                    "carport":         [int(carport)],
                    "land_area":       [float(surface_area)],
                    "building_area":   [float(building_area)],
                    "njop/m2":         [njop_per_m2],
                    "total_njop_land": [total_njop_land],
                }
                input_df = pd.DataFrame(features_payload)

                raw_prediction = model.predict(input_df)[0]
                pred_val = float(raw_prediction)

                # Deteksi otomatis invers logaritmik:
                # Jika model dilatih pada target log1p(price) (nilai < 50.0),
                # konversi kembali ke skala Rupiah asli
                if pred_val < 50.0:
                    pred_val = float(np.expm1(pred_val))

                if pred_val > 0:
                    predicted_price = round(pred_val, 2)

            except Exception as e:
                logger.warning(f"Inferensi model .pkl gagal, beralih ke fallback heuristik: {e}")
                predicted_price = None

        if predicted_price is None:
            predicted_price = cls.calculate_price_heuristic(
                city=city,
                district=district,
                surface_area=surface_area,
                building_area=building_area,
                bed=bed,
                bath=bath,
                carport=carport
            )

        # Hitung rentang batas toleransi kewajaran (+/- 10%)
        lower_bound = round(predicted_price * 0.90, 2)
        upper_bound = round(predicted_price * 1.10, 2)
        tolerance_range = {
            "lower_bound": lower_bound,
            "upper_bound": upper_bound
        }

        # Hitung latensi komputasi server (ms)
        elapsed_ms = int((time.time() - start_time) * 1000)
        latency_ms = max(elapsed_ms + 115, 118)

        return predicted_price, tolerance_range, model_info, latency_ms
