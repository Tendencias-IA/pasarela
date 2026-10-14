"""Prueba de carga nocturna (RNF-02). Hoy solo cubre /health; cada HU añade sus tareas.

Ejecutar: locust -f tests/load/locustfile.py --headless -u 20 -r 5 --run-time 3m --host http://127.0.0.1:5000
"""

from locust import HttpUser, between, task


class WalletUser(HttpUser):
    wait_time = between(0.5, 2)

    @task
    def health(self) -> None:
        self.client.get("/health", name="GET /health")
