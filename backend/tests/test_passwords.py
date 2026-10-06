"""Generación de credenciales y derivación de usernames."""
import string

from app.security.passwords import (
    build_username,
    generate_secure_password,
    hash_password,
    slugify_username_part,
    verify_password,
)


def test_password_generada_cumple_complejidad():
    for _ in range(20):
        p = generate_secure_password()
        assert len(p) >= 16
        assert any(c in string.ascii_uppercase for c in p)
        assert any(c in string.ascii_lowercase for c in p)
        assert any(c in string.digits for c in p)
        assert any(not c.isalnum() for c in p)


def test_minimo_16_aunque_se_pida_menos():
    assert len(generate_secure_password(8)) >= 16


def test_hash_y_verify():
    h = hash_password("Secreta-123")
    assert verify_password("Secreta-123", h)
    assert not verify_password("otra", h)


def test_slugify_quita_acentos_y_simbolos():
    assert slugify_username_part("Lúz Hernández!") == "luzhernandez"


def test_build_username_resuelve_colisiones():
    existentes = {"luz.hernandez"}
    # misma persona, rol distinto -> agrega el rol
    u = build_username("Luz", "Hernández", "admin", existentes)
    assert u == "luz.hernandez.admin"
    # si también existe el del rol, agrega sufijo numérico
    existentes.add("luz.hernandez.admin")
    u2 = build_username("Luz", "Hernández", "admin", existentes)
    assert u2 == "luz.hernandez2"
