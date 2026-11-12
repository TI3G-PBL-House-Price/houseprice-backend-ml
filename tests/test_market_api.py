import pytest
from app.extensions import db
from app.models.location import MasterLocation, MarketStatistic


@pytest.fixture(scope="module", autouse=True)
def ensure_market_fixture_data(app):
    """Menjamin data master lokasi & statistik pasar tersedia selama pengujian modul market API."""
    with app.app_context():
        existing_cities = {loc.city for loc in MasterLocation.query.all()}
        has_tebet_stat = MarketStatistic.query.filter_by(district="Tebet").first() is not None
        if len(existing_cities) >= 5 and has_tebet_stat:
            yield
            return

        saved_locs = [
            {"city": loc.city, "district": loc.district, "is_active": loc.is_active}
            for loc in MasterLocation.query.all()
        ]
        saved_stats = [
            {
                "city": st.city,
                "district": st.district,
                "avg_price": st.avg_price,
                "avg_price_per_sqm": st.avg_price_per_sqm,
                "avg_surface_area": st.avg_surface_area,
                "avg_building_area": st.avg_building_area,
                "total_properties": st.total_properties,
            }
            for st in MarketStatistic.query.all()
        ]

        sample_locations = [
            ("Jakarta Selatan", "Tebet", 4500000000, 25000000, 180, 200, 12),
            ("Jakarta Pusat", "Menteng", 12000000000, 45000000, 260, 320, 8),
            ("Jakarta Barat", "Kembangan", 3200000000, 20000000, 160, 175, 10),
            ("Jakarta Timur", "Duren Sawit", 2400000000, 15000000, 160, 150, 9),
            ("Jakarta Utara", "Kelapa Gading", 5100000000, 28000000, 182, 210, 11),
        ]

        MasterLocation.query.delete()
        MarketStatistic.query.delete()
        for city, district, avg_p, avg_sqm, avg_sa, avg_ba, total in sample_locations:
            db.session.add(MasterLocation(city=city, district=district, is_active=True))
            db.session.add(MarketStatistic(
                city=city, district=None,
                avg_price=avg_p, avg_price_per_sqm=avg_sqm,
                avg_surface_area=avg_sa, avg_building_area=avg_ba,
                total_properties=total,
            ))
            db.session.add(MarketStatistic(
                city=city, district=district,
                avg_price=avg_p, avg_price_per_sqm=avg_sqm,
                avg_surface_area=avg_sa, avg_building_area=avg_ba,
                total_properties=total,
            ))
        db.session.commit()

        yield

        MasterLocation.query.delete()
        MarketStatistic.query.delete()
        for loc in saved_locs:
            db.session.add(MasterLocation(**loc))
        for st in saved_stats:
            db.session.add(MarketStatistic(**st))
        db.session.commit()


def test_get_locations_success(client):
    """Memverifikasi endpoint GET /api/v1/locations mengembalikan struktur hierarkis kota & kecamatan."""
    response = client.get("/api/v1/locations")
    assert response.status_code == 200
    
    payload = response.get_json()
    assert payload["status"] == "success"
    assert "Master lokasi berhasil dimuat" in payload["message"]
    assert isinstance(payload["data"], list)
    assert len(payload["data"]) >= 5

    # Pastikan setiap item memiliki key 'city' dan 'districts' (list)
    for city_group in payload["data"]:
        assert "city" in city_group
        assert "districts" in city_group
        assert isinstance(city_group["districts"], list)
        assert len(city_group["districts"]) > 0


def test_get_market_statistics_all(client):
    """Memverifikasi endpoint GET /api/v1/market-statistics mengembalikan seluruh ringkasan pasar."""
    response = client.get("/api/v1/market-statistics")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["status"] == "success"
    assert "Data statistik pasar berhasil dimuat" in payload["message"]
    assert isinstance(payload["data"], list)
    assert len(payload["data"]) > 0

    first_item = payload["data"][0]
    assert "city" in first_item
    assert "avg_price" in first_item
    assert "avg_price_per_sqm" in first_item
    assert isinstance(first_item["avg_price"], (float, int))


def test_get_market_statistics_filter_city(client):
    """Memverifikasi filter query parameter ?city=Jakarta+Selatan."""
    response = client.get("/api/v1/market-statistics?city=Jakarta+Selatan")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["status"] == "success"
    for item in payload["data"]:
        assert item["city"] == "Jakarta Selatan"


def test_get_market_statistics_filter_district(client):
    """Memverifikasi filter query parameter ?district=Tebet."""
    response = client.get("/api/v1/market-statistics?district=Tebet")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["status"] == "success"
    assert len(payload["data"]) == 1
    assert payload["data"][0]["district"] == "Tebet"

