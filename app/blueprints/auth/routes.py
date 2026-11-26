from flask import Blueprint, request, jsonify, current_app
from app.extensions import db, bcrypt
from app.models.user import User
from app.utils.jwt_helper import generate_access_token
from app.middlewares.auth_guard import token_required

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")
    phone_number = data.get("phone_number", "").strip() or None
    fcm_token = data.get("fcm_token")

    # Validasi input batas minimal & skema
    if not full_name or len(full_name) < 3:
        return jsonify({"status": "error", "message": "Nama lengkap minimal 3 karakter"}), 400
    if not email or "@" not in email:
        return jsonify({"status": "error", "message": "Format alamat email tidak valid"}), 400
    if not password or len(password) < 8:
        return jsonify({"status": "error", "message": "Kata sandi minimal 8 karakter"}), 400
    if not confirm_password:
        return jsonify({"status": "error", "message": "Konfirmasi kata sandi wajib diisi"}), 400
    if password != confirm_password:
        return jsonify({"status": "error", "message": "Kata sandi dan konfirmasi kata sandi tidak cocok"}), 400

    # Cek duplikasi email
    if User.query.filter_by(email=email).first():
        return jsonify({"status": "error", "message": "Email sudah terdaftar"}), 409

    # Enkripsi kata sandi menggunakan Bcrypt (12 rounds)
    hashed_password = bcrypt.generate_password_hash(password, rounds=12).decode("utf-8")

    new_user = User(
        full_name=full_name,
        email=email,
        password_hash=hashed_password,
        phone_number=phone_number,
        fcm_token=fcm_token
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Gagal mendaftarkan akun: {str(e)}"}), 500

    return jsonify({
        "status": "success",
        "message": "Registrasi akun berhasil",
        "data": {
            "id": str(new_user.id),
            "full_name": new_user.full_name,
            "email": new_user.email,
            "created_at": new_user.created_at.isoformat()
        }
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email dan kata sandi wajib diisi"}), 400

    user = User.query.filter_by(email=email).first()

    # Verifikasi keberadaan akun dan kecocokan hash sandi
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"status": "error", "message": "Email atau kata sandi salah"}), 401

    if not user.is_active:
        return jsonify({"status": "error", "message": "Akun Anda telah dinonaktifkan"}), 403

    # Perbarui fcm_token jika dikirimkan dari mobile
    fcm_token = data.get("fcm_token")
    if fcm_token:
        user.fcm_token = fcm_token
        db.session.commit()

    token = generate_access_token(user)
    expires_in = int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds())

    return jsonify({
        "status": "success",
        "message": "Login berhasil",
        "data": {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "user": {
                "id": str(user.id),
                "full_name": user.full_name,
                "email": user.email,
                "phone_number": user.phone_number
            }
        }
    }), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user_profile(current_user):
    return jsonify({
        "status": "success",
        "message": "Profil pengguna berhasil dimuat",
        "data": {
            "id": str(current_user.id),
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone_number": current_user.phone_number,
            "created_at": current_user.created_at.isoformat()
        }
    }), 200


@auth_bp.route("/profile", methods=["PUT"], strict_slashes=False)
@token_required
def update_profile(current_user):
    payload = request.get_json(silent=True) or {}
    full_name = payload.get("full_name")
    phone_number = payload.get("phone_number")
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")

    # Jika ingin mengganti kata sandi
    if new_password:
        if not current_password:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_INPUT_SCHEMA",
                "message": "Kata sandi saat ini (current_password) wajib diisi untuk mengubah kata sandi baru",
                "details": ["Field 'current_password' tidak boleh kosong jika 'new_password' diisi"]
            }), 400

        if not bcrypt.check_password_hash(current_user.password_hash, current_password):
            return jsonify({
                "status": "error",
                "error_code": "INVALID_CREDENTIALS",
                "message": "Kata sandi lama tidak sesuai",
                "details": ["Kata sandi saat ini yang Anda masukkan salah"]
            }), 400

        if len(new_password) < 8:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_INPUT_SCHEMA",
                "message": "Kata sandi baru minimal 8 karakter",
                "details": ["Panjang 'new_password' harus minimal 8 karakter"]
            }), 400

        current_user.password_hash = bcrypt.generate_password_hash(new_password, rounds=12).decode("utf-8")

    if full_name is not None and isinstance(full_name, str) and full_name.strip():
        current_user.full_name = full_name.strip()

    if phone_number is not None and isinstance(phone_number, str):
        current_user.phone_number = phone_number.strip()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "error_code": "DATABASE_ERROR",
            "message": "Gagal memperbarui profil pengguna",
            "details": [str(e)]
        }), 500

    return jsonify({
        "status": "success",
        "message": "Profil berhasil diperbarui",
        "data": {
            "id": str(current_user.id),
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone_number": current_user.phone_number,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    }), 200


@auth_bp.route("/fcm-token", methods=["POST"], strict_slashes=False)
@token_required
def update_fcm_token(current_user):
    payload = request.get_json(silent=True) or {}
    fcm_token = payload.get("fcm_token")

    if not fcm_token or not isinstance(fcm_token, str) or not fcm_token.strip():
        return jsonify({
            "status": "error",
            "error_code": "INVALID_INPUT_SCHEMA",
            "message": "Field 'fcm_token' wajib diisi",
            "details": ["Token FCM tidak boleh kosong"]
        }), 400

    current_user.fcm_token = fcm_token.strip()
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "error_code": "DATABASE_ERROR",
            "message": "Gagal menyimpan token FCM",
            "details": [str(e)]
        }), 500

    return jsonify({
        "status": "success",
        "message": "Token FCM berhasil disinkronkan"
    }), 200


@auth_bp.route("/logout", methods=["POST"], strict_slashes=False)
@token_required
def logout(current_user):
    # Hapus token FCM jika tersimpan saat pengguna keluar
    if current_user.fcm_token:
        current_user.fcm_token = None
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    return jsonify({
        "status": "success",
        "message": "Berhasil logout dari sistem"
    }), 200

