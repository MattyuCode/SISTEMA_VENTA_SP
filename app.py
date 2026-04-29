import os
import customtkinter as ctk
from PIL import Image
from datetime import datetime
from tkinter import ttk

from config import *
from frames.inicio         import InicioFrame
from frames.inventario     import InventarioFrame
from frames.nuevo_producto import NuevoProductoFrame
from frames.vender         import VenderFrame
from frames.historial      import HistorialFrame
from frames.observaciones  import ObservacionesFrame
from frames.fiados         import FiadosFrame

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

def apply_treeview_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview",
        background=WHITE, fieldbackground=WHITE,
        foreground="#374151", rowheight=26,
        borderwidth=0, font=("Segoe UI", 10))
    style.configure("Treeview.Heading",
        background=NAVY, foreground=WHITE,
        font=("Segoe UI", 10, "bold"), relief="flat", borderwidth=0)
    style.map("Treeview.Heading", background=[("active", ORANGE)])
    style.map("Treeview", background=[("selected", ORANGE)],
              foreground=[("selected", WHITE)])


class LibreriaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Librería - SOLUCIONES PLUS")
        self.geometry("1200x680")
        self.resizable(True, True)
        self.configure(fg_color=GRAY_BG)
        self.after(10, self._dark_titlebar)
        apply_treeview_style()

        self._build_sidebar()
        self._build_content()

    def _dark_titlebar(self):
        try:
            from ctypes import windll, byref, sizeof, c_int
            self.update()
            HWND = windll.user32.GetParent(self.winfo_id())
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            windll.dwmapi.DwmSetWindowAttribute(
                HWND, 20, byref(c_int(2)), sizeof(c_int))
            # forzar redibujado
            windll.user32.SetWindowPos(HWND, 0, 0, 0, 0, 0, 0x0027)
        except Exception:
            pass

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=195, corner_radius=0, fg_color=NAVY)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Cabecera centrada
        hdr = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(20, 14))

        icon_box = ctk.CTkFrame(hdr, width=64, height=64, corner_radius=14, fg_color=ORANGE)
        icon_box.pack(anchor="center")
        icon_box.pack_propagate(False)
        self._load_icon(icon_box)

        ctk.CTkLabel(hdr, text="Soluciones Plus",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=WHITE, justify="center").pack(anchor="center", pady=(10, 0))
        ctk.CTkLabel(hdr, text="Sistema de ventas",
                     font=ctk.CTkFont(size=11), text_color="gray60",
                     justify="center").pack(anchor="center")

        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").pack(fill="x", pady=4)

        # Navegación
        nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav.pack(fill="x", padx=10, pady=8)

        self.nav_buttons = {}
        items = [
            ("🏠  Inicio",           "inicio"),
            ("📦  Inventario",       "inventario"),
            ("➕  Nuevo producto",   "nuevo_producto"),
            ("🛒  Vender",           "vender"),
            ("💳  Fiados",           "fiados"),
            ("📋  Historial",        "historial"),
            ("📝  Observaciones",    "observaciones"),
        ]
        for label, key in items:
            btn = ctk.CTkButton(
                nav, text=label, width=170, height=36,
                anchor="w", corner_radius=8,
                fg_color="transparent", text_color="gray80",
                hover_color="#1a3d6e", font=ctk.CTkFont(size=13),
                command=lambda k=key: self.show_frame(k))
            btn.pack(pady=2)
            self.nav_buttons[key] = btn

        # Logo inferior
        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").pack(side="bottom", fill="x")
        self._load_footer_logo()

    def _load_icon(self, parent):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SP White.png")
        if os.path.exists(path):
            try:
                img = Image.open(path)
                img.thumbnail((54, 54), Image.LANCZOS)
                self._icon_img = ctk.CTkImage(light_image=img, dark_image=img,
                                               size=(img.width, img.height))
                ctk.CTkLabel(parent, image=self._icon_img, text="").place(
                    relx=0.5, rely=0.5, anchor="center")
                return
            except Exception:
                pass
        ctk.CTkLabel(parent, text="SP", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=WHITE).place(relx=0.5, rely=0.5, anchor="center")

    def _load_footer_logo(self):
        container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        container.pack(side="bottom", pady=14)
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SP White.png")
        if os.path.exists(path):
            try:
                img = Image.open(path)
                img.thumbnail((155, 70), Image.LANCZOS)
                self._footer_img = ctk.CTkImage(light_image=img, dark_image=img,
                                                 size=(img.width, img.height))
                ctk.CTkLabel(container, image=self._footer_img, text="").pack()
                return
            except Exception:
                pass
        ctk.CTkLabel(container, text="Pon logo.png\njunto al script",
                     text_color="gray50", font=ctk.CTkFont(size=10),
                     justify="center").pack()

    # ── Contenido ─────────────────────────────────────────────────────────────
    def _build_content(self):
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=GRAY_BG)
        self.content.pack(side="right", fill="both", expand=True)

        topbar = ctk.CTkFrame(self.content, height=52, corner_radius=0, fg_color=WHITE)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        # línea de acento izquierda
        ctk.CTkFrame(topbar, width=4, corner_radius=0,
                     fg_color=ORANGE).pack(side="left", fill="y")

        self.topbar_title = ctk.CTkLabel(topbar, text="Nueva venta",
            font=ctk.CTkFont(size=17, weight="bold"), text_color=NAVY)
        self.topbar_title.pack(side="left", padx=16)

        ctk.CTkLabel(topbar,
            text=f"Soluciones Plus  —  {datetime.now().strftime('%d/%m/%Y')}",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(side="right", padx=20)

        self.inner = ctk.CTkFrame(self.content, fg_color=GRAY_BG, corner_radius=0)
        self.inner.pack(fill="both", expand=True, padx=20, pady=16)

        self.frames = {
            "inicio":         InicioFrame(self.inner, self),
            "inventario":     InventarioFrame(self.inner, self),
            "nuevo_producto": NuevoProductoFrame(self.inner, self),
            "vender":         VenderFrame(self.inner, self),
            "fiados":         FiadosFrame(self.inner, self),
            "historial":      HistorialFrame(self.inner, self),
            "observaciones":  ObservacionesFrame(self.inner, self),
        }
        self.show_frame("vender")

    # ── Navegación ────────────────────────────────────────────────────────────
    def show_frame(self, key):
        titles = {
            "inicio":         "Panel principal",
            "inventario":     "Inventario",
            "nuevo_producto": "Registrar nuevo producto",
            "vender":         "Nueva venta",
            "fiados":         "Fiados / Deudas de clientes",
            "historial":      "Historial de ventas",
            "observaciones":  "Observaciones del día",
        }
        for f in self.frames.values():
            f.pack_forget()
        self.frames[key].pack(fill="both", expand=True)
        if hasattr(self.frames[key], "refresh"):
            self.frames[key].refresh()
        self.topbar_title.configure(text=titles.get(key, ""))
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=ORANGE, text_color=WHITE,
                              hover_color=ORANGE, font=ctk.CTkFont(size=13, weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color="gray80",
                              hover_color="#1a3d6e", font=ctk.CTkFont(size=13))