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

