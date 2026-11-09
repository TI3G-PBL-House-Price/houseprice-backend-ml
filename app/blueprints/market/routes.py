from flask import Blueprint, request, jsonify
from app.models.location import MasterLocation, MarketStatistic

market_bp = Blueprint("market", __name__)

@market_bp.route("/locations", methods=["GET"])
def get_locations():
    """
    Mengambil daftar master referensi kota dan kecamatan di DKI Jakarta
    yang berstatus aktif, dikelompokkan per kota untuk kebutuhan dropdown mobile.
    """
    try:
        locations = (
            MasterLocation.query.filter_by(is_active=True)
            .order_by(MasterLocation.city.asc(), MasterLocation.district.asc())
            .all()
        )

        # Kelompokkan kecamatan berdasarkan kota
        grouped_locations = {}
        for loc in locations:
            city_name = loc.city.strip()
            district_name = loc.district.strip()

            if city_name not in grouped_locations:
                grouped_locations[city_name] = []

            if district_name and district_name not in grouped_locations[city_name]:
                grouped_locations[city_name].append(district_name)

        # Susun payload data sesuai spesifikasi OpenAPI LocationsResponse
        data_payload = [
            {
                "city": city,
                "districts": districts
            }
            for city, districts in grouped_locations.items()
        ]

        return jsonify({
            "status": "success",
            "message": "Master lokasi berhasil dimuat",
            "data": data_payload
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error_code": "DATABASE_ERROR",
            "message": "Gagal memuat data master wilayah",
            "details": [str(e)]
        }), 500


@market_bp.route("/market-statistics", methods=["GET"])
def get_market_statistics():
    """
    Menyajikan data agregasi statistik pasar properti (rata-rata harga, rata-rata
    harga per meter persegi, luas tanah/bangunan) untuk visualisasi Beranda Mobile.
    Mendukung filter opsional berdasarkan parameter query 'city' dan 'district'.
    """
    try:
        city_param = request.args.get("city", "").strip()
        district_param = request.args.get("district", "").strip()

        query = MarketStatistic.query

        if city_param:
            query = query.filter(MarketStatistic.city.ilike(f"%{city_param}%"))
        
        if district_param:
            query = query.filter(MarketStatistic.district.ilike(f"%{district_param}%"))

        # Urutkan berdasarkan kota, dan tempatkan data level kota (district null) di awal
        records = query.order_by(
            MarketStatistic.city.asc(),
            MarketStatistic.district.asc().nullsfirst()
        ).all()

        data_payload = []
        for item in records:
            data_payload.append({
                "city": item.city,
                "district": item.district,
                "avg_price": float(item.avg_price),
                "avg_price_per_sqm": float(item.avg_price_per_sqm),
                "avg_surface_area": float(item.avg_surface_area),
                "avg_building_area": float(item.avg_building_area),
                "total_properties": item.total_properties
            })

        return jsonify({
            "status": "success",
            "message": "Data statistik pasar berhasil dimuat",
            "data": data_payload
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error_code": "DATABASE_ERROR",
            "message": "Terjadi kesalahan pembacaan basis data PostgreSQL",
            "details": [str(e)]
        }), 500

