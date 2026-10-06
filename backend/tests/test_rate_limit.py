"""Freno de fuerza bruta en memoria."""
from app.security import rate_limit


def test_bloquea_tras_cinco_intentos():
    k = "1.2.3.4|kori"
    for _ in range(4):
        rate_limit.registrar_intento_fallido(k)
    assert rate_limit.bloqueado(k) is False
    rate_limit.registrar_intento_fallido(k)
    assert rate_limit.bloqueado(k) is True


def test_claves_distintas_son_independientes():
    # Dos IPs distintas contra el mismo usuario NO se afectan entre sí:
    # así un tercero no puede bloquear la cuenta de un CM legítimo.
    victima = "9.9.9.9|kori"      # IP del CM legítimo
    atacante = "6.6.6.6|kori"     # IP del atacante
    for _ in range(5):
        rate_limit.registrar_intento_fallido(atacante)
    assert rate_limit.bloqueado(atacante) is True
    assert rate_limit.bloqueado(victima) is False


def test_limpiar_intentos():
    k = "1.1.1.1|luz"
    for _ in range(5):
        rate_limit.registrar_intento_fallido(k)
    rate_limit.limpiar_intentos(k)
    assert rate_limit.bloqueado(k) is False
