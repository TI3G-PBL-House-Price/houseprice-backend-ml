from datetime import datetime
from app.extensions import db

class MasterLocation(db.Model):
    __tablename__ = "master_locations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    city = db.Column(db.String(50), nullable=False, index=True)
    district = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index("idx_master_locations_lookup", "city", "is_active"),
    )

    def __repr__(self):
        return f"<MasterLocation {self.district}, {self.city}>"


class MarketStatistic(db.Model):
    __tablename__ = "market_statistics"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    city = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(50), nullable=True)
    avg_price = db.Column(db.Numeric(18, 2), nullable=False)
    avg_price_per_sqm = db.Column(db.Numeric(18, 2), nullable=False)
    avg_surface_area = db.Column(db.Numeric(8, 2), nullable=False)
    avg_building_area = db.Column(db.Numeric(8, 2), nullable=False)
    total_properties = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index("idx_market_stats_location", "city", "district"),
        db.CheckConstraint("avg_price >= 0", name="chk_market_avg_price"),
        db.CheckConstraint("avg_price_per_sqm >= 0", name="chk_market_avg_sqm"),
        db.CheckConstraint("avg_surface_area > 0", name="chk_market_surface_area"),
        db.CheckConstraint("avg_building_area > 0", name="chk_market_building_area"),
        db.CheckConstraint("total_properties > 0", name="chk_market_total_properties"),
    )

    def __repr__(self):
        return f"<MarketStatistic {self.city} - {self.district}>"