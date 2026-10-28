import jwt
from functools import wraps
from flask import request, jsonify, current_app
from app.models.user import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({
                "status": "error",
                "message": "Header Authorization diperlukan untuk mengakses endpoint ini"
            }), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({
                "status": "error",
                "message": "Format header otentikasi tidak valid. Gunakan format 'Bearer <token>'"
            }), 401

        token = parts[1]
        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"]
            )
            user_id = payload.get("user_id")
            current_user = User.query.filter_by(id=user_id, is_active=True).first()

            if not current_user:
                return jsonify({
                    "status": "error",
                    "message": "Pengguna tidak ditemukan atau akun telah dinonaktifkan"
                }), 401

        except jwt.ExpiredSignatureError:
            return jsonify({
                "status": "error",
                "message": "Sesi token telah kedaluwarsa, silakan masuk kembali"
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                "status": "error",
                "message": "Tanda tangan token tidak valid atau telah dimanipulasi"
            }), 401
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Terjadi kesalahan otentikasi: {str(e)}"
            }), 401

        return f(current_user, *args, **kwargs)

    return decorated