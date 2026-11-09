import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.log import PredictionLog
from app.middlewares.auth_guard import token_required
from app.services.ml_service import MLService

predict_bp = Blueprint("predict", __name__)


@predict_bp.route("", methods=["POST"], strict_slashes=False)
@predict_bp.route("/", methods=["POST"], strict_slashes=False)
@token_required
def predict_price(current_user):
    """
    POST /api/v1/predict
    Strict Gate Protected: Menghitung estimasi harga properti berbasis model ML
    dan mencatat riwayat transaksi komputasi ke tabel prediction_logs.
    """
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return jsonify({
            "status": "error",
            "error_code": "INVALID_INPUT_SCHEMA",
            "message": "Body permintaan JSON wajib disertakan",
            "details": ["Payload JSON tidak ditemukan atau format tidak valid"]
        }), 400

    details = []

    # Validasi city & district
    city = payload.get("city")
    if not city or not isinstance(city, str) or not city.strip():
        details.append("Field 'city' wajib diisi dengan nama kota administrasi yang valid")
    else:
        city = city.strip()

    district = payload.get("district")
    if not district or not isinstance(district, str) or not district.strip():
        details.append("Field 'district' wajib diisi dengan nama kecamatan/kawasan yang valid")
    else:
        district = district.strip()

    # Validasi surface_area
    surface_area = payload.get("surface_area")
    if surface_area is None or not isinstance(surface_area, (int, float)) or surface_area < 1:
        details.append("Nilai luas tanah (surface_area) harus berupa angka dan minimal 1 m²")

    # Validasi building_area
    building_area = payload.get("building_area")
    if building_area is None or not isinstance(building_area, (int, float)) or building_area < 1:
        details.append("Nilai luas bangunan (building_area) harus berupa angka dan minimal 1 m²")

    # Validasi bed
    bed = payload.get("bed")
    if bed is None or not isinstance(bed, int) or isinstance(bed, bool) or bed < 0:
        details.append("Jumlah kamar tidur (bed) harus berupa bilangan bulat non-negatif (>= 0)")

    # Validasi bath
    bath = payload.get("bath")
    if bath is None or not isinstance(bath, int) or isinstance(bath, bool) or bath < 0:
        details.append("Jumlah kamar mandi (bath) harus berupa bilangan bulat non-negatif (>= 0)")

    # Validasi carport
    carport = payload.get("carport")
    if carport is None or not isinstance(carport, int) or isinstance(carport, bool) or carport < 0:
        details.append("Kapasitas carport harus berupa bilangan bulat non-negatif (>= 0)")

    if details:
        return jsonify({
            "status": "error",
            "error_code": "INVALID_INPUT_SCHEMA",
            "message": "Masukan data tidak valid atau batas nilai terlanggar",
            "details": details
        }), 400

    try:
        # Eksekusi inferensi melalui MLService
        predicted_price, tolerance_range, model_info, latency_ms = MLService.predict(
            city=city,
            district=district,
            surface_area=float(surface_area),
            building_area=float(building_area),
            bed=int(bed),
            bath=int(bath),
            carport=int(carport)
        )

        # Simpan jejak komputasi ke tabel prediction_logs yang terikat ke akun pengguna
        log_entry = PredictionLog(
            id=uuid.uuid4(),
            user_id=current_user.id,
            city=city,
            district=district,
            surface_area=surface_area,
            building_area=building_area,
            bed=bed,
            bath=bath,
            carport=carport,
            predicted_price=predicted_price,
            model_version=model_info.get("version", "v1.0.0"),
            latency_ms=latency_ms,
            client_ip=request.remote_addr or "127.0.0.1",
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(log_entry)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Estimasi harga properti berhasil dihitung",
            "data": {
                "prediction_id": str(log_entry.id),
                "predicted_price": float(predicted_price),
                "currency": "IDR",
                "tolerance_range": {
                    "lower_bound": float(tolerance_range["lower_bound"]),
                    "upper_bound": float(tolerance_range["upper_bound"])
                },
                "model_info": {
                    "version": model_info.get("version", "v1.0.0"),
                    "algorithm": model_info.get("algorithm", "Random Forest Regressor")
                },
                "performance": {
                    "latency_ms": latency_ms
                }
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Terjadi kesalahan internal komputasi saat mengeksekusi inferensi",
            "details": [str(e)]
        }), 500


@predict_bp.route("/history", methods=["GET"], strict_slashes=False)
@token_required
def get_prediction_history(current_user):
    """
    GET /api/v1/predict/history
    Strict Gate Protected: Menampilkan daftar riwayat kalkulasi prediksi milik pengguna aktif.
    Mendukung paginasi melalui query parameters 'limit' dan 'offset'.
    """
    try:
        limit = request.args.get("limit", default=20, type=int)
        offset = request.args.get("offset", default=0, type=int)
    except Exception:
        limit = 20
        offset = 0

    if limit is None or limit < 1:
        limit = 20
    elif limit > 100:
        limit = 100

    if offset is None or offset < 0:
        offset = 0

    try:
        records = (
            PredictionLog.query.filter_by(user_id=current_user.id)
            .order_by(PredictionLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        history_items = [
            {
                "id": str(item.id),
                "city": item.city,
                "district": item.district,
                "surface_area": float(item.surface_area),
                "building_area": float(item.building_area),
                "predicted_price": float(item.predicted_price),
                "created_at": item.created_at.isoformat() if item.created_at else None
            }
            for item in records
        ]

        return jsonify({
            "status": "success",
            "message": "Riwayat prediksi berhasil diambil",
            "data": history_items
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error_code": "DATABASE_ERROR",
            "message": "Gagal mengambil data riwayat prediksi dari basis data",
            "details": [str(e)]
        }), 500
