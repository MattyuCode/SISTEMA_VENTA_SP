# ── Colores Soluciones Plus ───────────────────────────────────────────────────
import os
import sys

NAVY      = "#0d2b55"
ORANGE    = "#F97316"
WHITE1     = "#3d3d3d"
WHITE     = "#ffffff"
GRAY_BG   = "#f4f6fb"
BORDER    = "#e2e8f0"
TEXT_MAIN = "#0d2b55"
TEXT_MUTED= "#8a94a6"



def recurso(ruta_relativa):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_relativa)
    return os.path.join(os.path.abspath("."), ruta_relativa)