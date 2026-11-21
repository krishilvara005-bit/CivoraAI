import io

import pytest

from app import create_app

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "t.db"),
        "UPLOAD_DIR": str(tmp_path / "up"),
        "GEMINI_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "READ_ASYNC": False,
    })


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def project(client):
    return client.post("/api/projects", json={"name": "Patel Residence"}).get_json()


def upload(client, pid, name="plan.png", data=PNG):
    return client.post(f"/api/projects/{pid}/plan", data={"file": (io.BytesIO(data), name)},
                       content_type="multipart/form-data")
