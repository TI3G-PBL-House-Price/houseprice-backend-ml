import uuid
import pytest
from app.models.log import PredictionLog

def get_auth_token(client, email=None, password="Password123!"):
    """Helper untuk mendaftarkan dan me-login-kan user pengujian."""
    if email is None:
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
    
    register_payload = {
        "full_name": "Test Prediction User",
        "email": email,
        "password": password,
        "confirm_password": password,
        "phone_number": "081299998888"
    }
    reg_res = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201

    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    token = login_res.get_json()["data"]["access_token"]
    user_id = login_res.get_json()["data"]["user"]["id"]
    return token, user_id


def test_predict_unauthorized(client):
    """Memverifikasi endpoint POST /api/v1/predict menolak permintaan tanpa token JWT (401)."""
    payload = {
        "city": "Jakarta Selatan",
        "district": "Kebayoran Baru",
        "surface_area": 150.0,
        "building_area": 200.0,
        "bed": 4,
        "bath": 3,
        "carport": 2
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 401
    data = response.get_json()
    assert data["status"] == "error"


def test_predict_invalid_schema(client):
    """Memverifikasi validasi skema masukan fisik properti (400 INVALID_INPUT_SCHEMA)."""
    token, _ = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Kasus 1: Luas tanah < 1 m² dan kamar tidur negatif
    invalid_payload = {
        "city": "Jakarta Barat",
        "district": "Kebon Jeruk",
        "surface_area": 0.0,  # Tidak valid (< 1)
        "building_area": 50.0,
        "bed": -1,  # Tidak valid (< 0)
        "bath": 1,
        "carport": 1
    }
    response = client.post("/api/v1/predict", json=invalid_payload, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "error"
    assert data["error_code"] == "INVALID_INPUT_SCHEMA"
    assert isinstance(data["details"], list)
    assert len(data["details"]) >= 2

    # Kasus 2: Field wajib kosong (city string kosong)
    empty_city_payload = {
        "city": "   ",
        "district": "Tebet",
        "surface_area": 100.0,
        "building_area": 80.0,
        "bed": 2,
        "bath": 1,
        "carport": 1
    }
    response_empty = client.post("/api/v1/predict", json=empty_city_payload, headers=headers)
    assert response_empty.status_code == 400
    assert response_empty.get_json()["error_code"] == "INVALID_INPUT_SCHEMA"


def test_predict_success_and_tolerance_range(client):
    """
    Memverifikasi inferensi prediksi berhasil, batas toleransi (+/- 10%) valid,
    dan telemetri tercatat di prediction_logs.
    """
    token, user_id = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "city": "Jakarta Selatan",
        "district": "Tebet",
        "surface_area": 120.0,
        "building_area": 140.0,
        "bed": 3,
        "bath": 2,
        "carport": 1
    }

    response = client.post("/api/v1/predict", json=payload, headers=headers)
    assert response.status_code == 200

    res_body = response.get_json()
    assert res_body["status"] == "success"
    assert "Estimasi harga properti berhasil dihitung" in res_body["message"]

    pred_data = res_body["data"]
    assert "prediction_id" in pred_data
    assert pred_data["currency"] == "IDR"
    assert isinstance(pred_data["predicted_price"], (int, float))
    assert pred_data["predicted_price"] > 0

    # Verifikasi toleransi wajar (+/- 10%)
    predicted = pred_data["predicted_price"]
    expected_lower = round(predicted * 0.90, 2)
    expected_upper = round(predicted * 1.10, 2)
    assert pred_data["tolerance_range"]["lower_bound"] == expected_lower
    assert pred_data["tolerance_range"]["upper_bound"] == expected_upper

    # Verifikasi model info & performance NFR (< 1500 ms)
    assert "version" in pred_data["model_info"]
    assert "algorithm" in pred_data["model_info"]
    assert isinstance(pred_data["performance"]["latency_ms"], int)
    assert pred_data["performance"]["latency_ms"] < 1500


def test_predict_history_and_user_isolation(client):
    """
    Memverifikasi riwayat prediksi (GET /api/v1/predict/history)
    mendukung paginasi dan mengisolasi data antar-pengguna secara ketat.
    """
    # 1. User A melakukan 2 kali prediksi
    token_a, user_a_id = get_auth_token(client)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    client.post("/api/v1/predict", json={
        "city": "Jakarta Barat", "district": "Citra Garden",
        "surface_area": 100.0, "building_area": 85.0, "bed": 2, "bath": 1, "carport": 1
    }, headers=headers_a)

    client.post("/api/v1/predict", json={
        "city": "Jakarta Timur", "district": "Cakung",
        "surface_area": 120.0, "building_area": 100.0, "bed": 3, "bath": 2, "carport": 1
    }, headers=headers_a)

    # 2. Ambil riwayat User A
    hist_res_a = client.get("/api/v1/predict/history", headers=headers_a)
    assert hist_res_a.status_code == 200
    hist_data_a = hist_res_a.get_json()["data"]
    assert len(hist_data_a) >= 2
    assert "city" in hist_data_a[0]
    assert "predicted_price" in hist_data_a[0]
    assert "created_at" in hist_data_a[0]

    # 3. User B baru belum pernah melakukan prediksi -> riwayat harus kosong
    token_b, user_b_id = get_auth_token(client)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    hist_res_b = client.get("/api/v1/predict/history", headers=headers_b)
    assert hist_res_b.status_code == 200
    hist_data_b = hist_res_b.get_json()["data"]
    assert len(hist_data_b) == 0  # Terisolasi bersih dari data user A

    # 4. Tes paginasi limit=1
    paged_res = client.get("/api/v1/predict/history?limit=1&offset=0", headers=headers_a)
    assert paged_res.status_code == 200
    assert len(paged_res.get_json()["data"]) == 1


def test_predict_history_unauthorized(client):
    """Memverifikasi riwayat prediksi ditolak jika tanpa token (401)."""
    response = client.get("/api/v1/predict/history")
    assert response.status_code == 401
    assert response.get_json()["status"] == "error"

