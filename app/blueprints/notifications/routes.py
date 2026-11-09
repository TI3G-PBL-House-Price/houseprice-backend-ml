import uuid
from flask import Blueprint, jsonify
from app.extensions import db
from app.models.notification import Notification
from app.middlewares.auth_guard import token_required

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("", methods=["GET"], strict_slashes=False)
@notifications_bp.route("/", methods=["GET"], strict_slashes=False)
@token_required
def get_user_notifications(current_user):
    """
    GET /api/v1/notifications
    Strict Gate Protected: Mengambil seluruh notifikasi milik pengguna aktif
    beserta jumlah notifikasi yang belum dibaca (unread_count).
    """
    try:
        notifications = (
            Notification.query.filter_by(user_id=current_user.id)
            .order_by(Notification.created_at.desc())
            .all()
        )

        unread_count = sum(1 for n in notifications if not n.is_read)

        items = [
            {
                "id": str(n.id),
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None
            }
            for n in notifications
        ]

        return jsonify({
            "status": "success",
            "message": "Daftar notifikasi berhasil dimuat",
            "data": {
                "unread_count": unread_count,
                "items": items
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error_code": "DATABASE_ERROR",
            "message": "Gagal memuat notifikasi pengguna",
            "details": [str(e)]
        }), 500


@notifications_bp.route("/<uuid:id>/read", methods=["PATCH"], strict_slashes=False)
@token_required
def mark_notification_as_read(current_user, id):
    """
    PATCH /api/v1/notifications/<uuid:id>/read
    Strict Gate Protected: Menandai sebuah notifikasi telah dibaca (is_read = TRUE).
    Hanya dapat dilakukan jika notifikasi tersebut milik pengguna aktif.
    """
    try:
        notif = Notification.query.filter_by(id=id, user_id=current_user.id).first()

        if not notif:
            return jsonify({
                "status": "error",
                "error_code": "RESOURCE_NOT_FOUND",
                "message": "Notifikasi tidak ditemukan atau bukan milik pengguna aktif",
                "details": [f"Notifikasi dengan ID '{id}' tidak ditemukan pada akun Anda"]
            }), 404

        notif.is_read = True
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Status notifikasi berhasil diperbarui"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "error_code": "DATABASE_ERROR",
            "message": "Gagal memperbarui status notifikasi",
            "details": [str(e)]
        }), 500
