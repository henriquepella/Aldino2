from __future__ import annotations

import io
import time

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from scipy.spatial.distance import cdist


@pytest.fixture(scope="module")
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth() -> dict:
    # Login removido: a API opera com um único usuário implícito.
    return {}


@pytest.fixture(scope="module")
def small_xlsx() -> bytes:
    rng = np.random.default_rng(7)
    n = 70
    x = rng.uniform(0, 300, n)
    y = rng.uniform(0, 300, n)
    cov = np.exp(-cdist(np.c_[x, y], np.c_[x, y]) / 90.0) + 1e-8 * np.eye(n)
    base = np.linalg.cholesky(cov) @ rng.standard_normal(n)
    base = (base - base.mean()) / base.std()
    df = pd.DataFrame({
        "amostra": range(1, n + 1),
        "x": np.round(300000 + x, 2),
        "y": np.round(7500000 + y, 2),
        "teor": np.round(25 + 6 * base + rng.normal(0, 1, n), 2),
        "cota": np.round(500 + 8 * base + rng.normal(0, 0.5, n), 2),
    })
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as xw:
        df.to_excel(xw, index=False, sheet_name="dados")
    return buf.getvalue()


def test_project_dataset_run_flow(client, auth, small_xlsx):
    # --- projeto ---
    r = client.post("/api/projects", headers=auth, json={"name": "Projeto API", "client": "X"})
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # --- upload ---
    r = client.post(
        f"/api/projects/{pid}/datasets", headers=auth,
        files={"file": ("dados.xlsx", small_xlsx,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert r.status_code == 201, r.text
    ds = r.json()
    did = ds["id"]
    assert ds["row_count"] == 70
    assert ds["detection"]["coord_x"] == "x"
    assert ds["detection"]["coord_y"] == "y"

    # --- config ---
    cfg = {
        "x_col": "x", "y_col": "y", "crs": "EPSG:31982",
        "primary": "teor", "secondary": ["cota"], "explanatory": ["cota"],
        "aux_drift": "cota", "id_col": "amostra", "negatives_allowed": True,
        "bivariate_pairs": [], "advanced": {},
    }
    r = client.patch(f"/api/datasets/{did}/config", headers=auth, json={"config": cfg})
    assert r.status_code == 200, r.text
    assert r.json()["validation"]["can_proceed"] is True

    # --- run ---
    r = client.post(
        f"/api/projects/{pid}/runs", headers=auth,
        json={"dataset_id": did, "mode": "full",
              "advanced": {"n_permutations": 99, "grid_resolution": 18}},
    )
    assert r.status_code == 201, r.text
    rid = r.json()["id"]

    # --- poll ---
    deadline = time.time() + 240
    status = "pending"
    while time.time() < deadline:
        j = client.get(f"/api/runs/{rid}", headers=auth).json()
        status = j["status"]
        if status in ("done", "failed", "cancelled"):
            break
        time.sleep(2)
    assert status == "done", f"status={status} error={client.get(f'/api/runs/{rid}', headers=auth).json().get('error')}"

    j = client.get(f"/api/runs/{rid}", headers=auth).json()
    assert j["progress"] == 100.0
    assert j["metrics_summary"]["n_points"] == 70
    assert j["metrics_summary"].get("best_method")

    # --- results ---
    res = client.get(f"/api/runs/{rid}/results", headers=auth).json()
    assert len(res["steps"]) >= 8
    assert res["report_url"]
    assert res["package_url"]
    desc = next(s for s in res["steps"] if s["key"] == "descriptive")
    assert desc["tables"] and desc["figures"]

    # --- downloads ---
    pdf = client.get(f"/api/runs/{rid}/report.pdf", headers=auth)
    assert pdf.status_code == 200 and len(pdf.content) > 50_000
    zip_ = client.get(f"/api/runs/{rid}/package.zip", headers=auth)
    assert zip_.status_code == 200 and len(zip_.content) > 10_000
    xlsx = client.get(f"/api/runs/{rid}/tables.xlsx", headers=auth)
    assert xlsx.status_code == 200

    # --- IDs inexistentes retornam 404 ---
    assert client.get("/api/runs/nao-existe", headers=auth).status_code == 404
    assert client.get("/api/projects/nao-existe", headers=auth).status_code == 404


def test_reject_bad_upload(client, auth):
    r = client.post("/api/projects", headers=auth, json={"name": "P2"})
    pid = r.json()["id"]
    r = client.post(
        f"/api/projects/{pid}/datasets", headers=auth,
        files={"file": ("x.pdf", b"%PDF-1.4 garbage", "application/pdf")},
    )
    assert r.status_code == 400
