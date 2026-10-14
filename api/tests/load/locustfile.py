"""Prueba de carga nocturna (RNF-02). Cada HU añade sus tareas.

Ejecutar (API con APP_CONFIG=e2e y usuarios de scripts/seed_test_user.py):
locust -f tests/load/locustfile.py --headless -u 20 -r 5 --run-time 3m --host http://127.0.0.1:5000
"""

from uuid import uuid4

from locust import HttpUser, between, task

PHONE = "3009876543"
PASSWORD = "Clave1234"  # noqa: S105 (credencial ficticia del usuario sembrado para pruebas)


class WalletUser(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self) -> None:
        """HU-02: la cookie de sesión queda en el cliente de Locust."""
        self.client.post(
            "/api/v1/auth/login",
            json={"phone": PHONE, "password": PASSWORD},
            headers={"X-Requested-With": "fetch"},
            name="POST /api/v1/auth/login",
        )

    @task
    def health(self) -> None:
        self.client.get("/health", name="GET /health")

    @task
    def recharge(self) -> None:
        """HU-08 CA-10, RNF-02.3: p95 <= 3 s con 20 usuarios."""
        self.client.post(
            "/api/v1/wallet/recharges",
            json={"amount": "50000.00"},
            headers={"X-Requested-With": "fetch", "Idempotency-Key": str(uuid4())},
            name="POST /api/v1/wallet/recharges",
        )

    @task
    def movements(self) -> None:
        """HU-09 CA-8, RNF-02.2: p95 <= 3 s con 20 usuarios."""
        self.client.get("/api/v1/movements?page=1", name="GET /api/v1/movements")

    @task(2)
    def wallet(self) -> None:
        """HU-05 CA-6, RNF-02.1: p95 <= 2 s con 20 usuarios."""
        self.client.get("/api/v1/wallet", name="GET /api/v1/wallet")

    @task
    def movements_filtered(self) -> None:
        """HU-10, RNF-02.2: el filtro por tipo no degrada el p95 de 3 s del historial."""
        self.client.get(
            "/api/v1/movements?type=recharge", name="GET /api/v1/movements?type=recharge"
        )
