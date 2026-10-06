"""Login, rate limit por (IP, usuario) y aislamiento por CM en la API."""


def test_login_ok_y_credenciales_invalidas(api, crear_usuario):
    cm = crear_usuario("Kori", "kori", password="Clave-de-prueba-123")
    r = api.post("/api/auth/login", json={"username": "kori", "password": "Clave-de-prueba-123"})
    assert r.status_code == 200
    assert "access_token" in r.json()

    r2 = api.post("/api/auth/login", json={"username": "kori", "password": "mala"})
    assert r2.status_code == 401


def test_lockout_tras_cinco_fallos(api, crear_usuario):
    crear_usuario("Kori", "kori", password="Clave-de-prueba-123")
    h = {"X-Forwarded-For": "6.6.6.6"}
    for _ in range(5):
        api.post("/api/auth/login", json={"username": "kori", "password": "mala"}, headers=h)
    r = api.post("/api/auth/login", json={"username": "kori", "password": "mala"}, headers=h)
    assert r.status_code == 429


def test_lockout_no_afecta_a_la_victima_desde_otra_ip(api, crear_usuario):
    crear_usuario("Kori", "kori", password="Clave-de-prueba-123")
    atacante = {"X-Forwarded-For": "6.6.6.6"}
    for _ in range(6):
        api.post("/api/auth/login", json={"username": "kori", "password": "mala"}, headers=atacante)
    # La víctima, desde su propia IP y con su contraseña correcta, entra sin problema
    victima = {"X-Forwarded-For": "9.9.9.9"}
    r = api.post("/api/auth/login", json={"username": "kori", "password": "Clave-de-prueba-123"}, headers=victima)
    assert r.status_code == 200


def test_cm_no_ve_clientes_de_otro_cm(api, crear_usuario, fabrica, auth):
    kori = crear_usuario("Kori", "kori")
    saray = crear_usuario("Saray", "saray")
    cliente_de_saray = fabrica.cliente(saray, nombre="Cliente de Saray")

    headers = auth(kori)
    # Kori no debe poder abrir el detalle de un cliente que no es suyo
    r = api.get(f"/api/cm/clientes/{cliente_de_saray.id}", headers=headers)
    assert r.status_code == 404
    # Y su propia lista no incluye al cliente de Saray
    r2 = api.get("/api/cm/clientes", headers=headers)
    assert r2.status_code == 200
    assert all(c["nombre"] != "Cliente de Saray" for c in r2.json())
