import uuid
import pytest
from app.extensions import db
from app.models.notification import Notification

def get_auth_token(client, email=None, password="Password123!"):
    """Helper untuk mendaftarkan dan me-login-kan user pengujian."""
    if email is None:
        email = f"user_{uuid.uuid4().hex[:8]}@test.com"
    
    register_payload = {
        "full_name": "Test Profile User",
        "email": email,
        "password": password,
        "confirm_password": password,
        "phone_number": "08123456789"
    }
    reg_res = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201

    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    token = login_res.get_json()["data"]["access_token"]
    user_id = login_res.get_json()["data"]["user"]["id"]
    return token, user_id, email


# ============================================================================
# TEST SUITE: USER PROFILE, FCM TOKEN & LOGOUT
# ============================================================================

def test_update_profile_info(client):
    """Memverifikasi pembaruan data profil nama dan nomor telepon."""
    token, _, _ = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "full_name": "Budi Santoso Updated",
        "phone_number": "089876543210"
    }
    response = client.put("/api/v1/auth/profile", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["data"]["full_name"] == "Budi Santoso Updated"
    assert data["data"]["phone_number"] == "089876543210"


def test_update_password_flow(client):
    """Memverifikasi alur penggantian kata sandi (sukses, sandi lama salah, sandi baru pendek)."""
    old_pass = "OldPassword123!"
    token, _, email = get_auth_token(client, password=old_pass)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Sandi lama salah -> 400
    wrong_payload = {
        "current_password": "WrongCurrentPassword!",
        "new_password": "NewValidPassword456!"
    }
    res_wrong = client.put("/api/v1/auth/profile", json=wrong_payload, headers=headers)
    assert res_wrong.status_code == 400
    assert res_wrong.get_json()["error_code"] == "INVALID_CREDENTIALS"

    # 2. Sandi baru kurang dari 8 karakter -> 400
    short_payload = {
        "current_password": old_pass,
        "new_password": "short"
    }
    res_short = client.put("/api/v1/auth/profile", json=short_payload, headers=headers)
    assert res_short.status_code == 400
    assert res_short.get_json()["error_code"] == "INVALID_INPUT_SCHEMA"

    # 3. Sukses ganti kata sandi baru
    new_pass = "NewValidPassword456!"
    valid_payload = {
        "current_password": old_pass,
        "new_password": new_pass
    }
    res_valid = client.put("/api/v1/auth/profile", json=valid_payload, headers=headers)
    assert res_valid.status_code == 200

    # 4. Verifikasi login dengan kata sandi baru
    login_new = client.post("/api/v1/auth/login", json={"email": email, "password": new_pass})
    assert login_new.status_code == 200


def test_fcm_token_sync(client):
    """Memverifikasi sinkronisasi FCM token perangkat pengguna."""
    token, _, _ = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Sukses sinkronisasi
    res = client.post("/api/v1/auth/fcm-token", json={"fcm_token": "fcm_sample_token_xyz_123"}, headers=headers)
    assert res.status_code == 200
    assert res.get_json()["status"] == "success"

    # Gagal tanpa field fcm_token
    res_empty = client.post("/api/v1/auth/fcm-token", json={}, headers=headers)
    assert res_empty.status_code == 400
    assert res_empty.get_json()["error_code"] == "INVALID_INPUT_SCHEMA"


def test_auth_logout(client):
    """Memverifikasi endpoint POST /api/v1/auth/logout."""
    token, _, _ = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/v1/auth/logout", headers=headers)
    assert res.status_code == 200
    assert res.get_json()["status"] == "success"


# ============================================================================
# TEST SUITE: IN-APP NOTIFICATIONS
# ============================================================================

def test_get_notifications_and_mark_as_read(client, app):
    """
    Memverifikasi pengambilan daftar notifikasi pengguna (dengan unread_count),
    penandaan notifikasi telah dibaca, dan isolasi notifikasi antar-user.
    """
    token_a, user_a_id, _ = get_auth_token(client)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Buat 2 notifikasi dummy untuk user A di DB
    with app.app_context():
        notif1 = Notification(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_a_id),
            title="Tren Pasar Jakarta Selatan",
            message="Harga rata-rata properti di Tebet naik 2.5%",
            type="MARKET_TREND",
            is_read=False
        )
        notif2 = Notification(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_a_id),
            title="Model Baru Diaktifkan",
            message="Model regresi v1.0.0 siap digunakan",
            type="SYSTEM",
            is_read=False
        )
        db.session.add_all([notif1, notif2])
        db.session.commit()
        notif1_id = str(notif1.id)

    # 1. Ambil notifikasi User A
    get_res = client.get("/api/v1/notifications", headers=headers_a)
    assert get_res.status_code == 200
    data = get_res.get_json()["data"]
    assert data["unread_count"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] in ["Tren Pasar Jakarta Selatan", "Model Baru Diaktifkan"]

    # 2. Tandai notif1 sebagai telah dibaca
    read_res = client.patch(f"/api/v1/notifications/{notif1_id}/read", headers=headers_a)
    assert read_res.status_code == 200
    assert read_res.get_json()["status"] == "success"

    # 3. Verifikasi unread_count berkurang menjadi 1
    get_res_after = client.get("/api/v1/notifications", headers=headers_a)
    assert get_res_after.status_code == 200
    assert get_res_after.get_json()["data"]["unread_count"] == 1

    # 4. User B mencoba menandai notif milik User A -> 404 (RESOURCE_NOT_FOUND)
    token_b, _, _ = get_auth_token(client)
    headers_b = {"Authorization": f"Bearer {token_b}"}
    read_res_other = client.patch(f"/api/v1/notifications/{notif1_id}/read", headers=headers_b)
    assert read_res_other.status_code == 404
    assert read_res_other.get_json()["error_code"] == "RESOURCE_NOT_FOUND"


def test_notifications_unauthorized(client):
    """Memverifikasi akses notifikasi tanpa token ditolak (401)."""
    res = client.get("/api/v1/notifications")
    assert res.status_code == 401
    assert res.get_json()["status"] == "error"

