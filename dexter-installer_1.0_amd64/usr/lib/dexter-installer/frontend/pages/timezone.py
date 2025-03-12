#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# DexterOS Installer - Página de bienvenida
# Version: 1.0
# Author: Victor Oubiña <oubinav78@gmail.com>
#

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
regions = defaultdict(list)

class TimezonePage:
    """Página de selección de zona horaria"""
    
    def __init__(self, app):
        """Inicializa la página de zona horaria"""
        self.app = app
        self.scale = 1
        self.current_region = "Europe"
        
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
            .timezone-marker {
                color: #FFFFFF;
                background-color: #FF0000;
                border-radius: 5px;
                padding: 2px 4px;
            }
            combobox {
                border: 1px solid #ccc;
                border-radius: 0;
                background-color: white;
            }
            button {
                border-radius: 10px;
                padding: 4px 8px;
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
        # Mantener el fondo original
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
        
        # Overlay para posicionar elementos sobre el mapa
        self.map_overlay = Gtk.Overlay()
        self.map_overlay.add(self.timezone_map_event_box)
        
        # Etiqueta para mostrar la hora actual
        self.time_label = Gtk.Label()
        self.time_label.set_markup("<span foreground='white' size='large' weight='bold'>00:00</span>")
        
        self.time_label_box = Gtk.EventBox()
        self.time_label_box.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.0, 0.0, 0.0, 0.7))
        self.time_label_box.add(self.time_label)
        self.time_label_box.set_size_request(60, 25)
        
        # Etiqueta para mostrar la ubicación seleccionada
        self.location_label = Gtk.Label()
        self.location_label.set_markup("<span foreground='white' size='small' weight='bold'>Madrid</span>")
        
        self.location_box = Gtk.EventBox()
        self.location_box.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.0, 0.0, 0.0, 0.7))
        self.location_box.get_style_context().add_class("timezone-marker")
        self.location_box.add(self.location_label)
        self.location_box.set_size_request(80, 20)
        
        # Contenedor para los selectores de región y zona
        selector_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        selector_box.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.9, 0.9, 0.9, 1.0))
        selector_box.set_border_width(8)
        
        # Selector de región
        region_label = Gtk.Label("Región:")
        self.region_combo = Gtk.ComboBoxText()
        self.region_combo.set_hexpand(True)
        
        # Selector de zona
        zone_label = Gtk.Label("Zona:")
        self.zone_combo = Gtk.ComboBoxText()
        self.zone_combo.set_hexpand(True)
        
        # Añadir componentes al selector_box
        selector_box.pack_start(region_label, False, False, 5)
        selector_box.pack_start(self.region_combo, True, True, 0)
        selector_box.pack_start(zone_label, False, False, 5)
        selector_box.pack_start(self.zone_combo, True, True, 0)
        
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
        
        # Añadir el contenedor de selector al contenido principal
        self.content.pack_start(selector_box, False, False, 0)
        
        # Crear contenedor para la información del idioma
        language_info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        language_info_box.set_margin_top(10)
        language_info_box.set_margin_bottom(5)
        language_info_box.set_margin_start(10)
        language_info_box.set_margin_end(10)

        # Etiqueta para el idioma
        language_label = Gtk.Label("El idioma del sistema se establecerá a español de España (España).")
        language_label.set_halign(Gtk.Align.START)
        language_label.set_hexpand(True)

        # Botón "Cambiar..." para el idioma
        change_language_button = Gtk.Button(label="Cambiar...")
        change_language_button.set_halign(Gtk.Align.END)

        # Añadir los elementos al contenedor
        language_info_box.pack_start(language_label, True, True, 0)
        language_info_box.pack_end(change_language_button, False, False, 0)

        # Contenedor para la información de localización
        locale_info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        locale_info_box.set_margin_top(5)
        locale_info_box.set_margin_bottom(10)
        locale_info_box.set_margin_start(10)
        locale_info_box.set_margin_end(10)
        
        # Etiqueta para la localización
        locale_label = Gtk.Label("La localización de números y fechas se establecerá a español de España (España).")
        locale_label.set_halign(Gtk.Align.START)
        locale_label.set_hexpand(True)

        # Botón "Cambiar..." para la localización
        change_locale_button = Gtk.Button(label="Cambiar...")
        change_locale_button.set_halign(Gtk.Align.END)

        # Añadir los elementos al contenedor
        locale_info_box.pack_start(locale_label, True, True, 0)
        locale_info_box.pack_end(change_locale_button, False, False, 0)

        # Añadir los contenedores al contenido principal
        self.content.pack_start(language_info_box, False, False, 0)
        self.content.pack_start(locale_info_box, False, False, 0)
        
        # Rellenar los selectores
        self.populate_selectors()
        
        # Conectar señales de los selectores
        self.region_combo.connect('changed', self.on_region_changed)
        self.zone_combo.connect('changed', self.on_zone_changed)
        
        # Actualizar la hora periódicamente
        GLib.timeout_add_seconds(1, self.update_local_time_label)
        
        # Dibujar el marcador de posición en la ubicación inicial
        for tz in timezones:
            if tz.name == "Europe/Madrid":
                self.add_location_marker(tz)
                break
    
    def draw_marker(self, widget, cr):
        """Dibuja un marcador circular para la posición seleccionada"""
        cr.set_source_rgb(1, 0, 0)  # Color rojo
        cr.arc(5, 5, 5, 0, 2 * math.pi)
        cr.fill()
        return False
    
    def add_location_marker(self, tz):
        """Añade un marcador de posición sobre el mapa"""
        # Actualizar la etiqueta de ubicación
        city = tz.name.split('/')[-1].replace('_', ' ')
        self.location_label.set_markup(f"<span foreground='white' size='small' weight='bold'>{city}</span>")
        
        # Eliminar el marcador anterior si existe
        if self.location_box.get_parent():
            self.map_overlay.remove(self.location_box)
        
        # Crear un área de dibujo para el marcador de posición
        marker = Gtk.DrawingArea()
        marker.set_size_request(10, 10)
        marker.connect('draw', self.draw_marker)
        
        # Añadir el marcador al overlay
        self.map_overlay.add_overlay(marker)
        
        # Posicionar el marcador
        marker.set_halign(Gtk.Align.START)
        marker.set_valign(Gtk.Align.START)
        marker.set_margin_start(tz.x - 5)
        marker.set_margin_top(tz.y - 5)
        
        # Añadir etiqueta de ubicación
        self.map_overlay.add_overlay(self.location_box)
        
        # Posicionar la etiqueta cerca del marcador pero ligeramente desplazada
        self.location_box.set_halign(Gtk.Align.START)
        self.location_box.set_valign(Gtk.Align.START)
        self.location_box.set_margin_start(tz.x + 5)
        self.location_box.set_margin_top(tz.y - 10)
        
        # Mostrar todo
        self.location_box.show_all()
        marker.show_all()
    
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
            
            # Actualizar los selectores para que coincidan con la zona seleccionada
            self.update_selectors_from_timezone(tz.name)
            
            # Añadir el marcador de posición
            self.add_location_marker(tz)
                
        except Exception as e:
            print("Error al seleccionar zona horaria:", e)
    
    def build_timezones(self):
        """Construye la estructura de datos para las zonas horarias"""
        global timezones, regions
        timezones = []
        regions = defaultdict(list)
        
        # Zonas horarias predefinidas con coordenadas correctas
        default_timezones = [
            ("Europe/Madrid", "ES", 380, 170),         # España - coordenadas ajustadas
            ("Europe/London", "GB", 400, 140),         # Londres
            ("Europe/Paris", "FR", 420, 150),          # París
            ("Europe/Berlin", "DE", 440, 140),         # Berlín
            ("Europe/Rome", "IT", 440, 160),           # Roma
            ("Europe/Athens", "GR", 460, 170),         # Atenas
            ("Europe/Moscow", "RU", 490, 130),         # Moscú
            ("America/New_York", "US", 230, 150),      # Nueva York
            ("America/Chicago", "US", 200, 150),       # Chicago
            ("America/Denver", "US", 180, 150),        # Denver
            ("America/Los_Angeles", "US", 150, 150),   # Los Ángeles
            ("America/Mexico_City", "MX", 190, 180),   # Ciudad de México
            ("America/Argentina/Buenos_Aires", "AR", 300, 300),  # Buenos Aires
            ("America/Sao_Paulo", "BR", 320, 270),     # Sao Paulo
            ("Africa/Cairo", "EG", 460, 190),          # El Cairo
            ("Africa/Johannesburg", "ZA", 450, 270),   # Johannesburgo
            ("Asia/Tokyo", "JP", 680, 170),            # Tokio
            ("Asia/Shanghai", "CN", 630, 170),         # Shanghai
            ("Asia/Dubai", "AE", 520, 200),            # Dubai
            ("Asia/Kolkata", "IN", 570, 200),          # India
            ("Australia/Sydney", "AU", 690, 280),      # Sydney
            ("Pacific/Auckland", "NZ", 740, 300),      # Auckland
            ("UTC", "XX", 382, 205)                    # UTC
        ]
        
        for name, ccode, x, y in default_timezones:
            tz = Timezone(name, ccode, x, y)
            timezones.append(tz)
            
            # Organizar por región para los selectores
            parts = name.split('/')
            if len(parts) >= 1:
                region = parts[0]
                regions[region].append(tz)
        
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
                                    tz = Timezone(name, ccode, x, y)
                                    timezones.append(tz)
                                    
                                    # Añadir a las regiones para los selectores
                                    parts = name.split('/')
                                    if len(parts) >= 1:
                                        region = parts[0]
                                        regions[region].append(tz)
                        except:
                            pass
        except:
            pass
    
    def populate_selectors(self):
        """Rellena los selectores de región y zona"""
        # Obtener las regiones ordenadas
        region_names = sorted(regions.keys())
        
        # Limpiar los selectores
        self.region_combo.remove_all()
        self.zone_combo.remove_all()
        
        # Añadir las regiones al selector
        for region in region_names:
            self.region_combo.append_text(region)
        
        # Seleccionar Europa por defecto
        for i, region in enumerate(region_names):
            if region == "Europe":
                self.region_combo.set_active(i)
                self.current_region = "Europe"
                # Rellenar las zonas para Europa
                self.populate_zones_for_region("Europe")
                break
    
    def populate_zones_for_region(self, region):
        """Rellena el selector de zonas para una región específica"""
        # Limpiar el selector de zonas
        self.zone_combo.remove_all()
        
        # Obtener y ordenar las zonas para esta región
        zones = sorted([tz.name.split('/')[-1].replace('_', ' ') for tz in regions[region]])
        
        # Añadir al selector
        for zone in zones:
            self.zone_combo.append_text(zone)
        
        # Seleccionar Madrid por defecto si estamos en Europe
        if region == "Europe":
            for i, zone in enumerate(zones):
                if zone == "Madrid":
                    self.zone_combo.set_active(i)
                    break
    
    def on_region_changed(self, widget):
        """Manejador para el cambio de región en el selector"""
        region = self.region_combo.get_active_text()
        if region:
            self.current_region = region
            self.populate_zones_for_region(region)
    
    def on_zone_changed(self, widget):
        """Manejador para el cambio de zona en el selector"""
        # Prevenir recursión
        if hasattr(self, '_updating_zone') and self._updating_zone:  # Eliminado el paréntesis extra
            return
            
        region = self.region_combo.get_active_text()
        zone = self.zone_combo.get_active_text()
        
        if region and zone:
            # Buscar la zona horaria que corresponda a esta combinación
            zone_name = zone.replace(' ', '_')
            full_name = f"{region}/{zone_name}"
            
            # Buscar casos con más niveles (como America/Argentina/Buenos_Aires)
            target_timezone = None
            for tz in timezones:
                if tz.name == full_name or tz.name.endswith(f"/{zone_name}"):
                    target_timezone = tz
                    break
            
            # Seleccionar si se encontró
            if target_timezone:
                self.select_timezone(target_timezone)
    
    def update_selectors_from_timezone(self, timezone_name):
        """Actualiza los selectores basados en el nombre de la zona horaria"""
        parts = timezone_name.split('/')
        
        if len(parts) >= 2:
            region = parts[0]
            zone = parts[-1].replace('_', ' ')
            
            # Actualizar el selector de regiones
            for i in range(self.region_combo.get_model().iter_n_children(None)):
                if self.region_combo.get_model()[i][0] == region:
                    self.region_combo.set_active(i)
                    self.current_region = region
                    
                    # Actualizar las zonas para esta región
                    self.populate_zones_for_region(region)
                    
                    # Seleccionar la zona correcta
                    for j in range(self.zone_combo.get_model().iter_n_children(None)):
                        if self.zone_combo.get_model()[j][0] == zone:
                            self.zone_combo.set_active(j)
                            break
                    break
    
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
