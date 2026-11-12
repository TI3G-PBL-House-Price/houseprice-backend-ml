import pandas as pd
from app.extensions import db
from app.models import MasterLocation, MarketStatistic


class DatasetService:
    """Layanan pemrosesan berkas CSV dataset dan sinkronisasi lokasi & statistik pasar."""

    REQUIRED_BASE_COLUMNS = ("price", "city", "district")

    @staticmethod
    def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Menyamakan variasi penamaan kolom fitur antara skema dataset asli dan backend."""
        df = df.copy()
        df.columns = [str(col).strip() for col in df.columns]

        alias_pairs = [
            ("surface_area", "land_area"),
            ("building_area", "building_area"),
            ("bed", "bed_rooms"),
            ("bath", "bath_rooms"),
        ]
        for primary, alias in alias_pairs:
            if primary not in df.columns and alias in df.columns:
                df[primary] = df[alias]

        return df

    @classmethod
    def sync_locations_and_stats_from_csv(cls, file_path: str) -> tuple[int, int, int]:
        """
        Membaca CSV properti, memvalidasi kolom wajib, lalu menyinkronkan tabel
        `master_locations` dan `market_statistics` di PostgreSQL.

        Returns:
            Tuple (total_rows, total_locations, total_market_records)
        """
        df = pd.read_csv(file_path)
        total_rows = int(len(df))
        if total_rows == 0:
            raise ValueError("Berkas CSV kosong atau tidak memiliki baris data.")

        df = cls._normalize_columns(df)
        missing_cols = [
            col for col in (*cls.REQUIRED_BASE_COLUMNS, "surface_area", "building_area")
            if col not in df.columns
        ]
        if missing_cols:
            raise ValueError(
                f"Kolom wajib dataset tidak lengkap: {', '.join(missing_cols)}. "
                "Pastikan CSV memuat price, surface_area (atau land_area), building_area, district, dan city."
            )

        for num_col in ("price", "surface_area", "building_area"):
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

        df["city"] = df["city"].astype(str).str.strip().str.slice(0, 50)
        df["district"] = df["district"].astype(str).str.strip().str.slice(0, 50)

        df_clean = df.dropna(subset=["price", "surface_area", "building_area", "city", "district"]).copy()
        df_clean = df_clean[
            (df_clean["city"] != "")
            & (df_clean["city"].str.lower() != "nan")
            & (df_clean["district"] != "")
            & (df_clean["district"].str.lower() != "nan")
            & (df_clean["price"] >= 0)
            & (df_clean["surface_area"] > 0)
            & (df_clean["surface_area"] < 1_000_000)
            & (df_clean["building_area"] > 0)
            & (df_clean["building_area"] < 1_000_000)
        ].copy()

        if df_clean.empty:
            raise ValueError(
                "Tidak ada baris data valid setelah penyaringan nilai kosong atau luas <= 0."
            )

        df_clean["price_per_sqm"] = df_clean["price"] / df_clean["surface_area"]

        # Sinkronisasi master_locations
        locations_df = (
            df_clean[["city", "district"]]
            .drop_duplicates()
            .sort_values(by=["city", "district"])
        )
        MasterLocation.query.delete()
        for _, row in locations_df.iterrows():
            db.session.add(
                MasterLocation(
                    city=row["city"],
                    district=row["district"],
                    is_active=True,
                )
            )

        # Sinkronisasi market_statistics (agregasi level kota & kecamatan)
        MarketStatistic.query.delete()
        city_stats = df_clean.groupby("city", as_index=False).agg(
            avg_price=("price", "mean"),
            avg_price_per_sqm=("price_per_sqm", "mean"),
            avg_surface_area=("surface_area", "mean"),
            avg_building_area=("building_area", "mean"),
            total_properties=("price", "count"),
        )
        for _, r in city_stats.iterrows():
            db.session.add(
                MarketStatistic(
                    city=r["city"],
                    district=None,
                    avg_price=round(float(r["avg_price"]), 2),
                    avg_price_per_sqm=round(float(r["avg_price_per_sqm"]), 2),
                    avg_surface_area=round(float(r["avg_surface_area"]), 2),
                    avg_building_area=round(float(r["avg_building_area"]), 2),
                    total_properties=int(r["total_properties"]),
                )
            )

        district_stats = df_clean.groupby(["city", "district"], as_index=False).agg(
            avg_price=("price", "mean"),
            avg_price_per_sqm=("price_per_sqm", "mean"),
            avg_surface_area=("surface_area", "mean"),
            avg_building_area=("building_area", "mean"),
            total_properties=("price", "count"),
        )
        for _, r in district_stats.iterrows():
            db.session.add(
                MarketStatistic(
                    city=r["city"],
                    district=r["district"],
                    avg_price=round(float(r["avg_price"]), 2),
                    avg_price_per_sqm=round(float(r["avg_price_per_sqm"]), 2),
                    avg_surface_area=round(float(r["avg_surface_area"]), 2),
                    avg_building_area=round(float(r["avg_building_area"]), 2),
                    total_properties=int(r["total_properties"]),
                )
            )

        total_locations = int(len(locations_df))
        total_market_records = int(len(city_stats) + len(district_stats))
        return total_rows, total_locations, total_market_records

