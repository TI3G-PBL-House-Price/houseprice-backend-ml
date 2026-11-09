import uuid

def test_register_and_login_flow(client):
    """Memverifikasi siklus registrasi, login JWT, dan akses /me."""
    unique_email = f"test_{uuid.uuid4().hex[:6]}@houseprice.id"
    register_payload = {
        "full_name": "Pengguna Uji Coba",
        "email": unique_email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "phone_number": "08123456789"
    }

    # 1. Registrasi Akun Baru
    reg_res = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.get_json()
    assert reg_data["status"] == "success"
    assert reg_data["data"]["email"] == unique_email

    # 2. Login Akun Baru
    login_payload = {
        "email": unique_email,
        "password": "Password123!"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.get_json()
    assert login_data["status"] == "success"
    assert "access_token" in login_data["data"]
    assert login_data["data"]["token_type"] == "Bearer"
    token = login_data["data"]["access_token"]

    # 3. Akses Profil /me dengan Bearer Token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    me_data = me_res.get_json()
    assert me_data["status"] == "success"
    assert me_data["data"]["email"] == unique_email


def test_login_invalid_password(client):
    """Memverifikasi login ditolak jika kata sandi salah (401)."""
    res = client.post("/api/v1/auth/login", json={
        "email": "budi.santoso@gmail.com",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    data = res.get_json()
    assert data["status"] == "error"


def test_auth_me_unauthorized(client):
    """Memverifikasi endpoint /me menolak akses tanpa token (401)."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    data = res.get_json()
    assert data["status"] == "error"

