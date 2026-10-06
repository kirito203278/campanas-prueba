"""Genera el PDF y TXT de entrega a partir de backend/seed_credentials.txt.
Uso: python generar_credenciales_entrega.py
"""
import re
from pathlib import Path

from app.reports.credenciales_pdf import generar_pdf_credenciales, generar_txt_credenciales

SRC = Path(__file__).parent / "seed_credentials.txt"
LINE_RE = re.compile(r"^(?P<username>\S+)\s+(?P<password>\S+)\s+\(rol=(?P<rol>\w+)")

NOMBRES = {
    "kori": "Kori", "saray": "Saray", "uriel": "Uriel", "alondra": "Alondra",
    "fatima": "Fátima", "luz.cm": "Luz (CM)", "luz.admin": "Luz (Admin)",
}


def main():
    usuarios = []
    for line in SRC.read_text(encoding="utf-8").splitlines():
        m = LINE_RE.match(line.strip())
        if not m:
            continue
        username = m.group("username")
        usuarios.append({
            "nombre": NOMBRES.get(username, username),
            "username": username,
            "password": m.group("password"),
            "rol": m.group("rol"),
        })

    out_pdf = Path(__file__).parent / "credenciales_entrega.pdf"
    out_txt = Path(__file__).parent / "credenciales_entrega.txt"
    generar_pdf_credenciales(usuarios, out_pdf)
    generar_txt_credenciales(usuarios, out_txt)
    print(f"Generados: {out_pdf} y {out_txt}")


if __name__ == "__main__":
    main()
