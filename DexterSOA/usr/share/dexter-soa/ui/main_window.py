#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ventana principal de DexterSOA.
Gestiona la estructura principal de la interfaz y la navegación entre secciones.
"""

import os
import math
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango, GObject

from utils.utils import _, load_config, get_icons_path, get_data_path
from ui.update_tab import UpdateTab
from ui.cleanup_tab import CleanupTab
from ui.config_tab import ConfigTab
from ui.stats_tab import StatsTab

class MainWindow(Gtk.Window):
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        """Inicializar la ventana principal"""
        Gtk.Window.__init__(self, title="DexterSOA")
        
        # Establecer tamaño y posición (tamaño reducido)
        self.set_default_size(800, 550)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Cargar tema
        self.load_theme()
        
        # Contenedor principal
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.main_box)
        
        # Crear cabecera
        self.create_header()
        
        # Crear contenido principal
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_box.pack_start(self.content_box, True, True, 0)
        
        # Panel izquierdo (navegación)
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.sidebar.set_size_request(200, -1)
        self.sidebar.get_style_context().add_class("sidebar")
        self.content_box.pack_start(self.sidebar, False, False, 0)
        
        # Crear botones de navegación
        self.create_nav_buttons()
        
        # Panel derecho (contenido)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.get_style_context().add_class("content")
        self.content_box.pack_start(self.content, True, True, 0)
        
        # Crear pestañas
        self.create_tabs()
        
        # Mostrar pestaña inicial
        self.show_tab("inicio")
        
        # Verificar actualizaciones al inicio
        GLib.timeout_add(2000, self.check_updates_startup)
    
    def on_draw(self, widget, cr):
        """Dibujar el fondo de la ventana con esquinas redondeadas"""
        # Obtener dimensiones
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        
        # Dibujar fondo con esquinas redondeadas
        radius = 10
        cr.set_source_rgb(0.9, 0.9, 0.9)
        
        # Dibujar rectángulo con esquinas redondeadas
        cr.move_to(radius, 0)
        cr.line_to(width - radius, 0)
        cr.arc(width - radius, radius, radius, -90 * (3.14 / 180), 0)
        cr.line_to(width, height - radius)
        cr.arc(width - radius, height - radius, radius, 0, 90 * (3.14 / 180))
        cr.line_to(radius, height)
        cr.arc(radius, height - radius, radius, 90 * (3.14 / 180), 180 * (3.14 / 180))
        cr.line_to(0, radius)
        cr.arc(radius, radius, radius, 180 * (3.14 / 180), 270 * (3.14 / 180))
        cr.close_path()
        
        cr.fill()
        
        return False
    
    def load_theme(self):
        """Cargar el tema actual"""
        # Obtener tema de la configuración
        config = load_config()
        theme_name = config.get("theme", "light")  # Por defecto tema claro
        
        # Verificar que el tema es válido (light o dark)
        if theme_name not in ["light", "dark"]:
            theme_name = "light"  # Valor predeterminado en caso de error
        
        # Cargar archivo CSS externo
        css_provider = Gtk.CssProvider()
        theme_path = os.path.join(get_data_path(), "assets", "themes", f"{theme_name}.css")
        
        try:
            if os.path.exists(theme_path):
                css_provider.load_from_path(theme_path)
                print(f"Tema cargado desde: {theme_path}")
            else:
                # Fallback a CSS básico si el archivo no existe
                print(f"Archivo de tema no encontrado: {theme_path}")
                css = """
                    .header {
                        background-color: #A80030;
                        color: white;
                        padding: 10px;
                    }
                    
                    .header-title {
                        font-size: 20px;
                        font-weight: bold;
                    }
                """
                css_provider.load_from_data(css.encode())
        except Exception as e:
            print(f"Error al cargar tema: {e}")
        
        # Aplicar estilo
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Actualizar ruta de iconos para el tema
        self.icons_path = os.path.join(get_data_path(), "assets", "themes", "icons", theme_name)
        
        # Actualizar iconos en la interfaz si es necesario
        try:
            self.update_nav_button_icons()
        except Exception as e:
            print(f"Error al actualizar iconos: {e}")
    
    def create_header(self):
        """Crear la cabecera de la aplicación"""
        # Header box - reducido el tamaño y sin botón de cerrar
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        header_box.get_style_context().add_class("header")
        header_box.set_border_width(5)  # Reducido de 10 a 5
        self.main_box.pack_start(header_box, False, False, 0)
        
        # Logo con tamaño reducido
        try:
            config = load_config()
            theme_name = config.get("theme", "light")
            if theme_name not in ["light", "dark"]:
                theme_name = "light"
                
            logo_path = os.path.join(get_data_path(), "assets", "themes", "icons", theme_name, "dexter-soa.svg")
            
            if os.path.isfile(logo_path):
                logo = Gtk.Image.new_from_file(logo_path)
                logo.set_pixel_size(24)  # Reducido de 32 a 24
                header_box.pack_start(logo, False, False, 0)
            else:
                # Usar icono genérico si no encuentra el logo personalizado
                logo = Gtk.Image.new_from_icon_name("applications-system", Gtk.IconSize.SMALL_TOOLBAR)  # Cambiado a small
                header_box.pack_start(logo, False, False, 0)
        except Exception as e:
            print(f"Error al cargar logo: {e}")
        
        # Título
        title_label = Gtk.Label(label="DexterSOA")
        title_label.get_style_context().add_class("header-title")
        header_box.pack_start(title_label, False, False, 0)
        
        # Espaciador
        header_box.pack_start(Gtk.Label(label=""), True, True, 0)
        
        # Selector de tema
        theme_label = Gtk.Label(label=_("Tema:"))
        header_box.pack_start(theme_label, False, False, 0)
        
        theme_store = Gtk.ListStore(str, str)  # Nombre, ID
        theme_store.append([_("Claro"), "light"])
        theme_store.append([_("Oscuro"), "dark"])
        
        self.theme_combo = Gtk.ComboBox.new_with_model(theme_store)
        renderer_text = Gtk.CellRendererText()
        self.theme_combo.pack_start(renderer_text, True)
        self.theme_combo.add_attribute(renderer_text, "text", 0)
        
        # Establecer tema activo
        config = load_config()
        current_theme = config.get("theme", "dark")
        active_index = 0
        
        for i, row in enumerate(theme_store):
            if row[1] == current_theme:
                active_index = i
                break
        
        self.theme_combo.set_active(active_index)
        self.theme_combo.connect("changed", self.on_theme_changed)
        
        header_box.pack_start(self.theme_combo, False, False, 5)
        
        # Botón de menú
        menu_button = Gtk.Button()
        menu_icon = Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON)
        menu_button.add(menu_icon)
        menu_button.connect("clicked", self.on_menu_button_clicked)
        header_box.pack_start(menu_button, False, False, 0)
    
    def create_nav_buttons(self):
        """Crear botones de navegación"""
        # Crear contenedores para botones con iconos y texto
        
        # Botón de inicio
        self.btn_inicio = Gtk.Button()
        self.btn_inicio_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.btn_inicio_icon = Gtk.Image()
        self.btn_inicio_label = Gtk.Label(label=_("Inicio"))
        self.btn_inicio_box.pack_start(self.btn_inicio_icon, False, False, 5)
        self.btn_inicio_box.pack_start(self.btn_inicio_label, False, False, 0)
        self.btn_inicio.add(self.btn_inicio_box)
        self.btn_inicio.get_style_context().add_class("nav-button")
        self.btn_inicio.connect("clicked", self.on_nav_button_clicked, "inicio")
        self.sidebar.pack_start(self.btn_inicio, False, False, 0)
        
        # Botón de estadísticas
        self.btn_stats = Gtk.Button()
        self.btn_stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.btn_stats_icon = Gtk.Image()
        self.btn_stats_label = Gtk.Label(label=_("Estadísticas"))
        self.btn_stats_box.pack_start(self.btn_stats_icon, False, False, 5)
        self.btn_stats_box.pack_start(self.btn_stats_label, False, False, 0)
        self.btn_stats.add(self.btn_stats_box)
        self.btn_stats.get_style_context().add_class("nav-button")
        self.btn_stats.connect("clicked", self.on_nav_button_clicked, "stats")
        self.sidebar.pack_start(self.btn_stats, False, False, 0)
        
        # Botón de actualización
        self.btn_update = Gtk.Button()
        self.btn_update_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.btn_update_icon = Gtk.Image()
        self.btn_update_label = Gtk.Label(label=_("Actualización"))
        self.btn_update_box.pack_start(self.btn_update_icon, False, False, 5)
        self.btn_update_box.pack_start(self.btn_update_label, False, False, 0)
        self.btn_update.add(self.btn_update_box)
        self.btn_update.get_style_context().add_class("nav-button")
        self.btn_update.connect("clicked", self.on_nav_button_clicked, "update")
        self.sidebar.pack_start(self.btn_update, False, False, 0)
        
        # Botón de limpieza
        self.btn_cleanup = Gtk.Button()
        self.btn_cleanup_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.btn_cleanup_icon = Gtk.Image()
        self.btn_cleanup_label = Gtk.Label(label=_("Limpieza"))
        self.btn_cleanup_box.pack_start(self.btn_cleanup_icon, False, False, 5)
        self.btn_cleanup_box.pack_start(self.btn_cleanup_label, False, False, 0)
        self.btn_cleanup.add(self.btn_cleanup_box)
        self.btn_cleanup.get_style_context().add_class("nav-button")
        self.btn_cleanup.connect("clicked", self.on_nav_button_clicked, "cleanup")
        self.sidebar.pack_start(self.btn_cleanup, False, False, 0)
        
        # Botón de configuración
        self.btn_config = Gtk.Button()
        self.btn_config_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.btn_config_icon = Gtk.Image()
        self.btn_config_label = Gtk.Label(label=_("Configuración"))
        self.btn_config_box.pack_start(self.btn_config_icon, False, False, 5)
        self.btn_config_box.pack_start(self.btn_config_label, False, False, 0)
        self.btn_config.add(self.btn_config_box)
        self.btn_config.get_style_context().add_class("nav-button")
        self.btn_config.connect("clicked", self.on_nav_button_clicked, "config")
        self.sidebar.pack_start(self.btn_config, False, False, 0)
        
        # Actualizar iconos según el tema actual
        self.update_nav_button_icons()
        
        # Espaciador
        self.sidebar.pack_start(Gtk.Label(label=""), True, True, 0)
        
        # Versión
        version_label = Gtk.Label(label=_("Versión: 1.0.0"))
        version_label.set_alignment(0.5, 0.5)
        version_label.set_padding(5, 5)
        self.sidebar.pack_start(version_label, False, False, 10)
    
    def create_tabs(self):
        """Crear las pestañas de la aplicación"""
        # Crear pestañas
        self.tabs = {}
        
        # Pestaña de inicio
        self.tabs["inicio"] = self.create_inicio_tab()
        
        # Pestaña de estadísticas
        self.tabs["stats"] = StatsTab(self)
        
        # Pestaña de actualización
        self.tabs["update"] = UpdateTab(self)
        
        # Pestaña de limpieza
        self.tabs["cleanup"] = CleanupTab(self)
        
        # Pestaña de configuración
        self.tabs["config"] = ConfigTab(self)
        
        # Añadir todas las pestañas al contenedor
        for tab_name, tab in self.tabs.items():
            self.content.pack_start(tab, True, True, 0)
            tab.hide()
    
    def create_inicio_tab(self):
        """Crear la pestaña de inicio"""
        # Contenedor principal
        inicio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        inicio_box.set_border_width(20)
        
        # Banner
        banner_label = Gtk.Label()
        banner_label.set_markup(
            f"<span size='xx-large' weight='bold'>{_('Bienvenido a DexterSOA')}</span>"
        )
        inicio_box.pack_start(banner_label, False, False, 0)
        
        # Descripción
        desc_label = Gtk.Label()
        desc_label.set_markup(
            _("DexterSOA es una herramienta para la gestión de actualizaciones, ") +
            _("administración de paquetes APT, limpieza del sistema y notificaciones programadas.")
        )
        desc_label.set_line_wrap(True)
        desc_label.set_max_width_chars(80)
        inicio_box.pack_start(desc_label, False, False, 0)
        
        # Separador
        inicio_box.pack_start(Gtk.Separator(), False, False, 10)
        
        # Estado del sistema
        status_frame = Gtk.Frame(label=_("Estado del Sistema"))
        inicio_box.pack_start(status_frame, False, False, 0)
        
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        status_box.set_border_width(10)
        status_frame.add(status_box)
        
        # Etiqueta de actualizaciones
        self.updates_label = Gtk.Label()
        self.updates_label.set_markup(_("Comprobando actualizaciones..."))
        self.updates_label.set_alignment(0, 0.5)
        status_box.pack_start(self.updates_label, False, False, 0)
        
        # Botón de comprobar actualizaciones
        check_updates_button = Gtk.Button(label=_("Comprobar Actualizaciones"))
        check_updates_button.connect("clicked", self.on_check_updates_clicked)
        status_box.pack_start(check_updates_button, False, False, 5)
        
        # Acciones rápidas
        actions_frame = Gtk.Frame(label=_("Acciones Rápidas"))
        inicio_box.pack_start(actions_frame, True, True, 0)
        
        actions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        actions_box.set_border_width(10)
        actions_frame.add(actions_box)
        
        # Botones de acciones rápidas
        update_button = Gtk.Button(label=_("Actualizar Sistema"))
        update_button.connect("clicked", self.on_nav_button_clicked, "update")
        actions_box.pack_start(update_button, False, False, 0)
        
        cleanup_button = Gtk.Button(label=_("Limpiar Sistema"))
        cleanup_button.connect("clicked", self.on_nav_button_clicked, "cleanup")
        actions_box.pack_start(cleanup_button, False, False, 0)
        
        config_button = Gtk.Button(label=_("Configurar Sistema"))
        config_button.connect("clicked", self.on_nav_button_clicked, "config")
        actions_box.pack_start(config_button, False, False, 0)
        
        return inicio_box
    
    def check_updates_startup(self):
        """Verificar actualizaciones al iniciar"""
        self.on_check_updates_clicked()
        return False  # No repetir
    
    def on_check_updates_clicked(self, button=None):
        """Manejar clic en botón de verificar actualizaciones"""
        # Actualizar etiqueta
        self.updates_label.set_markup(_("Comprobando actualizaciones..."))
        
        # Comprobar actualizaciones en segundo plano
        def check_updates_thread():
            try:
                # Importar AptManager
                from utils.apt_manager import AptManager
                apt_manager = AptManager()
                
                # Obtener actualizaciones
                updates = apt_manager.get_updates()
                
                # Actualizar UI en el hilo principal
                GLib.idle_add(self.update_status_label, updates)
            except Exception as e:
                print(f"Error al comprobar actualizaciones: {e}")
                GLib.idle_add(
                    self.updates_label.set_markup,
                    _("Error al comprobar actualizaciones.")
                )
            
            return False
        
        GLib.timeout_add(100, check_updates_thread)
    
    def update_status_label(self, updates):
        """Actualizar etiqueta de estado con información de actualizaciones"""
        if updates:
            self.updates_label.set_markup(
                _("Hay <b>{0}</b> actualizaciones disponibles. ").format(len(updates)) +
                _("Vaya a la pestaña de Actualización para instalarlas.")
            )
        else:
            self.updates_label.set_markup(
                _("El sistema está actualizado.")
            )
        
        return False
    
    def update_nav_button_icons(self):
        """Actualizar iconos en los botones de navegación según el tema actual"""
        try:
            # Verificar si los atributos existen
            if not hasattr(self, "btn_inicio_icon") or not hasattr(self, "btn_stats_icon") or \
               not hasattr(self, "btn_update_icon") or not hasattr(self, "btn_cleanup_icon") or \
               not hasattr(self, "btn_config_icon"):
                print("Los botones de navegación aún no han sido inicializados.")
                return
            
            # Cargar iconos desde la ruta del tema actual
            icon_size = 24
            
            # Botón de inicio
            home_icon_path = os.path.join(self.icons_path, "home.svg")
            if os.path.isfile(home_icon_path):
                self.btn_inicio_icon.set_from_file(home_icon_path)
                self.btn_inicio_icon.set_pixel_size(icon_size)
            else:
                self.btn_inicio_icon.set_from_icon_name("go-home-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            
            # Botón de estadísticas
            stats_icon_path = os.path.join(self.icons_path, "stats.svg")
            if os.path.isfile(stats_icon_path):
                self.btn_stats_icon.set_from_file(stats_icon_path)
                self.btn_stats_icon.set_pixel_size(icon_size)
            else:
                self.btn_stats_icon.set_from_icon_name("utilities-system-monitor-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            
            # Botón de actualización
            update_icon_path = os.path.join(self.icons_path, "update.svg")
            if os.path.isfile(update_icon_path):
                self.btn_update_icon.set_from_file(update_icon_path)
                self.btn_update_icon.set_pixel_size(icon_size)
            else:
                self.btn_update_icon.set_from_icon_name("software-update-available-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            
            # Botón de limpieza
            cleanup_icon_path = os.path.join(self.icons_path, "cleanup.svg")
            if os.path.isfile(cleanup_icon_path):
                self.btn_cleanup_icon.set_from_file(cleanup_icon_path)
                self.btn_cleanup_icon.set_pixel_size(icon_size)
            else:
                self.btn_cleanup_icon.set_from_icon_name("edit-clear-all-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            
            # Botón de configuración
            config_icon_path = os.path.join(self.icons_path, "config.svg")
            if os.path.isfile(config_icon_path):
                self.btn_config_icon.set_from_file(config_icon_path)
                self.btn_config_icon.set_pixel_size(icon_size)
            else:
                self.btn_config_icon.set_from_icon_name("preferences-system-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            
        except Exception as e:
            print(f"Error al actualizar iconos: {e}")
    
    def on_theme_changed(self, combo):
        """Manejar cambio de tema"""
        # Obtener tema seleccionado
        iter = combo.get_active_iter()
        if iter is not None:
            model = combo.get_model()
            theme_id = model[iter][1]
            
            # Actualizar configuración
            config = load_config()
            config["theme"] = theme_id
            
            from utils.utils import save_config
            save_config(config)
            
            # Recargar tema
            self.load_theme()
            
            # Actualizar iconos en los botones de navegación
            self.update_nav_button_icons()
    
    def on_menu_button_clicked(self, button):
        """Manejar clic en botón de menú"""
        # Crear menú emergente
        menu = Gtk.Menu()
        
        # Opción: Destruir archivos
        shred_item = Gtk.MenuItem(label=_("Destruir archivos"))
        shred_item.connect("activate", self.on_shred_files)
        menu.append(shred_item)
        
        # Opción: Destruir carpetas
        shred_dirs_item = Gtk.MenuItem(label=_("Destruir carpetas"))
        shred_dirs_item.connect("activate", self.on_shred_dirs)
        menu.append(shred_dirs_item)
        
        # Opción: Limpiar espacio libre
        clean_space_item = Gtk.MenuItem(label=_("Limpiar espacio libre"))
        clean_space_item.connect("activate", self.on_clean_free_space)
        menu.append(clean_space_item)
        
        # Separador
        menu.append(Gtk.SeparatorMenuItem())
        
        # Opción: Acerca de
        about_item = Gtk.MenuItem(label=_("Acerca de"))
        about_item.connect("activate", self.on_about)
        menu.append(about_item)
        
        # Mostrar menú
        menu.show_all()
        menu.popup_at_widget(
            button,
            Gdk.Gravity.SOUTH_WEST,
            Gdk.Gravity.NORTH_WEST,
            None
        )
    
    def on_shred_files(self, menuitem):
        """Manejar acción de destruir archivos"""
        # Mostrar diálogo de selección de archivos
        dialog = Gtk.FileChooserDialog(
            title=_("Seleccionar archivos a destruir"),
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
        )
        
        dialog.set_select_multiple(True)
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Obtener archivos seleccionados
            files = dialog.get_filenames()
            dialog.destroy()
            
            if files:
                # Mostrar diálogo de confirmación
                confirm_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text=_("¿Destruir archivos seleccionados?")
                )
                
                confirm_dialog.format_secondary_text(
                    _("Esta acción es irreversible y los archivos no podrán ser recuperados.")
                )
                
                confirm_response = confirm_dialog.run()
                confirm_dialog.destroy()
                
                if confirm_response == Gtk.ResponseType.YES:
                    # Destruir archivos usando el limpiador
                    self.show_tab("cleanup")
                    self.tabs["cleanup"].shred_files(files)
        else:
            dialog.destroy()
    
    def on_shred_dirs(self, menuitem):
        """Manejar acción de destruir carpetas"""
        # Mostrar diálogo de selección de carpetas
        dialog = Gtk.FileChooserDialog(
            title=_("Seleccionar carpeta a destruir"),
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                _("Seleccionar"), Gtk.ResponseType.OK
            )
        )
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Obtener carpeta seleccionada
            directory = dialog.get_filename()
            dialog.destroy()
            
            if directory:
                # Mostrar diálogo de confirmación
                confirm_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text=_("¿Destruir carpeta seleccionada?")
                )
                
                confirm_dialog.format_secondary_text(
                    _("Esta acción es irreversible y todos los archivos en la carpeta no podrán ser recuperados.")
                )
                
                confirm_response = confirm_dialog.run()
                confirm_dialog.destroy()
                
                if confirm_response == Gtk.ResponseType.YES:
                    # Destruir carpeta usando el limpiador
                    self.show_tab("cleanup")
                    self.tabs["cleanup"].shred_directory(directory)
        else:
            dialog.destroy()
    
    def on_clean_free_space(self, menuitem):
        """Manejar acción de limpiar espacio libre"""
        # Mostrar diálogo de selección de carpetas
        dialog = Gtk.FileChooserDialog(
            title=_("Seleccionar carpeta para limpiar espacio libre"),
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                _("Seleccionar"), Gtk.ResponseType.OK
            )
        )
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Obtener carpeta seleccionada
            directory = dialog.get_filename()
            dialog.destroy()
            
            if directory:
                # Mostrar diálogo de confirmación
                confirm_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text=_("¿Limpiar espacio libre en la carpeta seleccionada?")
                )
                
                confirm_dialog.format_secondary_text(
                    _("Esta acción no eliminará archivos pero sobrescribirá el espacio libre para evitar la recuperación de archivos borrados anteriormente.")
                )
                
                confirm_response = confirm_dialog.run()
                confirm_dialog.destroy()
                
                if confirm_response == Gtk.ResponseType.YES:
                    # Limpiar espacio libre usando el limpiador
                    self.show_tab("cleanup")
                    self.tabs["cleanup"].clean_free_space(directory)
        else:
            dialog.destroy()
    
    def on_about(self, menuitem):
        """Mostrar diálogo 'Acerca de'"""
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_transient_for(self)
        
        about_dialog.set_program_name("DexterSOA")
        about_dialog.set_version("1.0.0")
        about_dialog.set_copyright("© 2023")
        about_dialog.set_comments(_(
            "Una aplicación gráfica para gestión de actualizaciones, "
            "administración de paquetes APT, limpieza del sistema y notificaciones programadas."
        ))
        about_dialog.set_website("https://github.com/")
        
        # Cargar logo
        try:
            config = load_config()
            theme_name = config.get("theme", "light")
            if theme_name not in ["light", "dark"]:
                theme_name = "light"
                
            logo_path = os.path.join(get_data_path(), "assets", "themes", "icons", theme_name, "dexter-soa.svg")
            
            if os.path.isfile(logo_path):
                logo = Gtk.Image.new_from_file(logo_path)
                pixbuf = logo.get_pixbuf()
                about_dialog.set_logo(pixbuf)
            else:
                # Usar icono genérico si no encuentra el logo personalizado
                icon_theme = Gtk.IconTheme.get_default()
                try:
                    pixbuf = icon_theme.load_icon("applications-system", 128, 0)
                    about_dialog.set_logo(pixbuf)
                except:
                    pass
        except Exception as e:
            print(f"Error al cargar logo en diálogo Acerca de: {e}")
        
        about_dialog.run()
        about_dialog.destroy()
    
    def on_close_button_clicked(self, button):
        """Manejar clic en botón de cerrar"""
        self.destroy()
    
    def on_nav_button_clicked(self, button, tab_name):
        """Manejar clic en botones de navegación"""
        self.show_tab(tab_name)
    
    def show_tab(self, tab_name):
        """Mostrar una pestaña específica"""
        # Preparar animación
        GLib.timeout_add(10, self.animate_tab_change, tab_name)
    
    def animate_tab_change(self, tab_name):
        """Animar el cambio de pestaña con una transición suave"""
        # Ocultar todas las pestañas
        for name, tab in self.tabs.items():
            tab.hide()
        
        # Mostrar la pestaña seleccionada
        if tab_name in self.tabs:
            self.tabs[tab_name].show_all()
            
            # Aplicar efecto de aparición
            self.tabs[tab_name].set_opacity(0)
            
            def fade_in_step(opacity):
                """Incrementar gradualmente la opacidad"""
                self.tabs[tab_name].set_opacity(opacity)
                
                if opacity < 1.0:
                    # Continuar animación
                    GLib.timeout_add(20, fade_in_step, opacity + 0.1)
                return False
            
            # Iniciar animación
            GLib.timeout_add(20, fade_in_step, 0.1)
        
        # Actualizar estilo de botones de navegación
        for btn in [self.btn_inicio, self.btn_stats, self.btn_update, self.btn_cleanup, self.btn_config]:
            btn.get_style_context().remove_class("nav-button-active")
        
        # Marcar botón activo con una animación
        target_btn = None
        if tab_name == "inicio":
            target_btn = self.btn_inicio
        elif tab_name == "stats":
            target_btn = self.btn_stats
        elif tab_name == "update":
            target_btn = self.btn_update
        elif tab_name == "cleanup":
            target_btn = self.btn_cleanup
        elif tab_name == "config":
            target_btn = self.btn_config
            
        if target_btn:
            # Animar el botón seleccionado
            def highlight_button_step():
                target_btn.get_style_context().add_class("nav-button-active")
                return False
                
            # Retrasar ligeramente la activación del botón para que coincida con la animación
            GLib.timeout_add(100, highlight_button_step)
            
        return False