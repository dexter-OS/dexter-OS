#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import math
import re
import subprocess
from collections import defaultdict, namedtuple
from datetime import datetime, timedelta
import os
import time

# Constantes para el mapa
MAP_FILE_PNG = '/usr/share/dexter-installer/maps/miller.png'
MAP_SIZE = (752, 384)
MAP_CENTER = (382, 205)

# Expresiones regulares
ADJUST_HOURS_MINUTES = re.compile('([+-])([0-9][0-9])([0-9][0-9])')
TZ_SPLIT_COORDS = re.compile('([+-][0-9]+)([+-][0-9]+)')

# Funciones auxiliares
def to_float(position, wholedigits):
    assert position and len(position) > 4 and wholedigits < 9
    return float(position[:wholedigits + 1] + '.' + position[wholedigits + 1:])

def pixel_position(lat, lon):
    dx = MAP_SIZE[0] / 2 / 180
    dy = MAP_SIZE[1] / 2 / 90
    x = MAP_CENTER[0] + dx * lon
    y = MAP_CENTER[1] - dy * math.degrees(5/4 * math.log(math.tan(math.pi/4 + 2/5 * math.radians(lat))))
    return int(x), int(y)

# Zona horaria (namedtuple)
Timezone = namedtuple('Timezone', 'name ccode x y')

# Variables globales
timezones = []
region_menus = {}

class TimezonePage:
    """Página de selección de zona horaria"""
    
    def __init__(self, app):
        """Inicializa la página de zona horaria"""
        self.app = app
        self.scale = 1
        
        # Establecer zona horaria predeterminada
        class Setup:
            pass
        if not hasattr(app, 'setup'):
            app.setup = Setup()
        
        # Asegurarnos de que la zona horaria esté establecida correctamente
        if not hasattr(app.setup, 'timezone') or app.setup.timezone is None:
            print("Inicializando zona horaria predeterminada: Europe/Madrid")
            app.setup.timezone = "Europe/Madrid"
        
        # Configurar CSS para el título con esquinas redondeadas
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data("""
            .title-header {
                background-color: #212836;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }
        """.encode('utf-8'))
        
        # Aplicar el proveedor CSS al contexto de estilo
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Crear el contenedor principal
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.content.set_margin_start(2)
        self.content.set_margin_end(2)
        self.content.set_margin_top(2)
        self.content.set_margin_bottom(15)
        
        # Cargar el icono
        icon_path = "/usr/share/dexter-installer/images/icons/timezone.svg"
        icon_image = None
        try:
            icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 48, 48)
            icon_image = Gtk.Image.new_from_pixbuf(icon_pixbuf)
        except Exception as e:
            print("Error cargando el icono de idioma:", e)
            
        # Título de la página con esquinas redondeadas
        title_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title_container.get_style_context().add_class("title-header")
        title_container.set_hexpand(True)
        
        # Añadir el icono si se cargó correctamente
        if icon_image:
            title_container.pack_start(icon_image, False, False, 10)
            
        # Contenedor vertical para títulos
        title_labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Título de la página
        title = Gtk.Label()
        title.set_markup("<span foreground='white' size='xx-large' weight='bold'>Seleccione su Zona Horaria</span>")
        title.set_halign(Gtk.Align.START)
        title.set_margin_start(10)
        title.set_margin_top(10)
        title.set_margin_bottom(10)
        
        subtitle = Gtk.Label()
        subtitle.set_markup("<span foreground='white' size='medium'>¿Dónde estás?</span>")
        subtitle.set_halign(Gtk.Align.CENTER)
        subtitle.set_margin_start(250)
        subtitle.set_margin_bottom(10)
        
        # Añadir los labels al title_labels
        title_labels.pack_start(title, False, False, 0)
        title_labels.pack_start(subtitle, False, False, 0)

        # Añadir title_labels al title_container
        title_container.pack_start(title_labels, False, False, 0)

        # Añadir title_container al contenedor principal
        self.content.pack_start(title_container, False, False, 0)
        
        # Contenedor para el mapa
        map_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        map_container.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.117, 0.117, 0.117, 1.0))
        self.content.pack_start(map_container, True, True, 0)
        
        # Mapa interactivo de zonas horarias
        self.timezone_map = Gtk.Image()
        self.timezone_map_event_box = Gtk.EventBox()
        self.timezone_map_event_box.add(self.timezone_map)
        
        try:
            self.timezone_map.set_from_file(MAP_FILE_PNG)
            self.timezone_map_event_box.connect('button-release-event', self.map_clicked)
            self.timezone_map_event_box.connect('motion-notify-event', self.map_motion)
        except Exception as e:
            print("Error cargando la imagen del mapa:", e)
        
        # Overlay para posicionar la etiqueta de hora sobre el mapa
        self.map_overlay = Gtk.Overlay()
        self.map_overlay.add(self.timezone_map_event_box)
        
        # Etiqueta para mostrar la hora actual
        self.time_label = Gtk.Label()
        self.time_label.set_markup("<span foreground='white' size='large' weight='bold'>00:00</span>")
        
        self.time_label_box = Gtk.EventBox()
        self.time_label_box.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.0, 0.0, 0.0, 0.7))
        self.time_label_box.add(self.time_label)
        self.time_label_box.set_size_request(60, 25)
        
        # Panel inferior para mostrar continente y región
        self.region_info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.region_info_box.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.9, 0.9, 0.9, 1.0))
        self.region_info_box.set_halign(Gtk.Align.FILL)
        self.region_info_box.set_hexpand(True)
        
        # Contenedor para el continente (mitad izquierda)
        continent_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        continent_container.set_hexpand(True)
        continent_container.set_halign(Gtk.Align.FILL)
        continent_container.set_border_width(5)
        
        # Contenedor para la región (mitad derecha)
        region_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        region_container.set_hexpand(True)
        region_container.set_halign(Gtk.Align.FILL)
        region_container.set_border_width(5)
        
        # Separador vertical
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        
        # Etiquetas para el continente y la región
        self.continent_label = Gtk.Label("España")
        self.continent_label.set_halign(Gtk.Align.CENTER)
        self.continent_label.set_hexpand(True)
        
        self.region_label = Gtk.Label("Madrid")
        self.region_label.set_halign(Gtk.Align.CENTER)
        self.region_label.set_hexpand(True)
        
        # Añadir las etiquetas a sus contenedores
        continent_container.pack_start(self.continent_label, True, True, 0)
        region_container.pack_start(self.region_label, True, True, 0)
        
        # Añadir los contenedores y el separador al panel inferior
        self.region_info_box.pack_start(continent_container, True, True, 0)
        self.region_info_box.pack_start(separator, False, False, 0)
        self.region_info_box.pack_start(region_container, True, True, 0)
        
        # Construir datos de zonas horarias
        self.build_timezones()
        
        # Añadir el overlay con el mapa al contenedor de mapa
        map_container.pack_start(self.map_overlay, True, True, 0)
        
        # Añadir el panel de información de región
        self.content.pack_start(self.region_info_box, False, False, 0)
        
        # Actualizar la hora periódicamente
        GLib.timeout_add_seconds(1, self.update_local_time_label)
    
    def update_local_time_label(self):
        """Actualiza la etiqueta de hora local"""
        try:
            current_time = "--:--"
            
            if hasattr(self.app, 'setup') and hasattr(self.app.setup, 'timezone'):
                tz_name = self.app.setup.timezone
                
                try:
                    # Opción 1: Usar time de Python
                    os.environ['TZ'] = tz_name
                    time.tzset()
                    current_time = time.strftime('%H:%M')
                except:
                    # Opción 2: Usar comando date
                    cmd = ["date", "+%H:%M"]
                    env = os.environ.copy()
                    env['TZ'] = tz_name
                    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                    if result.returncode == 0:
                        current_time = result.stdout.strip()
            
            self.time_label.set_markup("<span foreground='white' size='large' weight='bold'>" + current_time + "</span>")
        except:
            self.time_label.set_markup("<span foreground='white' size='large' weight='bold'>--:--</span>")
        
        return True
    
    def map_motion(self, widget, event, data=None):
        """Manejador para movimiento del ratón sobre el mapa"""
        try:
            widget.get_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.HAND1))
        except:
            pass
        return True
    
    def map_clicked(self, widget, event, data=None):
        """Manejador para clicks en el mapa"""
        try:
            x, y = event.x, event.y
            print("Clic en coordenadas:", x, y)
            
            # Encontrar la zona horaria más cercana
            closest_timezone = None
            min_distance = float('inf')
            
            for tz in timezones:
                distance = math.sqrt((x - tz.x)**2 + (y - tz.y)**2)
                print(tz.name, "distancia:", distance)
                if distance < min_distance:
                    min_distance = distance
                    closest_timezone = tz
            
            # Solo seleccionar si la distancia es razonable (menos de 60 píxeles)
            if closest_timezone and min_distance < 60:
                print("Seleccionando:", closest_timezone.name, "con distancia:", min_distance)
                self.select_timezone(closest_timezone)
            else:
                print("Clic demasiado lejos de cualquier zona horaria conocida")
        except Exception as e:
            print("Error al hacer clic en el mapa:", e)
    
    def select_timezone(self, tz):
        """Selecciona una zona horaria y actualiza la interfaz"""
        try:
            print("Seleccionando zona horaria:", tz.name, "en posición:", tz.x, tz.y)
            
            # Guardar la zona horaria en el objeto de configuración
            if hasattr(self.app, 'setup'):
                self.app.setup.timezone = tz.name
            
            # Actualizar la etiqueta de hora
            self.update_local_time_label()
            
            # Quitar la etiqueta de hora si ya existe
            if self.time_label_box.get_parent():
                self.map_overlay.remove(self.time_label_box)
            
            # Añadir la etiqueta al overlay
            self.map_overlay.add_overlay(self.time_label_box)
            
            # Calcular la posición para la etiqueta de hora
            x = tz.x - 30
            y = tz.y - 12
            
            # Asegurarse de que esté dentro de los límites del mapa
            if x < 0: x = 0
            if y < 0: y = 0
            if x > MAP_SIZE[0] - 60: x = MAP_SIZE[0] - 60
            if y > MAP_SIZE[1] - 25: y = MAP_SIZE[1] - 25
            
            # Configurar la posición de la etiqueta
            self.time_label_box.set_halign(Gtk.Align.START)
            self.time_label_box.set_valign(Gtk.Align.START)
            self.time_label_box.set_margin_start(x)
            self.time_label_box.set_margin_top(y)
            self.time_label_box.show_all()
            
            # Actualizar las etiquetas de continente y región usando la lógica básica
            parts = tz.name.split('/')
            if tz.name == "UTC":
                self.continent_label.set_text("Universal")
                self.region_label.set_text("UTC")
            elif len(parts) >= 2:
                # Para zonas horarias estándar (mayoría de casos)
                self.continent_label.set_text(parts[0].replace('_', ' '))
                self.region_label.set_text(parts[-1].replace('_', ' '))
            else:
                # Para zonas horarias de un solo nivel
                self.continent_label.set_text("Unknown")
                self.region_label.set_text(tz.name)
                
        except Exception as e:
            print("Error al seleccionar zona horaria:", e)
    
    def build_timezones(self):
        """Construye la estructura de datos para las zonas horarias"""
        global timezones
        timezones = []
        
        # Zonas horarias predefinidas con coordenadas correctas
        # Ajustado las coordenadas de Madrid para que esté sobre España
        default_timezones = [
            ("Europe/Madrid", "ES", 380, 170),         # España - coordenadas ajustadas
            ("Europe/London", "GB", 400, 140),         # Londres
            ("Europe/Paris", "FR", 420, 150),          # París
            ("Europe/Berlin", "DE", 440, 140),         # Berlín
            ("America/New_York", "US", 230, 150),      # Nueva York
            ("America/Argentina/Buenos_Aires", "AR", 300, 300),  # Buenos Aires
            ("Asia/Tokyo", "JP", 680, 170),            # Tokio
            ("UTC", "XX", 382, 205)                    # UTC
        ]
        
        for name, ccode, x, y in default_timezones:
            timezones.append(Timezone(name, ccode, x, y))
        
        # Intentar cargar zonas adicionales del archivo, solo si existe
        try:
            filepath = "/usr/share/dexter-installer/locales/timezones"
            if os.path.exists(filepath):
                with open(filepath, "r") as file:
                    for line in file:
                        try:
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                ccode, name = parts[0], parts[1]
                                # No añadir si ya existe en nuestras zonas predefinidas
                                if any(tz.name == name for tz in timezones):
                                    continue
                                    
                                coords = name.split("/")[0].replace("_", " ")
                                match = TZ_SPLIT_COORDS.search(coords)
                                if match:
                                    lat, lon = match.groups()
                                    x, y = pixel_position(to_float(lat, 2), to_float(lon, 3))
                                    if x < 0: 
                                        x = MAP_SIZE[0] + x
                                    timezones.append(Timezone(name, ccode, x, y))
                        except:
                            pass
        except:
            pass
        
        # Seleccionar Madrid como zona horaria inicial
        for tz in timezones:
            if tz.name == "Europe/Madrid":
                self.select_timezone(tz)
                break
    
    def tz_menu_selected(self, widget, tz):
        """Manejador para selección de zonas horarias en el menú"""
        self.select_timezone(tz)
    
    def cont_menu_selected(self, widget, cont):
        """Manejador para selección de continentes en el menú"""
        pass
    
    def get_content(self):
        """Devuelve el contenedor principal de la página"""
        return self.content
    
    def validate(self):
        """Valida que se haya seleccionado una zona horaria"""
        return hasattr(self.app, 'setup') and hasattr(self.app.setup, 'timezone')
    
    def save(self):
        """Guarda la zona horaria seleccionada"""
        if hasattr(self.app, 'setup') and hasattr(self.app.setup, 'timezone'):
            return self.app.setup.timezone
        return "Europe/Madrid"
