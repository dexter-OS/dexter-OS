#!/usr/bin/env python3
import gi
import os
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, Gdk

from modules.dexter_config import ConfigView

def cargar_css(path_css):
    provider = Gtk.CssProvider()
    provider.load_from_path(path_css)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

class DexterOrganizer(Gtk.Application):

    def __init__(self):
        super().__init__(application_id="org.dexter.organizer",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)

        # Acciones del menú
        config_action = Gio.SimpleAction.new("config", None)
        config_action.connect("activate", self.mostrar_configuracion)
        self.add_action(config_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.mostrar_acerca_de)
        self.add_action(about_action)

    def on_activate(self, app):
        # Ruta recursos
        self.recursos_path = "/usr/share/dexter-organizer/resources"

        # Ventana principal
        self.window = Gtk.ApplicationWindow(application=app)
        self.window.set_title("DexterOrganizer")
        self.window.set_default_size(950, 700)
        self.window.set_resizable(False)

        # Carga de CSS base y claro
        cargar_css(os.path.join(self.recursos_path, "style.css"))
        cargar_css(os.path.join(self.recursos_path, "dexter-light", "light_style.css"))

        # Contenedor principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.window.set_child(main_box)

        # Panel lateral
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        sidebar.set_size_request(200, -1)
        sidebar.set_css_classes(["sidebar"])

        title_label = Gtk.Label(label="DexterOrganizer")
        title_label.set_css_classes(["sidebar-title"])
        subtitle_label = Gtk.Label(label="Organización de Documentos")
        subtitle_label.set_css_classes(["sidebar-subtitle"])

        sidebar.append(title_label)
        sidebar.append(subtitle_label)

        for i in range(3):
            btn = Gtk.Button(label=f"Categoría {i+1}")
            btn.set_css_classes(["sidebar-button"])
            sidebar.append(btn)

        # Contenido principal
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Barra superior
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.set_css_classes(["topbar"])
        header.set_margin_top(10)
        header.set_margin_bottom(10)
        header.set_margin_start(10)
        header.set_margin_end(10)

        btn_add = Gtk.Button(label="➕ Añadir")
        btn_edit = Gtk.Button(label="✏️ Editar")
        btn_delete = Gtk.Button(label="❌ Eliminar")

        spacer = Gtk.Box()
        spacer.set_hexpand(True)

        # Switch tema
        self.switch_tema = Gtk.Switch()
        self.switch_tema.set_active(False)
        self.switch_tema.connect("state-set", self.on_switch_tema)

        # Botón de menú personalizado (sin flecha)
        btn_menu = Gtk.MenuButton()
        btn_menu.set_icon_name("open-menu-symbolic")
        btn_menu.set_has_frame(False)

        # Crear menú popover estilizado
        menu_model = Gio.Menu()
        menu_model.append("Configuración", "app.config")
        menu_model.append("Acerca de", "app.about")

        popover_menu = Gtk.PopoverMenu()
        popover_menu.set_menu_model(menu_model)
        popover_menu.set_css_classes(["menu-popover"])
        btn_menu.set_popover(popover_menu)

        header.append(btn_add)
        header.append(btn_edit)
        header.append(btn_delete)
        header.append(spacer)
        header.append(self.switch_tema)
        header.append(btn_menu)

        # Área de contenido
        self.content_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.label_area = Gtk.Label(label="\n\nAquí se mostrará el contenido de los documentos.")
        self.content_area.append(self.label_area)

        # Ensamblado
        self.content_box.append(header)
        self.content_box.append(self.content_area)

        main_box.append(sidebar)
        main_box.append(self.content_box)

        self.window.present()

    def mostrar_configuracion(self, action, param):
        for child in self.content_area.get_children():
            self.content_area.remove(child)

        config_view = ConfigView()
        self.content_area.append(config_view)

    def mostrar_acerca_de(self, action, param):
        for child in self.content_area.get_children():
            self.content_area.remove(child)

        label = Gtk.Label(label="DexterOrganizer\nVersión 1.0\n(c) 2025 TuNombre")
        self.content_area.append(label)

    def on_switch_tema(self, switch, estado):
        if estado:
            ruta_css = os.path.join(self.recursos_path, "dexter-dark", "dark_style.css")
        else:
            ruta_css = os.path.join(self.recursos_path, "dexter-light", "light_style.css")

        cargar_css(ruta_css)
        return False

app = DexterOrganizer()
app.run()
