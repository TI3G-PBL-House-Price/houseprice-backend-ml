import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db

class PredictionLog(db.Model):
    __tablename__ = "prediction_logs"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    city = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    surface_area = db.Column(db.Numeric(8, 2), nullable=False)
    building_area = db.Column(db.Numeric(8, 2), nullable=False)
    bed = db.Column(db.Integer, nullable=False)
    bath = db.Column(db.Integer, nullable=False)
    carport = db.Column(db.Integer, nullable=False)
    predicted_price = db.Column(db.Numeric(18, 2), nullable=False)
    model_version = db.Column(db.String(20), nullable=False)
    latency_ms = db.Column(db.Integer, nullable=True)
    client_ip = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index("idx_prediction_logs_created_at", db.text("created_at DESC")),
        db.Index("idx_prediction_logs_user_id", "user_id", db.text("created_at DESC")),
        db.CheckConstraint("surface_area >= 1", name="chk_pred_surface_area"),
        db.CheckConstraint("building_area >= 1", name="chk_pred_building_area"),
        db.CheckConstraint("bed >= 0", name="chk_pred_bed"),
        db.CheckConstraint("bath >= 0", name="chk_pred_bath"),
        db.CheckConstraint("carport >= 0", name="chk_pred_carport"),
        db.CheckConstraint("predicted_price >= 0", name="chk_pred_price"),
        db.CheckConstraint("latency_ms >= 0", name="chk_pred_latency"),
    )

    def __repr__(self):
        return f"<PredictionLog {self.predicted_price}>"


class SystemAuditLog(db.Model):
    __tablename__ = "system_audit_logs"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey("admins.id", ondelete="RESTRICT"), nullable=False, index=True)
    action_type = db.Column(db.String(50), nullable=False)
    module_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
    db.Index("idx_audit_logs_created_at", db.text("created_at DESC")),
)

    def __repr__(self):
        return f"<SystemAuditLog {self.action_type}>"