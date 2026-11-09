import os
import io
import uuid
import pytest
from app.extensions import db
from app.models.ml import DatasetMetadata
from app.models.log import SystemAuditLog

def login_admin(client, identity="admin_hanif", password="Admin123!"):
    """Helper untuk mengautentikasi sesi administrator."""
    return client.post("/admin/login", data={
        "identity": identity,
        "password": password
    }, follow_redirects=True)


def test_admin_dashboard_renders_dataset_manager(client):
    """Memverifikasi tab Dataset Manager dan Pratinjau Tabular dirender pada dashboard."""
    login_admin(client)
    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Dataset Manager" in html
    assert "PRATINJAU STRUKTUR DATA TABULAR" in html
    assert "UNGGAH DATASET CSV" in html


def test_admin_upload_dataset_success(client, app):
    """
    Memverifikasi unggah berkas CSV baru:
    - File tersimpan di uploads/datasets
    - Metadata tercatat di dataset_metadata
    - Audit log tercatat di system_audit_logs
    """
    login_admin(client)

    csv_content = (
        b"city,district,surface_area,building_area,bed,bath,carport,price\n"
        b"Jakarta Selatan,Kebayoran Baru,180.0,220.0,4,3,2,7200000000\n"
        b"Jakarta Barat,Kebon Jeruk,110.0,120.0,3,2,1,2650000000\n"
    )
    unique_filename = f"upload_test_{uuid.uuid4().hex[:6]}.csv"
    data = {
        "dataset_file": (io.BytesIO(csv_content), unique_filename),
        "split_ratio": "80:20"
    }

    response = client.post(
        "/admin/dataset/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "berhasil diunggah" in html

    # Verifikasi record di database
    with app.app_context():
        record = DatasetMetadata.query.filter_by(file_name=unique_filename).first()
        assert record is not None
        assert record.total_records == 2
        assert record.file_size_bytes == len(csv_content)

        audit = SystemAuditLog.query.filter_by(action_type="DATASET_UPLOAD").order_by(SystemAuditLog.created_at.desc()).first()
        assert audit is not None
        assert unique_filename in audit.description

        # Cleanup berkas sementara dan record uji coba agar direktori datasets tetap bersih
        uploaded_path = os.path.join(app.root_path, "..", "uploads", "datasets", unique_filename)
        if os.path.exists(uploaded_path):
            try:
                os.remove(uploaded_path)
            except OSError:
                pass
        db.session.delete(record)
        db.session.delete(audit)
        db.session.commit()


def test_admin_upload_dataset_invalid_format(client):
    """Memverifikasi penolakan berkas non-CSV (ekstensi salah)."""
    login_admin(client)

    txt_content = b"This is not a CSV file"
    data = {
        "dataset_file": (io.BytesIO(txt_content), "invalid_file.txt"),
        "split_ratio": "80:20"
    }

    response = client.post(
        "/admin/dataset/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Format berkas tidak valid" in html


def test_admin_upload_dataset_unauthorized(client):
    """Memverifikasi endpoint unggah dataset memproteksi akses tanpa sesi login."""
    # Tanpa login
    data = {
        "dataset_file": (io.BytesIO(b"a,b,c\n1,2,3\n"), "test.csv")
    }
    response = client.post(
        "/admin/dataset/upload",
        data=data,
        content_type="multipart/form-data"
    )
    # Redirect ke /admin/login
    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]

