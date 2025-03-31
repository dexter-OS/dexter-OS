#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import signal
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib, Gdk


def load_css():
    """Carga el archivo CSS y lo aplica a la aplicación"""
    # Ruta al archivo CSS
    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
    
    if not os.path.exists(css_file):
        print(f"Archivo CSS no encontrado: {css_file}")
        return
    
    # Crea un proveedor de estilo CSS
    css_provider = Gtk.CssProvider()
    try:
        css_provider.load_from_path(css_file)
        # Aplica el CSS a toda la aplicación
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen, 
            css_provider, 
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        print(f"Estilos CSS cargados desde: {css_file}")
    except Exception as e:
        print(f"Error al cargar CSS: {str(e)}")


class ActualizacionSignal(GObject.GObject):
    """Clase para emitir señales desde el hilo de actualización al hilo principal"""
    __gsignals__ = {
        'actualizar': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'completado': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'error': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'cancelado': (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self):
        GObject.GObject.__init__(self)


class DexterUpdate(Gtk.Box):
    def __init__(self, parent=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        # Establecer nombre de widget y clase CSS
        self.set_name("DexterUpdate")
        context = self.get_style_context()
        context.add_class("dexter-update")
        
        self.is_updating = False
        self.update_thread = None
        self.signals = ActualizacionSignal()
        self.main_window = self.get_main_window(parent)
        self.cancelar_flag = False
        self.proceso_actual = None
        
        # Configurar las conexiones de señales
        self.signals.connect("actualizar", self.on_actualizar)
        self.signals.connect("completado", self.on_proceso_completado)
        self.signals.connect("error", self.on_mostrar_error)
        self.signals.connect("cancelado", self.on_proceso_cancelado)
        
        self.init_ui()
        
    def get_main_window(self, parent):
        """Obtiene una referencia a la ventana principal"""
        if parent is None:
            return None
            
        if hasattr(parent, 'disable_menu_buttons'):
            return parent
            
        if hasattr(parent, 'get_parent'):
            return self.get_main_window(parent.get_parent())
            
        return None
    
    def init_ui(self):
        # Terminal para mostrar salida en tiempo real
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(400)
        
        self.terminal = Gtk.TextView()
        self.terminal.set_editable(False)
        self.terminal.set_cursor_visible(False)
        
        # Aplicar clase CSS al terminal
        context = self.terminal.get_style_context()
        context.add_class("terminal")
        context.add_class("info-text")
        
        # Configurar la fuente monoespaciada
        self.terminal.override_font(self._create_pango_font("Monospace 10"))
        
        scrolled_window.add(self.terminal)
        self.terminal_buffer = self.terminal.get_buffer()
        
        # Crear el botón de actualización dentro de un contenedor para centrarlo
        button_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        button_container.set_halign(Gtk.Align.CENTER)
        
        self.update_button = Gtk.Button.new_with_label("Actualizar Sistema")
        self.update_button.set_size_request(200, 40)
        self.update_button.connect("clicked", self.on_iniciar_actualizacion)
        
        # Aplicar clase CSS al botón
        context = self.update_button.get_style_context()
        context.add_class("action-button")
        
        button_container.pack_start(self.update_button, False, False, 0)
        
        # Agregar componentes al layout principal
        self.pack_start(scrolled_window, True, True, 0)
        self.pack_start(button_container, False, False, 10)
        
        # Mensaje inicial
        self.append_text("Sistema listo para actualizar.\n")
    
    def _create_pango_font(self, font_string):
        try:
            import gi
            gi.require_version('Pango', '1.0')
            from gi.repository import Pango
            return Pango.FontDescription.from_string(font_string)
        except Exception as e:
            print(f"Error al crear fuente: {e}")
            return None
    
    def on_iniciar_actualizacion(self, widget):
        """Inicia o cancela el proceso de actualización"""
        if self.is_updating:
            # Si ya está en proceso de actualización, cancelamos
            self.cancelar_flag = True
            self.update_button.set_label("Cancelando...")
            self.terminal_buffer.set_text("")
            self.append_text("Cancelando actualización...")
            
            if self.proceso_actual:
                # Terminamos el proceso actual
                self.proceso_actual.terminate()
                try:
                    # Esperar a que termine el proceso con un timeout
                    for _ in range(20):  # Esperar hasta 2 segundos
                        if self.proceso_actual.poll() is not None:
                            break
                        GLib.timeout_add(100, lambda: None)
                    if self.proceso_actual.poll() is None:
                        self.proceso_actual.kill()  # Forzar terminación si no responde
                except Exception as e:
                    print(f"Error al terminar proceso: {e}")
            
            # Emitimos la señal de cancelación
            GLib.idle_add(lambda: self.signals.emit("cancelado"))
        else:
            # Si no está en proceso, comenzamos la actualización
            self.is_updating = True
            self.cancelar_flag = False
            self.update_button.set_label("Cancelar")
            self.terminal_buffer.set_text("")
            self.append_text("Iniciando actualización del sistema...\n")
            
            if self.main_window and hasattr(self.main_window, 'disable_menu_buttons'):
                self.main_window.disable_menu_buttons(True)
            
            # Iniciar el hilo de actualización
            self.update_thread = threading.Thread(target=self.ejecutar_actualizacion)
            self.update_thread.daemon = True
            self.update_thread.start()
    
    def ejecutar_actualizacion(self):
        """Ejecuta los comandos de actualización del sistema"""
        try:
            comandos = [
                "sudo apt-get update",
                "sudo apt-get install -f -y",
                "sudo apt-get install --fix-broken -y",
                "sudo dpkg --configure -a",
                "sudo apt-get full-upgrade -y",
                "sudo apt-get remove -y",
                "sudo apt-get autoremove -y",
                "sudo apt-get purge -y",
                "sudo apt-get autopurge -y",
                "sudo apt-get clean",
                "sudo apt-get autoclean",
                "sudo update-grub2"
            ]
            
            for comando in comandos:
                if self.cancelar_flag:
                    return  # Si se ha cancelado, salimos del proceso
                
                proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, 
                                          stderr=subprocess.STDOUT, text=True)
                self.proceso_actual = proceso  # Guardamos el proceso para poder cancelarlo
                
                for linea in proceso.stdout:
                    # Solo enviamos la línea si no está cancelado
                    if not self.cancelar_flag:
                        GLib.idle_add(lambda l=linea: self.signals.emit("actualizar", l))
                
                proceso.wait()
                # Solo verificamos errores si no está cancelado
                if proceso.returncode != 0 and not self.cancelar_flag:
                    GLib.idle_add(lambda cmd=comando: self.signals.emit("error", f"Error ejecutando: {cmd}"))
                    return
                
                # Verificar si se ha cancelado después de cada comando
                if self.cancelar_flag:
                    return
            
            # Solo emitimos completado si no está cancelado
            if not self.cancelar_flag:
                GLib.idle_add(lambda: self.signals.emit("completado"))
        except Exception as e:
            if not self.cancelar_flag:
                GLib.idle_add(lambda err=str(e): self.signals.emit("error", err))
    
    def on_proceso_completado(self, signal):
        """Maneja la finalización de la actualización"""
        self.append_text("\n¡Actualización completada con éxito!\n")
        self.is_updating = False
        self.update_button.set_label("Actualizar Sistema")
        
        if self.main_window and hasattr(self.main_window, 'disable_menu_buttons'):
            self.main_window.disable_menu_buttons(False)
    
    def on_proceso_cancelado(self, signal):
        """Maneja la cancelación limpia de la actualización"""
        self.terminal_buffer.set_text("")  # Limpiamos cualquier salida anterior
        self.append_text("Actualización cancelada.")  # Solo mostramos este mensaje
        self.is_updating = False
        self.update_button.set_label("Actualizar Sistema")
        
        if self.main_window and hasattr(self.main_window, 'disable_menu_buttons'):
            self.main_window.disable_menu_buttons(False)
    
    def on_actualizar(self, signal, texto):
        """Muestra salida en la terminal"""
        # Solo actualizamos la terminal si no estamos cancelando
        if not self.cancelar_flag:
            self.append_text(texto)
    
    def on_mostrar_error(self, signal, mensaje):
        """Muestra mensajes de error"""
        if not self.cancelar_flag:
            self.append_text(f"\n{mensaje}\n")
        self.is_updating = False
        self.update_button.set_label("Actualizar Sistema")
        
        if self.main_window and hasattr(self.main_window, 'disable_menu_buttons'):
            self.main_window.disable_menu_buttons(False)
            
    def append_text(self, text):
        """Añade texto al widget de terminal"""
        end_iter = self.terminal_buffer.get_end_iter()
        self.terminal_buffer.insert(end_iter, text)
        # Desplazar hacia abajo para ver el último texto
        self.terminal.scroll_to_iter(self.terminal_buffer.get_end_iter(), 0.0, False, 0.0, 0.0)


class DexterUpdateApp(Gtk.Window):
    """Clase para ejecutar la aplicación de forma independiente"""
    def __init__(self):
        super().__init__(title="DexterSOA - Actualización del Sistema")
        self.set_default_size(800, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Aplicar clase CSS a la ventana
        context = self.get_style_context()
        context.add_class("main-window")
        
        # Crear el widget de actualización
        self.update_widget = DexterUpdate(self)
        self.add(self.update_widget)
        
        # Conectar señal de cierre
        self.connect("delete-event", Gtk.main_quit)
    
    def disable_menu_buttons(self, disable):
        """Método requerido por DexterUpdate"""
        pass  # No hay menús que deshabilitar en esta app independiente


if __name__ == "__main__":
    # Inicializar GObject threads
    GObject.threads_init()
    
    # Cargar CSS
    load_css()
    
    # Crear y mostrar la aplicación
    app = DexterUpdateApp()
    app.show_all()
    Gtk.main()
