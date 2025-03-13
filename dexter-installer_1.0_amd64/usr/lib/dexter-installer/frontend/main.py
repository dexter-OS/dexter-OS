#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# DexterOS Installer - Módulo principal de la interfaz
# Version: 1.0
# Author: Victor Oubiña <oubinav78@gmail.com>
#

import os
import sys
import gi
import gettext
import fcntl
import tempfile

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

# Configurar traducción
_ = gettext.gettext

# Importar configuración
from helpers.config import Config

# Importar páginas
from frontend.pages.welcome import WelcomePage
from frontend.pages.timezone import TimezonePage
from frontend.pages.keyboard import KeyboardPage

class SingleInstanceApp:
    """Clase para asegurar que solo se ejecuta una instancia de la aplicación"""
    
    def __init__(self, lock_file):
        self.lock_file = lock_file
        self.lock_handle = None
        
    def acquire_lock(self):
        """Intenta adquirir el bloqueo. Retorna True si lo consigue, False si no."""
        try:
            # Abrir o crear el archivo de bloqueo
            self.lock_handle = open(self.lock_file, 'w')
            # Intentar bloquear el archivo (no bloqueante)
            fcntl.flock(self.lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Escribir el PID actual en el archivo
            self.lock_handle.write(str(os.getpid()))
            self.lock_handle.flush()
            return True
        except IOError:
            # No se pudo adquirir el bloqueo, probablemente otra instancia está corriendo
            if self.lock_handle:
                self.lock_handle.close()
                self.lock_handle = None
            return False
    
    def release_lock(self):
        """Libera el bloqueo si está adquirido"""
        if self.lock_handle:
            fcntl.flock(self.lock_handle, fcntl.LOCK_UN)
            self.lock_handle.close()
            self.lock_handle = None
            try:
                os.remove(self.lock_file)
            except:
                pass

class DexterInstallerApp:
    """Aplicación principal del instalador DexterOS"""
    
    def __init__(self):
        # Verificar que solo se ejecuta una instancia
        lock_file = os.path.join(tempfile.gettempdir(), 'dexter-installer.lock')
        self.single_instance = SingleInstanceApp(lock_file)
        
        if not self.single_instance.acquire_lock():
            dialog = Gtk.MessageDialog(
                transient_for=None,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=_("El instalador ya está en ejecución")
            )
            dialog.run()
            dialog.destroy()
            sys.exit(1)
            
        # Cargar configuración
        self.config = Config()
        
        # Configurar estilos CSS antes de crear widgets
        self.apply_css()
        
        # Crear la ventana principal
        self.window = Gtk.Window(title=_("Instalador de DexterOS"))
        # Tamaño reducido
        self.window.set_default_size(850, 600)
        self.window.set_size_request(850, 600)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_resizable(False)
        self.window.connect("delete-event", self.on_close)
        
        # Añadir también esta línea para forzar el tamaño
        self.window.resize(850, 600)
        
        # Quitar la decoración de la ventana (barra de título y botones)
        self.window.set_decorated(False)
        
        # Añadir clase CSS a la ventana para el estilo
        self.window.get_style_context().add_class("background")
        
        # Configurar esquinas redondeadas
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.window.set_visual(visual)
            
        # Hacer que la ventana sea pintable para efectos visuales
        self.window.set_app_paintable(True)
        self.window.connect("draw", self.draw_window)
        
        # Cargar el icono de la ventana
        try:
            icon_path = os.path.join('/usr/share/dexter-installer/images', 'logo.png')
            self.window.set_icon_from_file(icon_path)
        except:
            print(_("No se pudo cargar el icono de la aplicación"))
        
        # Crear layout principal
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.add(self.main_box)
        
        # Área principal de contenido (ahora ocupa todo el ancho)
        self.content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_box.pack_start(self.content, True, True, 0)
        
        # Definir los pasos (aunque no se muestren en la barra lateral)
        self.steps = [
            {"id": "welcome", "label": _("Bienvenida")},
            {"id": "timezone", "label": _("Zona Horaria")},
            {"id": "keyboard", "label": _("Teclado")},
            {"id": "partition", "label": _("Particionado")},
            {"id": "users", "label": _("Usuario")},
            {"id": "summary", "label": _("Resumen")},
            {"id": "install", "label": _("Instalación")}
        ]
        
        # Área principal de contenido
        self.main_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.pack_start(self.main_content, True, True, 0)
        
        # Stack para manejar las diferentes páginas
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)
        self.main_content.pack_start(self.stack, True, True, 0)
        
        # Inicializar las páginas 
        self.pages = {
            "welcome": WelcomePage(self),
            "timezone": TimezonePage(self),
            "keyboard": KeyboardPage(self)
        }
        
        # Añadir las páginas al stack
        self.stack.add_named(self.pages["welcome"].get_content(), "welcome")
        self.stack.add_named(self.pages["timezone"].get_content(), "timezone")
        self.stack.add_named(self.pages["keyboard"].get_content(), "keyboard")
        
        # Crear un box para los botones con fondo personalizado
        self.button_background = Gtk.EventBox()
        self.button_background.get_style_context().add_class("button-background")
        self.main_content.pack_end(self.button_background, False, True, 0)
        
        # Botones de navegación dentro del EventBox
        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.button_box.set_margin_top(10)
        self.button_box.set_margin_bottom(10)
        self.button_box.set_margin_start(10)
        self.button_box.set_margin_end(10)
        self.button_background.add(self.button_box)
        
        # Botón Cancelar
        self.cancel_button = Gtk.Button(label=_("Cancelar"))
        self.cancel_button.set_size_request(200, 36)
        self.cancel_button.get_style_context().add_class("cancel-button")
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        self.button_box.pack_start(self.cancel_button, False, False, 0)
        
        # Espacio flexible en el medio
        self.button_box.pack_start(Gtk.Box(), True, True, 0)
        
        # Botón Retroceso
        self.back_button = Gtk.Button(label=_("Retroceder"))
        self.back_button.set_size_request(200, 36)
        self.back_button.get_style_context().add_class("back-button")
        self.back_button.connect("clicked", self.on_back_clicked)
        self.button_box.pack_start(self.back_button, False, False, 0)
        
        # Botón Siguiente
        self.next_button = Gtk.Button(label=_("Siguiente"))
        self.next_button.set_size_request(200, 36)
        self.next_button.get_style_context().add_class("suggested-action")
        self.next_button.connect("clicked", self.on_next_clicked)
        self.button_box.pack_end(self.next_button, False, False, 0)
        
        # Estado inicial
        self.current_page_index = 0
    
    def apply_css(self):
        """Carga el CSS personalizado para la aplicación desde un archivo externo"""
        css_provider = Gtk.CssProvider()
        try:
            # Intentar cargar desde la ubicación de instalación
            css_path = '/usr/share/dexter-installer/styles/style.css'
            if not os.path.exists(css_path):
                # Si no está en la ubicación de instalación, intentar en la carpeta actual
                css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'styles', 'styles.css')
            
            css_provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            print(f"Error al cargar CSS: {e}")
    
    def draw_window(self, widget, context):
        """Dibuja el fondo de la ventana con esquinas redondeadas"""
        # Obtener dimensiones de la ventana
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        
        # Radio de las esquinas
        radius = 20
        
        # Dibujar un camino con esquinas redondeadas
        context.new_sub_path()
        context.arc(radius, radius, radius, 180 * (3.14/180), 270 * (3.14/180))  # Esquina superior izquierda
        context.arc(width - radius, radius, radius, 270 * (3.14/180), 0)  # Esquina superior derecha
        context.arc(width - radius, height - radius, radius, 0, 90 * (3.14/180))  # Esquina inferior derecha
        context.arc(radius, height - radius, radius, 90 * (3.14/180), 180 * (3.14/180))  # Esquina inferior izquierda
        context.close_path()
        
        # Rellenar el fondo
        context.set_source_rgba(0.12, 0.12, 0.12, 1)  #1e1e1e
        context.fill()
        
        return False  # Permitir dibujado de widgets hijo
    
    def on_close(self, widget, event):
        """Manejador para el cierre de la ventana"""
        # Obtener el tamaño actual de la ventana
        current_width, current_height = self.window.get_size()
        
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_("¿Está seguro que desea salir?")
        )
        dialog.format_secondary_text(_("La instalación no se ha completado.\nTamaño actual de la ventana: {}x{}").format(
            current_width, current_height))
        response = dialog.run()
        
        if response == Gtk.ResponseType.YES:
            dialog.destroy()
            # Liberar el bloqueo antes de salir
            self.single_instance.release_lock()
            print(f"Tamaño final de la ventana: {current_width}x{current_height}")
            Gtk.main_quit()
            return False
        else:
            dialog.destroy()
            return True  # Evita que se cierre la ventana
    
    def on_cancel_clicked(self, button):
        """Manejador para el botón Cancelar"""
        return self.on_close(None, None)
    
    def on_back_clicked(self, button):
        """Manejador para el botón Retroceder."""
        if self.current_page_index > 0:
            self.current_page_index -= 1
            prev_page_id = self.steps[self.current_page_index]["id"]
            self.navigate_to(prev_page_id)
            
    def on_next_clicked(self, button):
        """Manejador para el botón Siguiente"""
        current_page_id = self.steps[self.current_page_index]["id"]
        
        # Validar la página actual antes de avanzar
        current_page = None
        if current_page_id == "welcome":
            current_page = self.pages["welcome"]
        elif current_page_id == "timezone":
            current_page = self.pages["timezone"]
        elif current_page_id == "keyboard":
            current_page = self.pages["keyboard"]
            
        # Validar la página actual
        if current_page and hasattr(current_page, 'validate') and not current_page.validate():
            # Mostrar un mensaje de error si la validación falla
            dialog = Gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text=_("Selección inválida")
            )
            dialog.format_secondary_text(_("Por favor, seleccione una opción válida."))
            dialog.run()
            dialog.destroy()
            return
        
        # Guardar los datos de la página actual si es posible
        if current_page and hasattr(current_page, 'save'):
            current_page.save()
        
        # Avanzar a la siguiente página
        if self.current_page_index < len(self.steps) - 1:
            self.current_page_index += 1
            next_page_id = self.steps[self.current_page_index]["id"]
            self.navigate_to(next_page_id)
    
    def run(self):
        """Ejecuta la aplicación"""
        # Mostrar la ventana y sus elementos
        self.window.show_all()
        
        # Asegurarse de que la primera página esté visible
        self.stack.set_visible_child_name("welcome")
        
        # Ocultar el botón de retroceso en la página inicial
        self.back_button.hide()
    
        # Iniciar el bucle principal de Gtk
        Gtk.main()
        return 0

    def navigate_to(self, page_id):
        """Navega a una página específica"""
        if page_id in [step["id"] for step in self.steps]:
            # Encontrar el índice de la página
            for i, step in enumerate(self.steps):
                if step["id"] == page_id:
                    self.current_page_index = i
                    break
            
            # Cambiar la página en el stack
            self.stack.set_visible_child_name(page_id)
            
            # Ocultar o mostrar el botón de retroceso según la página
            if page_id in ["welcome", "timezone"]:
                self.back_button.hide()
            else:
                self.back_button.show()

# Inicializar la aplicación
if __name__ == "__main__":
    app = DexterInstallerApp()
    app.run()
