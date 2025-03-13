#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# DexterOS Installer - Página de zona horaria (versión mejorada)
# Version: 1.0
# Author: Victor Oubiña <oubinav78@gmail.com>
#

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import subprocess
import os
import time

class TimezonePage:
    """Página de selección de zona horaria - Versión mejorada con mapa estático"""
    
    def __init__(self, app):
        """Inicializa la página de zona horaria"""
        self.app = app
        self.current_region = "Europe"
        
        # Establecer zona horaria predeterminada
        class Setup:
            pass
        if not hasattr(app, 'setup'):
            app.setup = Setup()
        
        # Asegurarnos de que la zona horaria esté establecida correctamente
        if not hasattr(app.setup, 'timezone') or app.setup.timezone is None:
            app.setup.timezone = "Europe/Madrid"
        
        # Configurar CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data("""
            .title-header {
                background-color: #212836;
            }
            .label-text {
                color: #E0B0FF; /* Lavanda claro para combinar con el mapa */
            }
            .region-label {
                color: #E0B0FF;
                font-size: 12px;
                font-weight: bold;
            }
            .time-label {
                color: #E0B0FF;
                font-size: 12px;
                font-weight: bold;
            }
            combobox {
                color: white;
                min-height: 22px;
                padding: 2px;
            }
            combobox button {
                border-radius: 4px;
                border: none;
            }
            combobox arrow {
                color: #9370DB;
            }
            combobox menu {
                background-color: rgba(40, 40, 40, 0.95);
                border: 1px solid #9370DB;
                border-radius: 10px;
            }
            combobox menu menuitem {
                color: #E0B0FF;
                padding: 6px 8px;
                border-radius: 10px;
            }
            combobox menu menuitem:hover {
                background-color: rgba(147, 112, 219, 0.4);
                border-radius: 10px;
            }
            button {
                border-radius: 10px;
                padding: 6px 10px;
                border: 1px solid #9370DB; /* Púrpura para combinar con el mapa */
                background-color: rgba(40, 40, 40, 0.8);
                color: white;
            }
            button:hover {
                background-color: rgba(60, 60, 60, 0.8);
            }
            .selector-box {
                padding: 10px;
                border-radius: 10px;
            }
            .timezone-box {
                background-color: rgba(30, 30, 30, 0.8);
                border-radius: 8px;
                padding: 12px;
                border: 1px solid #9370DB; /* Color púrpura que combina con el mapa */
                margin-top: 20px;
            }
            .info-box {
                background-color: rgba(30, 30, 30, 0.8);
                padding: 6px 10px;
            }
        """.encode('utf-8'))
        
        # Aplicar el proveedor CSS
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Crear el contenedor principal
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.content.set_margin_bottom(15)
        
        # Título de la página
        title_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title_container.get_style_context().add_class("title-header")
        title_container.set_hexpand(True)
        
        # Cargar el icono
        icon_path = "/usr/share/dexter-installer/images/icons/idioma.svg"
        icon_image = None
        try:
            icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 48, 48)
            icon_image = Gtk.Image.new_from_pixbuf(icon_pixbuf)
        except Exception as e:
            print("Error cargando el icono de idioma:", e)
        
        # Título y subtítulo
        title_labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Añadir el icono si se cargó correctamente
        if icon_image:
            title_container.pack_start(icon_image, False, False, 10)
        
        title = Gtk.Label()
        title.set_markup("<span foreground='white' size='xx-large' weight='bold'>Seleccione su Zona Horaria</span>")
        title.set_halign(Gtk.Align.START)
        title.set_margin_start(10)
        title.set_margin_top(10)
        title.set_margin_bottom(5)
        
        subtitle = Gtk.Label()
        subtitle.set_markup("<span foreground='white' size='medium'>¿Dónde estás?</span>")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_margin_start(250)
        subtitle.set_margin_bottom(10)
        
        title_labels.pack_start(title, False, False, 0)
        title_labels.pack_start(subtitle, False, False, 0)
        title_container.pack_start(title_labels, False, False, 0)
        self.content.pack_start(title_container, False, False, 0)
        
        # Contenedor principal para el mapa y selectores
        main_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_content.set_hexpand(True)
        main_content.set_vexpand(True)
        
        # Cargar un mapa de fondo estático
        map_path = "/usr/share/dexter-installer/maps/miller.png"
        
        map_image = Gtk.Image()
        try:
            # Intentar cargar el mapa
            if os.path.exists(map_path):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(map_path)
                # Ajustar el mapa al tamaño adecuado manteniendo la proporción
                screen_width = Gdk.Screen.get_default().get_width()
                target_width = min(900, screen_width - 40)  # Ancho máximo con margen
                target_height = int(target_width * pixbuf.get_height() / pixbuf.get_width())
                scaled_pixbuf = pixbuf.scale_simple(target_width, target_height, GdkPixbuf.InterpType.BILINEAR)
                map_image.set_from_pixbuf(scaled_pixbuf)
            else:
                print("No se encontró el mapa, usando un fallback")
                # Crear un rectángulo negro como último recurso
                pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 800, 400)
                pixbuf.fill(0x000000FF)  # Negro con alpha 1.0
                map_image.set_from_pixbuf(pixbuf)
        except Exception as e:
            print(f"Error cargando el mapa: {e}")
            # Crear un rectángulo negro como último recurso
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 800, 400)
            pixbuf.fill(0x000000FF)  # Negro con alpha 1.0
            map_image.set_from_pixbuf(pixbuf)
        
        # Crear un contenedor para superponer elementos sobre el mapa
        map_overlay = Gtk.Overlay()
        map_overlay.add(map_image)
        
        # Añadir el overlay al contenido principal
        main_content.pack_start(map_overlay, True, True, 0)
        
        # Selector de región y zona (ajuste de posición más arriba y más estrechos)
        selector_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        selector_box.set_halign(Gtk.Align.CENTER)
        selector_box.set_valign(Gtk.Align.CENTER)
        selector_box.set_margin_bottom(350)  # Subir los selectores más arriba del centro
        selector_box.get_style_context().add_class("selector-box")
        selector_box.set_hexpand(True)
        
        # Selector de región
        region_label = Gtk.Label("Región:")
        region_label.get_style_context().add_class("label-text")
        self.region_combo = Gtk.ComboBoxText()
        self.region_combo.set_size_request(300, -1)  # Reducir el ancho
        
        # Selector de zona
        zone_label = Gtk.Label("Zona:")
        zone_label.get_style_context().add_class("label-text")
        self.zone_combo = Gtk.ComboBoxText()
        self.zone_combo.set_size_request(300, -1)  # Reducir el ancho
        
        # Añadir componentes al selector_box
        selector_box.pack_start(region_label, False, False, 5)
        selector_box.pack_start(self.region_combo, False, False, 0)
        selector_box.pack_start(zone_label, False, False, 5)
        selector_box.pack_start(self.zone_combo, False, False, 0)
        
        # Añadir el selector como overlay sobre el mapa
        map_overlay.add_overlay(selector_box)
        
        # Contenedor para mostrar la zona horaria seleccionada
        timezone_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        timezone_box.set_halign(Gtk.Align.CENTER)
        timezone_box.set_valign(Gtk.Align.END)
        timezone_box.get_style_context().add_class("timezone-box")
        timezone_box.set_margin_bottom(15)
        timezone_box.set_size_request(280, -1)  # Ancho más estrecho
        
        # Etiqueta para la zona horaria
        self.timezone_label = Gtk.Label()
        self.timezone_label.set_markup("<span color='white' size='large' weight='bold'>Europe/Madrid</span>")
        self.timezone_label.get_style_context().add_class("region-label")
        
        # Etiqueta para la hora actual
        self.time_label = Gtk.Label()
        self.time_label.set_markup("<span color='white' size='x-large' weight='bold'>00:00</span>")
        self.time_label.get_style_context().add_class("time-label")
        self.time_label.set_margin_start(20)
        
        timezone_box.pack_start(self.timezone_label, False, False, 0)
        timezone_box.pack_start(self.time_label, False, False, 0)
        
        # Añadir la caja de timezone como overlay
        map_overlay.add_overlay(timezone_box)
        
        # Añadir el contenido principal
        self.content.pack_start(main_content, True, True, 0)
        
        # Estilizar los botones del pie de página
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        bottom_box.set_margin_top(10)
        bottom_box.set_margin_start(10)
        bottom_box.set_margin_end(10)
        bottom_box.set_margin_bottom(5)
        
        # Información de idioma con estilo mejorado
        language_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        language_box.get_style_context().add_class("info-box")
        language_box.set_margin_bottom(2)
        
        self.language_label = Gtk.Label("El idioma del sistema se establecerá a español de España (España).")
        self.language_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.25, 0.88, 0.82, 1.0))
        self.language_label.set_halign(Gtk.Align.START)
        self.language_label.set_hexpand(True)
        
        # Botones "Cambiar..." un poco más largos
        change_language_button = Gtk.Button(label="Cambiar...")
        change_language_button.set_halign(Gtk.Align.END)
        change_language_button.set_size_request(150, -1)  # Aumentar ancho del botón
        change_language_button.connect("clicked", self.on_change_language_clicked)
        
        language_box.pack_start(self.language_label, True, True, 0)
        language_box.pack_end(change_language_button, False, False, 0)
        
        # Información de localización con estilo mejorado
        locale_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        locale_box.get_style_context().add_class("info-box")
        locale_box.set_margin_top(5)
        
        self.locale_label = Gtk.Label("La localización de números y fechas se establecerá a español de España (España).")
        self.language_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.25, 0.88, 0.82, 1.0))
        self.locale_label.set_halign(Gtk.Align.START)
        self.locale_label.set_hexpand(True)
        
        change_locale_button = Gtk.Button(label="Cambiar...")
        change_locale_button.set_halign(Gtk.Align.END)
        change_locale_button.set_size_request(150, -1)  # Aumentar ancho del botón
        change_locale_button.connect("clicked", self.on_change_locale_clicked)
        
        locale_box.pack_start(self.locale_label, True, True, 0)
        locale_box.pack_end(change_locale_button, False, False, 0)
        
        # Añadir al contenedor inferior
        bottom_box.pack_start(language_box, False, False, 0)
        bottom_box.pack_start(locale_box, False, False, 0)
        
        # Añadir el contenedor inferior al contenido principal
        self.content.pack_start(bottom_box, False, False, 0)
        
        # Inicializar datos de zonas horarias
        self.init_timezones()
        
        # Rellenar los selectores
        self.populate_selectors()
        
        # Conectar señales
        self.region_combo.connect('changed', self.on_region_changed)
        self.zone_combo.connect('changed', self.on_zone_changed)
        
        # Actualizar la hora periódicamente
        GLib.timeout_add_seconds(1, self.update_time_label)
    
    def init_timezones(self):
        """Inicializa los datos de zonas horarias"""
        self.timezones = {
            "Africa": ["Abidjan", "Accra", "Addis_Ababa", "Algiers", "Cairo", "Casablanca", "Dakar", "Johannesburg", "Lagos", "Nairobi", "Tunis"],
            "America": ["Argentina/Buenos_Aires", "Bogota", "Caracas", "Chicago", "Denver", "Havana", "Lima", "Los_Angeles", "Mexico_City", "New_York", "Santiago", "Sao_Paulo", "Toronto"],
            "Asia": ["Baghdad", "Bangkok", "Dubai", "Hong_Kong", "Jerusalem", "Karachi", "Kolkata", "Kuala_Lumpur", "Singapore", "Shanghai", "Tokyo"],
            "Australia": ["Adelaide", "Brisbane", "Melbourne", "Perth", "Sydney"],
            "Europe": ["Amsterdam", "Athens", "Berlin", "Brussels", "Dublin", "Lisbon", "London", "Madrid", "Moscow", "Paris", "Rome", "Stockholm", "Vienna"],
            "Pacific": ["Auckland", "Fiji", "Honolulu"]
        }
    
    def populate_selectors(self):
        """Rellena los selectores de región y zona"""
        # Obtener las regiones ordenadas
        region_names = sorted(self.timezones.keys())
        
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
        zones = sorted([zone.replace('_', ' ') for zone in self.timezones.get(region, [])])
        
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
            
            # Cambiar automáticamente el idioma según la región
            if region == "Europe":
                if "Spain" in self.timezones.get("Europe", []) or "Madrid" in self.timezones.get("Europe", []):
                    self.language_label.set_text("El idioma del sistema se establecerá a español de España (España).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a español de España (España).")
                elif "France" in self.timezones.get("Europe", []) or "Paris" in self.timezones.get("Europe", []):
                    self.language_label.set_text("El idioma del sistema se establecerá a francés de Francia (Francia).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a francés de Francia (Francia).")
                elif "Germany" in self.timezones.get("Europe", []) or "Berlin" in self.timezones.get("Europe", []):
                    self.language_label.set_text("El idioma del sistema se establecerá a alemán de Alemania (Alemania).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a alemán de Alemania (Alemania).")
                elif "United_Kingdom" in self.timezones.get("Europe", []) or "London" in self.timezones.get("Europe", []):
                    self.language_label.set_text("El idioma del sistema se establecerá a inglés de Reino Unido (UK).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a inglés de Reino Unido (UK).")
                else:
                    self.language_label.set_text("El idioma del sistema se establecerá a inglés de Estados Unidos (US).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a inglés de Estados Unidos (US).")
            elif region == "America":
                self.language_label.set_text("El idioma del sistema se establecerá a inglés de Estados Unidos (US).")
                self.locale_label.set_text("La localización de números y fechas se establecerá a inglés de Estados Unidos (US).")
            elif region == "Asia":
                self.language_label.set_text("El idioma del sistema se establecerá a inglés Internacional (EN).")
                self.locale_label.set_text("La localización de números y fechas se establecerá a inglés Internacional (EN).")
            elif region == "Africa":
                # Determinar el idioma según la zona seleccionada
                zone = self.zone_combo.get_active_text()
                if zone in ["Cairo", "Algiers", "Tunis", "Casablanca"]:
                    self.language_label.set_text("El idioma del sistema se establecerá a árabe (العربية).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a árabe (العربية).")
                else:
                    self.language_label.set_text("El idioma del sistema se establecerá a inglés Internacional (EN).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a inglés Internacional (EN).")
            else:
                self.language_label.set_text("El idioma del sistema se establecerá a inglés Internacional (EN).")
                self.locale_label.set_text("La localización de números y fechas se establecerá a inglés Internacional (EN).")
    
    def on_zone_changed(self, widget):
        """Manejador para el cambio de zona en el selector"""
        region = self.region_combo.get_active_text()
        zone = self.zone_combo.get_active_text()
        
        if region and zone:
            zone_name = zone.replace(' ', '_')
            timezone = f"{region}/{zone_name}"
            
            # Actualizar la zona horaria en configuración
            if hasattr(self.app, 'setup'):
                self.app.setup.timezone = timezone
            
            # Actualizar la etiqueta de zona horaria
            self.timezone_label.set_markup(f"<span color='white' size='large' weight='bold'>{timezone}</span>")
            
            # Actualizar la hora
            self.update_time_label()
            
            # Actualizar idioma según la zona específica
            if region == "Europe":
                if zone == "Madrid" or zone == "Barcelona":
                    self.language_label.set_text("El idioma del sistema se establecerá a español de España (España).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a español de España (España).")
                elif zone == "Paris":
                    self.language_label.set_text("El idioma del sistema se establecerá a francés de Francia (Francia).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a francés de Francia (Francia).")
                elif zone == "Berlin":
                    self.language_label.set_text("El idioma del sistema se establecerá a alemán de Alemania (Alemania).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a alemán de Alemania (Alemania).")
                elif zone == "Rome":
                    self.language_label.set_text("El idioma del sistema se establecerá a italiano de Italia (Italia).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a italiano de Italia (Italia).")
                elif zone == "London":
                    self.language_label.set_text("El idioma del sistema se establecerá a inglés de Reino Unido (UK).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a inglés de Reino Unido (UK).")
                elif zone == "Lisbon":
                    self.language_label.set_text("El idioma del sistema se establecerá a portugués de Portugal (Portugal).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a portugués de Portugal (Portugal).")
                elif zone == "Moscow":
                    self.language_label.set_text("El idioma del sistema se establecerá a ruso de Rusia (Россия).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a ruso de Rusia (Россия).")
            elif region == "America":
                if zone == "Argentina/Buenos Aires":
                    self.language_label.set_text("El idioma del sistema se establecerá a español de Argentina (Argentina).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a español de Argentina (Argentina).")
                elif zone == "Mexico City":
                    self.language_label.set_text("El idioma del sistema se establecerá a español de México (México).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a español de México (México).")
                elif zone in ["New York", "Chicago", "Denver", "Los Angeles"]:
                    self.language_label.set_text("El idioma del sistema se establecerá a inglés de Estados Unidos (US).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a inglés de Estados Unidos (US).")
                elif zone == "Sao Paulo":
                    self.language_label.set_text("El idioma del sistema se establecerá a portugués de Brasil (Brasil).")
                    self.locale_label.set_text("La localización de números y fechas se establecerá a portugués de Brasil (Brasil).")
    
    def update_time_label(self):
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
            
            self.time_label.set_markup(f"<span color='white' size='x-large' weight='bold'>{current_time}</span>")
        except Exception as e:
            print(f"Error al actualizar la hora: {e}")
            self.time_label.set_markup("<span color='white' size='x-large' weight='bold'>--:--</span>")
        
        return True
    
    def on_change_language_clicked(self, button):
        """Manejador de evento para el botón de cambiar idioma"""
        dialog = Gtk.Dialog(
            title="Cambiar idioma del sistema",
            parent=None,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(
                "Cancelar", Gtk.ResponseType.CANCEL,
                "Aceptar", Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(400, 300)
        
        content_area = dialog.get_content_area()
        content_area.set_border_width(15)
        content_area.set_spacing(10)
        
        label = Gtk.Label("Seleccione el idioma del sistema:")
        label.set_halign(Gtk.Align.START)
        content_area.add(label)
        
        # Selector de idiomas
        combo = Gtk.ComboBoxText()
        combo.append_text("Español (España)")
        combo.append_text("English (US)")
        combo.append_text("Français (France)")
        combo.set_active(0)
        content_area.add(combo)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            selected_language = combo.get_active_text()
            print(f"Idioma seleccionado: {selected_language}")
            
            # Actualizar la etiqueta para reflejar el cambio
            if selected_language == "English (US)":
                self.language_label.set_text("El idioma del sistema se establecerá a inglés de Estados Unidos (US).")
            elif selected_language == "Français (France)":
                self.language_label.set_text("El idioma del sistema se establecerá a francés de Francia (Francia).")
            else:
                self.language_label.set_text("El idioma del sistema se establecerá a español de España (España).")
        
        dialog.destroy()
    
    def on_change_locale_clicked(self, button):
        """Manejador de evento para el botón de cambiar localización"""
        dialog = Gtk.Dialog(
            title="Cambiar localización",
            parent=None,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(
                "Cancelar", Gtk.ResponseType.CANCEL,
                "Aceptar", Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(400, 300)
        
        content_area = dialog.get_content_area()
        content_area.set_border_width(15)
        content_area.set_spacing(10)
        
        label = Gtk.Label("Seleccione la localización para números y fechas:")
        label.set_halign(Gtk.Align.START)
        content_area.add(label)
        
        # Selector de localizaciones
        combo = Gtk.ComboBoxText()
        combo.append_text("Español (España)")
        combo.append_text("English (US)")
        combo.append_text("Français (France)")
        combo.set_active(0)
        content_area.add(combo)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            selected_locale = combo.get_active_text()
            
            # Actualizar la etiqueta para reflejar el cambio
            if selected_locale == "English (US)":
                self.locale_label.set_text("La localización de números y fechas se establecerá a inglés de Estados Unidos (US).")
            elif selected_locale == "Français (France)":
                self.locale_label.set_text("La localización de números y fechas se establecerá a francés de Francia (Francia).")
            else:
                self.locale_label.set_text("La localización de números y fechas se establecerá a español de España (España).")
        
        dialog.destroy()
    
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
