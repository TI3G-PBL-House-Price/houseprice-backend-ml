import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions import db

class DatasetMetadata(db.Model):
    __tablename__ = "dataset_metadata"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    total_records = db.Column(db.Integer, nullable=False)
    file_size_bytes = db.Column(db.BigInteger, nullable=False)
    uploaded_by = db.Column(UUID(as_uuid=True), db.ForeignKey("admins.id", ondelete="RESTRICT"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.CheckConstraint("total_records > 0", name="chk_dataset_records"),
    )

    def __repr__(self):
        return f"<DatasetMetadata {self.file_name}>"


class MLModel(db.Model):
    __tablename__ = "ml_models"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    model_file_path = db.Column(db.String(500), nullable=False)
    algorithm_type = db.Column(db.String(50), nullable=False)
    r2_score = db.Column(db.Numeric(6, 4), nullable=False)
    mae_score = db.Column(db.Numeric(18, 2), nullable=False)
    rmse_score = db.Column(db.Numeric(18, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    trained_by = db.Column(UUID(as_uuid=True), db.ForeignKey("admins.id", ondelete="RESTRICT"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
    db.Index("idx_ml_models_active", "is_active", unique=True, postgresql_where=db.text("is_active = TRUE")),
    db.CheckConstraint("r2_score <= 1.0", name="chk_model_r2"),
    db.CheckConstraint("mae_score >= 0", name="chk_model_mae"),
    db.CheckConstraint("rmse_score >= 0", name="chk_model_rmse"),
)

    def __repr__(self):
        return f"<MLModel {self.model_name} {self.version}>"