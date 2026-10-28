import jwt
from datetime import datetime, timezone
from flask import current_app

def generate_access_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "iat": now,
        "exp": now + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")