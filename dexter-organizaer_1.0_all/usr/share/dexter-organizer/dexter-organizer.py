#!/usr/bin/env python3

import os
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Gio, GdkPixbuf
import fcntl
import socket

class DexterOrganizer(Gtk.Window):
    def __init__(self):
        super(DexterOrganizer, self).__init__(type=Gtk.WindowType.TOPLEVEL)
        self.theme = "light"  # Inicialización por defecto del tema
        # Definir rutas absolutas a los CSS de tema
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.light_theme = os.path.join(base_dir, "assets", "dexter_light.css")
        self.dark_theme = os.path.join(base_dir, "assets", "dexter_dark.css")
        # Crear el proveedor de CSS y cargar el tema claro por defecto
        self.css_provider = Gtk.CssProvider()
        if os.path.exists(self.light_theme):
            self.css_provider.load_from_path(self.light_theme)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Configuración de la ventana principal
        self.set_decorated(False)  # Sin decoraciones de ventana
        self.set_app_paintable(True)  # Permite dibujar esquinas redondeadas
        self.set_position(Gtk.WindowPosition.CENTER)  # Centrar ventana
        self.set_resizable(True)  # Permitir redimensionar
        self.set_size_request(950, 700)

        # El resto de la apariencia se controla por CSS externo
        self.connect("delete-event", Gtk.main_quit)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("button-press-event", self.on_window_drag)
        self.connect_after("button-press-event", self.on_global_click)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        self.connect("draw", self.on_draw)
        
        # Contenedor principal - Horizontal para dividir izquierda y derecha
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_container.set_name("main-container")
        
        # Contenedor izquierdo para header izquierdo y sidebar
        self.left_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.left_container.set_name("left-container")
        self.left_container.set_size_request(200, -1)
        
        # Contenedor derecho para header derecho y módulo principal
        self.right_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.right_container.set_name("right-container")
        self.right_container.set_hexpand(True)
        
        # Añadir contenedores izquierdo y derecho al contenedor principal
        self.main_container.pack_start(self.left_container, False, False, 0)
        self.main_container.pack_start(self.right_container, True, True, 0)
        
        # Crear los headers y añadirlos a sus respectivos contenedores
        self.create_headers()
        
        # Crear el sidebar y añadirlo al contenedor izquierdo
        self.create_sidebar()
        self.left_container.pack_start(self.sidebar_container, True, True, 0)
        
        # Crear el contenedor para el módulo actual y añadirlo al contenedor derecho
        self.module_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.module_container.set_name("module-container")
        self.module_container.set_hexpand(True)
        self.right_container.pack_start(self.module_container, True, True, 0)
        
        # Añadir el contenedor principal a la ventana
        self.add(self.main_container)
        
        # Crear buffer de texto para mensajes
        self.textbuffer = Gtk.TextBuffer()
        
        # Cargar el módulo de inicio por defecto
        self.load_start_module()
        
        # Mostrar todo
        self.show_all()
    
    def create_sidebar(self):
        """Crea el panel lateral izquierdo"""
        self.sidebar_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar_container.set_name("sidebar-container")
    
        # Añadir una lista para opciones del sidebar
        sidebar_options = Gtk.ListBox()
        sidebar_options.set_selection_mode(Gtk.SelectionMode.SINGLE)
        sidebar_options.set_name("sidebar-options")
        
        # Añadir algunas opciones de ejemplo
        option_items = ["Inicio", "Actualizaciones"]
        for i, option in enumerate(option_items):
            # Crear un contenedor para cada opción
            option_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            option_box.set_margin_start(10)
            option_box.set_margin_end(10)
            option_box.set_margin_top(20)
            option_box.set_margin_bottom(8)
            
            # Obtener un icono apropiado para cada opción
            icon_names = ["go-home-symbolic", "software-update-available-symbolic"]
            option_icon = Gtk.Image.new_from_icon_name(icon_names[i], Gtk.IconSize.MENU)
            option_label = Gtk.Label(label=f" {option}")
            option_label.set_halign(Gtk.Align.START)
            
            option_box.pack_start(option_icon, False, False, 5)
            option_box.pack_start(option_label, True, True, 5)
            
            # Hacer el contenedor de opción sensible al hover
            option_event_box = Gtk.EventBox()
            option_event_box.add(option_box)
            
            # Añadir la opción al ListBox
            sidebar_options.add(option_event_box)
        
        # Agregar todo al sidebar
        self.sidebar_container.pack_start(sidebar_options, False, False, 0)
    
    def load_start_module(self):
        """Carga el módulo de inicio en el contenedor"""
        # Importar el módulo
        from modules import dexter_start
        
        # Crear la instancia del módulo
        self.start_module = dexter_start.DexterStart()
        
        # Añadir al contenedor
        for child in self.module_container.get_children():
            self.module_container.remove(child)
        
        self.module_container.add(self.start_module)
        self.module_container.show_all()
    
    def on_inicio_clicked(self, widget):
        """Maneja el clic en el botón de inicio"""
        self.load_start_module()
    
    def create_headers(self):
        """Crea los headers izquierdo y derecho independientes"""
        # 1. HEADER IZQUIERDO
        self.header_left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.header_left.set_name("header-left")
        self.header_left.get_style_context().add_class("header-left")
       
        # Título/Logo "Dexter-Organizer"
        # Logo clicable: al pulsar, carga la pantalla de inicio
        logo_label = Gtk.Label()
        logo_label.set_markup("Dexter-Organizer")
        logo_label.set_name("logo-label")
        logo_label.set_margin_start(5)
        logo_label.set_margin_top(5)
        logo_label.set_margin_bottom(5)
        logo_eventbox = Gtk.EventBox()
        logo_eventbox.add(logo_label)
        logo_eventbox.connect("button-press-event", lambda w, e: self.load_start_module())
        
        # Agregar menú de edición al lado del logo
        # Botón y menú de edición (izquierda)
        self.edit_menu_button = Gtk.MenuButton()
        edit_icon = Gtk.Image.new_from_icon_name("view-more-symbolic", Gtk.IconSize.BUTTON)
        self.edit_menu_button.add(edit_icon)
        self.edit_menu_button.set_name("edit-menu-button")
        self.edit_menu_button.set_relief(Gtk.ReliefStyle.NONE)
        # Crear el menú de edición como Popover
        edit_popover = Gtk.Popover.new(self.edit_menu_button)
        edit_popover.set_modal(True)
        edit_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for label, callback in [("Añadir", self.on_add_action), ("Editar", self.on_edit_action), ("Eliminar", self.on_delete_action)]:
            btn = Gtk.ModelButton(label=label)
            btn.connect("clicked", lambda b, cb=callback: (edit_popover.hide(), cb(None, None)))
            edit_box.pack_start(btn, False, False, 0)
        edit_popover.add(edit_box)
        edit_box.show_all()
        self.edit_menu_button.set_popover(edit_popover)
        # Añadir logo y menú al contenedor izquierdo
        self.header_left.pack_start(logo_eventbox, True, True, 0)
        self.header_left.pack_start(self.edit_menu_button, False, False, 5)

        # Crear acciones para el menú
        action_group = Gio.SimpleActionGroup()
        
        add_action = Gio.SimpleAction.new("add", None)
        add_action.connect("activate", self.on_add_action)
        action_group.add_action(add_action)
        
        edit_action = Gio.SimpleAction.new("edit", None)
        edit_action.connect("activate", self.on_edit_action)
        action_group.add_action(edit_action)
        
        delete_action = Gio.SimpleAction.new("delete", None)
        delete_action.connect("activate", self.on_delete_action)
        action_group.add_action(delete_action)
        
        # Insertar grupo de acciones
        self.insert_action_group("app", action_group)
        
        # 2. HEADER DERECHO
        self.header_right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.header_right.set_name("header-right")
        self.header_right.set_hexpand(True)
        self.header_right.set_vexpand(False)
        self.header_right.get_style_context().add_class("header-right")
        
        # Buscador alineado a la izquierda y expandible
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Buscar...")
        self.search_entry.set_hexpand(True)
        self.search_entry.set_vexpand(False)
        self.search_entry.set_name("search-entry")
        
        # Contenedor para los botones de acción (derecha)
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        action_box.set_name("action-box")
        action_box.set_hexpand(False)
        action_box.set_vexpand(False)
        action_box.set_halign(Gtk.Align.END)
        action_box.set_margin_end(10)
        
        # Botón de Opciones (derecha)
        self.options_button = Gtk.Button()
        self.options_button.set_relief(Gtk.ReliefStyle.NONE)
        options_icon = Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON)
        self.options_button.add(options_icon)
        self.options_button.set_name("options-button")
        
        # Popover de opciones
        self.options_popover = Gtk.Popover.new(self.options_button)
        self.options_popover.set_modal(True)
        options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        options = [
            ("Preferencias", self.cb_preferences_dialog),
            ("Acerca de", self.cb_about)
        ]
        for label, handler in options:
            btn = Gtk.ModelButton(label=label)
            btn.connect("clicked", lambda b, cb=handler: (self.options_popover.hide(), cb(None, None)))
            options_box.pack_start(btn, False, False, 0)
        self.options_popover.add(options_box)
        options_box.show_all()
        self.options_button.connect("clicked", lambda b: self.options_popover.show_all() or self.options_popover.popup())
        
        # Botón de Maximizar
        max_btn = Gtk.Button()
        max_btn.set_relief(Gtk.ReliefStyle.NONE)
        max_icon = Gtk.Image.new_from_icon_name("window-maximize-symbolic", Gtk.IconSize.BUTTON)
        max_btn.add(max_icon)
        max_btn.set_name("max-button")
        max_btn.connect("clicked", self.on_max_clicked)
               
        # Botón de Cerrar
        close_btn = Gtk.Button()
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_icon = Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.BUTTON)
        close_btn.add(close_icon)
        close_btn.set_name("close-button")
        close_btn.connect("clicked", Gtk.main_quit)
        
        # Botón de icono para alternar tema claro/oscuro
        self.theme_button = Gtk.Button()
        self.theme_button.set_relief(Gtk.ReliefStyle.NONE)
        self.theme_button.set_name("theme-button")
        # Icono inicial según el tema
        if self.theme == "light":
            self.theme_button.set_image(Gtk.Image.new_from_icon_name("weather-clear-night-symbolic", Gtk.IconSize.BUTTON))
        else:
            self.theme_button.set_image(Gtk.Image.new_from_icon_name("display-brightness-symbolic", Gtk.IconSize.BUTTON))
        self.theme_button.connect("clicked", self.toggle_theme)

        theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        theme_box.pack_start(self.theme_button, False, False, 0)
        action_box.pack_start(theme_box, False, False, 3)

        # Añadir botones de acción al contenedor
        action_box.pack_start(self.options_button, False, False, 3)
        action_box.pack_start(max_btn, False, False, 3)
        action_box.pack_start(close_btn, False, False, 3)
        
        # Añadir buscador expandido a la izquierda y los botones pegados a la derecha
        self.header_right.pack_start(self.search_entry, True, True, 5)
        self.header_right.pack_end(action_box, False, False, 0)
        
        # Añadir los headers a sus respectivos contenedores
        self.left_container.pack_start(self.header_left, False, False, 0)
        self.right_container.pack_start(self.header_right, False, True, 0)

    def on_add_action(self, action, param):
        """Callback para la acción Añadir"""
        print("Acción: Añadir")
        self.append_text("Acción: Añadir\n")

    def on_edit_action(self, action, param):
        """Callback para la acción Editar"""
        print("Acción: Editar")
        self.append_text("Acción: Editar\n")

    def on_delete_action(self, action, param):
        """Callback para la acción Eliminar"""
        print("Acción: Eliminar")
        self.append_text("Acción: Eliminar\n")
    
    # Método para cambiar entre temas
    def toggle_theme(self, button):
        if self.theme == "light":
            # Cambiar a tema oscuro
            if os.path.exists(self.dark_theme):
                self.css_provider.load_from_path(self.dark_theme)
                self.theme = "dark"
                self.theme_button.set_image(Gtk.Image.new_from_icon_name("display-brightness-symbolic", Gtk.IconSize.BUTTON))
                # Forzar tema oscuro a nivel de aplicación
                style_manager = Adw.StyleManager.get_default()
                style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            else:
                print(f"Advertencia: No se pudo encontrar el archivo CSS: {self.dark_theme}")
        else:
            # Cambiar a tema claro
            if os.path.exists(self.light_theme):
                self.css_provider.load_from_path(self.light_theme)
                self.theme = "light"
                self.theme_button.set_image(Gtk.Image.new_from_icon_name("weather-clear-night-symbolic", Gtk.IconSize.BUTTON))
                # Forzar tema claro a nivel de aplicación
    
    def build_dexter_menu_popover(self):
        # Opciones como Popover para cierre automático
        options_popover = Gtk.Popover.new(self.options_button)
        options_popover.set_modal(True)
        options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        # Opciones del menú de la derecha
        options = [
            ("Preferencias", self.cb_preferences_dialog),
            ("Acerca de", self.cb_about)
        ]
        for label, handler in options:
            btn = Gtk.ModelButton(label=label)
            btn.connect("clicked", lambda b, cb=handler: (options_popover.hide(), cb(None, None)))
            options_box.pack_start(btn, False, False, 0)
        options_popover.add(options_box)
        options_box.show_all()
        self.options_button.set_popover(options_popover)

    def cb_preferences_dialog(self, action=None, param=None):
        print("Función: Mostrar preferencias")
        self.append_text("Función: Mostrar preferencias\n")

    def cb_about(self, action=None, param=None):
        # Importación local para evitar ciclos
        from modules.dexter_about import DexterAbout
        # Limpiar el contenedor principal
        for child in self.module_container.get_children():
            self.module_container.remove(child)
        # Crear y mostrar el widget DexterAbout
        about_widget = DexterAbout()
        self.module_container.pack_start(about_widget, True, True, 0)
        about_widget.show_all()
    
    def on_draw(self, widget, cr):
        # Dibujar esquinas redondeadas manteniendo el tema del sistema
        allocation = widget.get_allocation()
        width = allocation.width
        height = allocation.height
        
        # Radio de las esquinas redondeadas
        radius = 20
        
        # Obtener el color de fondo del tema actual
        context = widget.get_style_context()
        bg_color = context.get_background_color(Gtk.StateFlags.NORMAL)
        
        # Si la transparencia del color es 0, usar un color por defecto del tema
        if bg_color.alpha == 0:
            # Intentar obtener color del tema
            success, color = context.lookup_color("theme_bg_color")
            if success:
                bg_color = color
            else:
                # Color por defecto si no se puede obtener del tema
                bg_color = Gdk.RGBA(0.2, 0.2, 0.2, 1.0)
        
        # Dibujar rectángulo con esquinas redondeadas usando el color del tema
        cr.set_source_rgba(bg_color.red, bg_color.green, bg_color.blue, bg_color.alpha)
        
        # Crear la forma con esquinas redondeadas
        cr.move_to(0, radius)
        cr.arc(radius, radius, radius, 3.14, 4.71)  # Esquina superior izquierda
        cr.line_to(width - radius, 0)
        cr.arc(width - radius, radius, radius, 4.71, 6.28)  # Esquina superior derecha
        cr.line_to(width, height - radius)
        cr.arc(width - radius, height - radius, radius, 0, 1.57)  # Esquina inferior derecha
        cr.line_to(radius, height)
        cr.arc(radius, height - radius, radius, 1.57, 3.14)  # Esquina inferior izquierda
        cr.close_path()
        
        # Rellenar el rectángulo
        cr.fill()
        
        # Permitir que los widgets hijos se dibujen
        return False
    
    
    def on_window_drag(self, widget, event):
        # Función para permitir mover la ventana al hacer clic y arrastrar
        self.begin_move_drag(
            event.button,
            event.x_root,
            event.y_root,
            event.time
        )
        return True

    def on_global_click(self, widget, event):
        # Cierra los menús contextuales si están abiertos
        if self.edit_menu_button.get_popup().get_visible():
            self.edit_menu_button.popdown()
        if self.options_button.get_popup().get_visible():
            self.options_button.popdown()

    def on_max_clicked(self, button):
        if self.is_maximized():
            self.unmaximize()
        else:
            self.maximize()
            
def main():
    # Control de instancia única directamente aquí
    import socket
    import sys
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock_socket.bind(("127.0.0.1", 65432))
    except socket.error:
        print("Ya hay una instancia en ejecución. Mostrando ventana activa.")
        # Intentar traer ventana al frente usando wmctrl
        import subprocess
        import os
        try:
            # Buscar la ventana por nombre
            result = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if ("Dexter-Organizer" in line) or ("dexter-organizer.py" in line):
                    win_id = line.split()[0]
                    subprocess.run(["wmctrl", "-ia", win_id])
                    print("Ventana de Dexter-Organizer traída al frente.")
                    break
            else:
                print("No se pudo encontrar la ventana de Dexter-Organizer para enfocarla.")
        except FileNotFoundError:
            print("wmctrl no está instalado. Instálalo para activar la ventana existente automáticamente.")
        sys.exit(0)
    try:
        app = DexterOrganizer()
        Gtk.main()
    finally:
        lock_socket.close()

if __name__ == "__main__":
    main()
