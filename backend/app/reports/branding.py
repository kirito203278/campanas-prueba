"""Identidad de marca INNquietus compartida por todos los PDF generados
(credenciales, reporte mensual). Colores tomados del logo de la agencia."""
from pathlib import Path

from reportlab.lib.colors import HexColor

LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"

PURPLE = HexColor('#4b2a82')
PURPLE_DARK = HexColor('#2b1749')
YELLOW = HexColor('#ffde00')
ORANGE = HexColor('#ff6a1a')
INK = HexColor('#1c1524')
INK_LIGHT = HexColor('#7c7286')
BORDER = HexColor('#e3ddee')
SURFACE_ALT = HexColor('#f7f2fd')

# Semáforo de rendimiento (mismos tonos que las badges del frontend)
GOOD = HexColor('#1f9d55')
WARN = HexColor('#e2530a')
BAD = HexColor('#c62828')

AGENCIA_NOMBRE = 'INNquietus'
