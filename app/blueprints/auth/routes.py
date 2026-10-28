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
