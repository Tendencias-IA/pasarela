"""Prueba de carga nocturna (RNF-02). Cada HU añade sus tareas.

Ejecutar: locust -f tests/load/locustfile.py --headless -u 20 -r 5 --run-time 3m --host http://127.0.0.1:5000
"""

from uuid import uuid4

from locust import HttpUser, between, task


class WalletUser(HttpUser):
    wait_time = between(0.5, 2)

    @task
    def health(self) -> None:
        self.client.get("/health", name="GET /health")

    # Activar (peso > 0) cuando HU-02 provea inicio de sesión en Locust (on_start con login).
    @task(0)
    def recharge(self) -> None:
        """HU-08 CA-10, RNF-02.3: p95 <= 3 s con 20 usuarios."""
        self.client.post(
            "/api/v1/wallet/recharges",
            json={"amount": "50000.00"},
            headers={"X-Requested-With": "fetch", "Idempotency-Key": str(uuid4())},
            name="POST /api/v1/wallet/recharges",
        )
