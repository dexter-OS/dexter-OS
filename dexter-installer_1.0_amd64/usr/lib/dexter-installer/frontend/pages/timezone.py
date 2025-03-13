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
import sys
import time
import locale
import json

# Constantes para el mapa
MAP_FILE_PNG = '/usr/share/dexter-installer/maps/miller.png'
MAP_SIZE = (800, 306)
MAP_CENTER = (200, 153)

# Añadir la ruta para importar el gestor de idiomas
sys.path.insert(0, '/usr/lib/dexter-installer')
from helpers.language_manager import LanguageManager

class TimezonePage:
    """Página de selección de zona horaria"""
    
    def __init__(self, app):
        """Inicializa la página de zona horaria"""
        self.app = app
        
        # Inicializar gestor de idiomas
        self.lang_manager = LanguageManager()
            
        # Valores predeterminados
        self.default_region = "Europe"
        self.default_zone = "Madrid"
        self.default_timezone = "Europe/Madrid"
        self.default_language = "es"
        self.default_locale = "es_ES"
        
        # Cargar zonas horarias desde JSON
        self.load_timezones_from_json()
        
        # Obtener la configuración de idioma y zona horaria detectados
        detected_lang = self.lang_manager.get_detected_language()
        detected_variant = self.lang_manager.get_detected_variant()
        
        if detected_lang and detected_variant:
            # Actualizar los valores con lo detectado
            self.default_language = detected_lang["code"]
            self.default_locale = detected_variant["code"]
            
            # Si tiene zona horaria asociada, usarla
            if "timezone" in detected_variant:
                self.default_timezone = detected_variant["timezone"]
                if "/" in self.default_timezone:
                    parts = self.default_timezone.split("/")
                    self.default_region = parts[0]
                    self.default_zone = parts[1].replace("_", " ")
                    
        # Establecer zona horaria predeterminada
        class Setup:
            pass
        if not hasattr(app, 'setup'):
            app.setup = Setup()
        
        # Configurar idioma y zona horaria en la configuración de la app
        if not hasattr(app.setup, 'timezone') or app.setup.timezone is None:
            app.setup.timezone = self.default_timezone
        
        # Configuración de idioma y región
        if not hasattr(app.setup, 'language'):
            app.setup.language = self.default_language
            
        if not hasattr(app.setup, 'locale'):
            app.setup.locale = self.default_locale
        
        # Cargar el CSS externo
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('/usr/share/dexter-installer/styles/style.css')
        
        # Aplicar el proveedor CSS
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Crear el contenedor principal - REDUCIDO SPACING
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.content.set_margin_bottom(0) # Eliminar el margen inferior por completo
        self.content.set_size_request(850, 500)
        
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
        
        # Título de la página
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
        subtitle.set_margin_bottom(5)  # REDUCIDO MARGIN
        
        # Añadir los labels al title_labels
        title_labels.pack_start(title, False, False, 0)
        title_labels.pack_start(subtitle, False, False, 0)
        title_container.pack_start(title_labels, False, False, 0)
        self.content.pack_start(title_container, False, False, 0)
   
        # Selector de región y zona al inicio (encima del mapa)
        selector_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        selector_box.set_halign(Gtk.Align.CENTER)
        selector_box.set_margin_top(0)
        selector_box.set_margin_bottom(0)
        selector_box.get_style_context().add_class("selector-box")
        
        # Selector de región
        region_label = Gtk.Label("Región:")
        region_label.get_style_context().add_class("label-text")
        self.region_combo = Gtk.ComboBoxText()
        self.region_combo.set_size_request(350, -1)
        self.region_combo.get_style_context().add_class("region-combo")
        
        # Selector de zona
        zone_label = Gtk.Label("Zona:")
        zone_label.get_style_context().add_class("label-text")
        self.zone_combo = Gtk.ComboBoxText()
        self.zone_combo.set_size_request(350, -1)
        self.zone_combo.get_style_context().add_class("zone-combo")
        
        # Añadir componentes al selector_box
        selector_box.pack_start(region_label, False, False, 5)
        selector_box.pack_start(self.region_combo, False, False, 0)
        selector_box.pack_start(zone_label, False, False, 5)
        selector_box.pack_start(self.zone_combo, False, False, 0)
        
        # Añadir el selector al principio del contenido
        self.content.pack_start(selector_box, False, False, 0)
        
        # NUEVO: Crear overlay para el mapa y el reloj
        map_overlay = Gtk.Overlay()
        
        # Cargar el mapa directamente
        map_path = MAP_FILE_PNG
        map_image = Gtk.Image()
        try:
            if os.path.exists(map_path):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(map_path)
                # Ajustar el mapa al tamaño adecuado manteniendo la proporción
                screen_width = Gdk.Screen.get_default().get_width()
                target_width = 800  # Ancho máximo con margen
                target_height = int(target_width * pixbuf.get_height() / pixbuf.get_width())
                
                # Limitar también la altura para que no haga la ventana más alta
                max_height = 250  # REDUCIDO DE 250
                if target_height > max_height:
                    target_height = max_height
                    target_width = int(max_height * pixbuf.get_width() / pixbuf.get_height())
                    
                scaled_pixbuf = pixbuf.scale_simple(target_width, target_height, GdkPixbuf.InterpType.BILINEAR)
                map_image.set_from_pixbuf(scaled_pixbuf)
                
                # No expandir más allá del tamaño asignado
                map_image.set_size_request(target_width, target_height)

            # Añadir la imagen al overlay como widget principal
            map_overlay.add(map_image)
        except Exception as e:
            print(f"Error cargando el mapa: {e}")
        
        # Contenedor para mostrar la zona horaria seleccionada (reloj)
        timezone_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        timezone_box.set_halign(Gtk.Align.CENTER)
        timezone_box.set_valign(Gtk.Align.END)
        timezone_box.set_margin_bottom(10)
        timezone_box.get_style_context().add_class("timezone-box")
        timezone_box.set_size_request(280, -1)
        timezone_box.set_homogeneous(False)
        
        # Etiqueta para la zona horaria
        self.timezone_label = Gtk.Label()
        self.timezone_label.set_markup(f"<span color='white' size='large' weight='bold'>{self.default_timezone}</span>")
        self.timezone_label.get_style_context().add_class("region-label")
        
        # Etiqueta para la hora actual
        self.time_label = Gtk.Label()
        self.time_label.set_markup("<span color='white' size='x-large' weight='bold'>00:00</span>")
        self.time_label.get_style_context().add_class("time-label")
        self.time_label.set_width_chars(5)
        self.time_label.set_justify(Gtk.Justification.CENTER)
        self.time_label.set_xalign(0.5)
        self.time_label.set_margin_start(0)
        
        timezone_box.pack_start(self.timezone_label, True, True, 0)
        timezone_box.pack_start(self.time_label, True, True, 0)
        
        # Añadir el reloj como overlay
        map_overlay.add_overlay(timezone_box)
        
        # Añadir el overlay completo al contenido
        self.content.pack_start(map_overlay, False, False, 0)
        
        # Información de idioma - REDUCIDOS MÁRGENES
        language_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        language_box.get_style_context().add_class("info-box")
        language_box.set_margin_top(2)
        language_box.set_margin_bottom(2)
        language_box.set_margin_start(10)
        language_box.set_margin_end(10)
        
        # Texto combinado para idioma y región
        detected_lang = self.lang_manager.get_detected_language()
        detected_variant = self.lang_manager.get_detected_variant()
        if detected_lang and detected_variant:
            display_text = f"El idioma y región del sistema: {detected_lang['name']} ({detected_variant['name']})"
        else:
            display_text = "El idioma y región del sistema: español de España (Castellano)"

        self.language_label = Gtk.Label(display_text)
        self.language_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.25, 0.88, 0.82, 1.0))
        self.language_label.set_halign(Gtk.Align.START)
        self.language_label.set_hexpand(True)
        
        # Un único botón para cambiar idioma y región
        change_language_button = Gtk.Button(label="Cambiar idioma y región...")
        change_language_button.set_halign(Gtk.Align.END)
        change_language_button.set_size_request(200, -1)
        change_language_button.connect("clicked", self.on_change_language_clicked)
        
        # Añadir elementos al language_box
        language_box.pack_start(self.language_label, True, True, 0)
        language_box.pack_end(change_language_button, False, False, 0)
        
        # Añadir el language_box directamente al contenido principal
        self.content.pack_start(language_box, False, False, 0)
        
        # Rellenar los selectores
        self.populate_selectors()
        
        # Conectar señales
        self.region_combo.connect('changed', self.on_region_changed)
        self.zone_combo.connect('changed', self.on_zone_changed)
        
        # Actualizar la hora periódicamente
        GLib.timeout_add_seconds(1, self.update_time_label)
        
    def load_timezones_from_json(self):
        """Carga las zonas horarias desde el archivo languages.json"""
        self.timezones = {}
        self.default_zones = {}
        
        # Extraer las zonas horarias de los datos de idiomas
        for lang in self.lang_manager.get_all_languages():
            for variant in lang.get("variants", []):
                if "timezone" in variant:
                    timezone = variant["timezone"]
                    if "/" in timezone:
                        region, zone = timezone.split("/", 1)
                        
                        # Añadir región si no existe
                        if region not in self.timezones:
                            self.timezones[region] = []
                            
                        # Añadir zona si no existe ya
                        if zone not in self.timezones[region]:
                            self.timezones[region].append(zone)
        
        # Garantizar que al menos hay unas regiones mínimas
        essential_regions = ["Europe", "America", "Asia"]
        for region in essential_regions:
            if region not in self.timezones:
                self.timezones[region] = []
                
        # Garantizar que Europe tiene Madrid si está vacío
        if "Europe" in self.timezones and not self.timezones["Europe"]:
            self.timezones["Europe"].append("Madrid")
            
        # Configurar zonas predeterminadas por región (mínimo necesario)
        self.default_zones = {
            "Europe": "Madrid"
        }
        
    def get_language_display_text(self):
        """Obtiene el texto a mostrar para el idioma detectado"""
        # Obtener el nombre del idioma y variante para mostrarlo
        detected_lang = self.lang_manager.get_detected_language()
        detected_variant = self.lang_manager.get_detected_variant()
        
        if detected_lang and detected_variant:
            return f"El idioma del sistema se establecerá a {detected_lang['name']} ({detected_variant['name']})."
        else:
            # Valores por defecto si no se pudo detectar
            return "El idioma del sistema se establecerá a español de España (España)."
    
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
        
        # Seleccionar la región detectada por defecto
        region_found = False
        for i, region in enumerate(region_names):
            if region == self.default_region:
                self.region_combo.set_active(i)
                self.current_region = self.default_region
                # Rellenar las zonas para esta región
                self.populate_zones_for_region(self.default_region, self.default_zone)
                region_found = True
                break
        
        # Si no se encontró la región detectada, usar Europa como fallback
        if not region_found and 'Europe' in region_names:
            for i, region in enumerate(region_names):
                if region == 'Europe':
                    self.region_combo.set_active(i)
                    self.current_region = 'Europe'
                    self.populate_zones_for_region('Europe', 'Madrid')
                    break
        
    def populate_zones_for_region(self, region, default_zone=None):
        """Rellena el selector de zonas para una región específica"""
        # Limpiar el selector de zonas
        self.zone_combo.remove_all()
        
        # Obtener y ordenar las zonas para esta región
        zones = sorted([zone.replace('_', ' ') for zone in self.timezones.get(region, [])])
        
        # Añadir al selector
        for zone in zones:
            self.zone_combo.append_text(zone)
        
        # Seleccionar una zona predeterminada según la región
        if len(zones) > 0:
            # Si hay una zona predeterminada específica pasada como parámetro
            if default_zone and default_zone in zones:
                # Seleccionar la zona predeterminada proporcionada
                for i, zone in enumerate(zones):
                    if zone == default_zone:
                        self.zone_combo.set_active(i)
                        return
            
            # Si no hay zona predeterminada específica o no se encontró, usar el mapeo general
            region_default = self.default_zones.get(region)
            
            if region_default:
                region_default = region_default.replace('_', ' ')
                
            if region_default and region_default in zones:
                # Si existe la zona predeterminada, seleccionarla
                for i, zone in enumerate(zones):
                    if zone == region_default:
                        self.zone_combo.set_active(i)
                        break
            else:
                # Si no hay zona predeterminada o no existe, seleccionar la primera
                self.zone_combo.set_active(0)
        
    def on_region_changed(self, widget):
        """Manejador para el cambio de región en el selector"""
        region = self.region_combo.get_active_text()
        if region:
            self.current_region = region
            self.populate_zones_for_region(region)
    
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
            
            # Buscar si hay una variante de idioma que corresponda a esta zona horaria
            # y actualizar las etiquetas de idioma/localización si es apropiado
            self.update_language_based_on_timezone(timezone)
        
    def update_language_based_on_timezone(self, timezone):
        """Actualiza las etiquetas de idioma/localización según la zona horaria seleccionada"""
        # Recorrer todas las definiciones de idioma para encontrar coincidencia de timezone
        for lang in self.lang_manager.get_all_languages():
            for variant in lang.get("variants", []):
                if variant.get("timezone") == timezone:
                    # Actualizar las etiquetas de idioma y localización
                    self.language_label.set_text(f"El idioma y región del sistema: {lang['name']} ({variant['name']})")
                    
                    # Actualizar la configuración de la aplicación
                    if hasattr(self.app, 'setup'):
                        self.app.setup.language = lang["code"]
                        self.app.setup.locale = variant["code"]
                    
                    return
        
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
        """Manejador para el botón de cambiar idioma"""
        # Crear la ventana de selección de idioma con el título para idioma
        self.show_language_selector_dialog("Cambiar idioma del sistema")
        
    def show_language_selector_dialog(self, title="Selección de idioma y región"):
        """Muestra el diálogo para seleccionar idioma y variante regional"""
        dialog = Gtk.Dialog(
            title=title,
            parent=None,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(
                "Cancelar", Gtk.ResponseType.CANCEL,
                "Aceptar", Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(550, 400)
        dialog.get_style_context().add_class("language-selector-dialog")
        
        content_area = dialog.get_content_area()
        content_area.set_border_width(15)
        content_area.set_spacing(10)
        
        # Título
        title_label = Gtk.Label(label="Seleccione su idioma y región")
        title_label.set_markup("<span font_weight='bold' size='large'>Seleccione su idioma y región</span>")
        title_label.set_halign(Gtk.Align.START)
        content_area.add(title_label)
    
        # Contenedor para los selectores
        selector_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        selector_box.set_margin_top(10)
    
        # Grid para organizar los combos
        grid = Gtk.Grid()
        grid.set_column_spacing(15)
        grid.set_row_spacing(15)
        
        # Etiqueta para el idioma
        lang_label = Gtk.Label(label="Idioma:")
        lang_label.set_halign(Gtk.Align.START)
        grid.attach(lang_label, 0, 0, 1, 1)
        
        # ComboBox para idioma
        self.dialog_lang_store = Gtk.ListStore(str, str)  # code, name
        self.dialog_lang_combo = Gtk.ComboBox.new_with_model(self.dialog_lang_store)
        renderer_text = Gtk.CellRendererText()
        self.dialog_lang_combo.pack_start(renderer_text, True)
        self.dialog_lang_combo.add_attribute(renderer_text, "text", 1)
        grid.attach(self.dialog_lang_combo, 1, 0, 1, 1)
        
        # Etiqueta para la variante
        variant_label = Gtk.Label(label="Región:")
        variant_label.set_halign(Gtk.Align.START)
        grid.attach(variant_label, 0, 1, 1, 1)
        
        # ComboBox para variante
        self.dialog_variant_store = Gtk.ListStore(str, str, str)  # code, name, timezone
        self.dialog_variant_combo = Gtk.ComboBox.new_with_model(self.dialog_variant_store)
        renderer_text = Gtk.CellRendererText()
        self.dialog_variant_combo.pack_start(renderer_text, True)
        self.dialog_variant_combo.add_attribute(renderer_text, "text", 1)
        grid.attach(self.dialog_variant_combo, 1, 1, 1, 1)
        
        # Conectar evento de cambio de idioma
        self.dialog_lang_combo.connect("changed", self.on_dialog_language_changed)
        
        # Añadir grid al contenedor
        selector_box.pack_start(grid, False, False, 0)
        
        # Añadir separador
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        selector_box.pack_start(separator, False, False, 5)
        
        # Información sobre la selección actual
        info_label = Gtk.Label()
        info_label.set_markup("<b>Información de la selección:</b>")
        info_label.set_halign(Gtk.Align.START)
        selector_box.pack_start(info_label, False, False, 0)
        
        # Detalles de idioma
        self.dialog_info_label = Gtk.Label()
        self.dialog_info_label.set_markup("Seleccione un idioma y una región para continuar.")
        self.dialog_info_label.set_halign(Gtk.Align.START)
        self.dialog_info_label.set_line_wrap(True)
        selector_box.pack_start(self.dialog_info_label, False, False, 0)
        
        # Detalles de timezone
        self.dialog_timezone_label = Gtk.Label()
        self.dialog_timezone_label.set_markup("Zona horaria: <i>no seleccionada</i>")
        self.dialog_timezone_label.set_halign(Gtk.Align.START)
        selector_box.pack_start(self.dialog_timezone_label, False, False, 0)
        
        # Añadir el contenedor de selectores al diálogo
        content_area.add(selector_box)
        
        # Cargar datos en los combos
        self.populate_dialog_language_combo()
        
        # Establecer valores actuales
        if hasattr(self.app, 'setup'):
            current_lang = getattr(self.app.setup, 'language', None)
            current_locale = getattr(self.app.setup, 'locale', None)
            
            if current_lang:
                # Seleccionar el idioma actual
                for i, row in enumerate(self.dialog_lang_store):
                    if row[0] == current_lang:
                        self.dialog_lang_combo.set_active(i)
                        
                        # Cargar variantes y seleccionar la actual
                        if current_locale:
                            # Dar tiempo para que se carguen las variantes
                            while Gtk.events_pending():
                                Gtk.main_iteration()
                                
                            for i, row in enumerate(self.dialog_variant_store):
                                if row[0] == current_locale:
                                    self.dialog_variant_combo.set_active(i)
                                    break
                        break
            else:
                # Si no hay selección previa, usar la primera
                self.dialog_lang_combo.set_active(0)
        else:
            # Si no hay configuración, usar la primera opción
            self.dialog_lang_combo.set_active(0)
        
        # Actualizar información
        self.update_dialog_info()
        
        # Conectar evento para actualizar la información
        self.dialog_variant_combo.connect("changed", self.on_dialog_variant_changed)
        
        # Mostrar todos los elementos
        dialog.show_all()
        
        # Ejecutar el diálogo
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Obtener los valores seleccionados
            lang_iter = self.dialog_lang_combo.get_active_iter()
            variant_iter = self.dialog_variant_combo.get_active_iter()
            
            if lang_iter is not None and variant_iter is not None:
                lang_code = self.dialog_lang_store[lang_iter][0]
                lang_name = self.dialog_lang_store[lang_iter][1]
                
                variant_code = self.dialog_variant_store[variant_iter][0]
                variant_name = self.dialog_variant_store[variant_iter][1]
                timezone = self.dialog_variant_store[variant_iter][2]
                
                # Actualizar la configuración
                if hasattr(self.app, 'setup'):
                    self.app.setup.language = lang_code
                    self.app.setup.locale = variant_code
                    
                    # Actualizar también la zona horaria
                    if timezone:
                        self.app.setup.timezone = timezone
                        
                        # Actualizar la interfaz con la nueva zona horaria
                        self.timezone_label.set_markup(f"<span color='white' size='large' weight='bold'>{timezone}</span>")
                        
                        # Actualizar el selector de región/zona si corresponde
                        if '/' in timezone:
                            region, zone = timezone.split('/', 1)
                            zone = zone.replace('_', ' ')
                            
                            # Actualizar los selectores
                            for i, reg in enumerate(self.region_combo.get_model()):
                                if reg[0] == region:
                                    self.region_combo.set_active(i)
                                    
                                    # Dar tiempo para que se carguen las zonas
                                    while Gtk.events_pending():
                                        Gtk.main_iteration()
                                    
                                    # Buscar la zona
                                    for i, z in enumerate(self.zone_combo.get_model()):
                                        if z[0] == zone:
                                            self.zone_combo.set_active(i)
                                            break
                                    break
                
                # Actualizar las etiquetas
                self.language_label.set_text(f"El idioma y región del sistema: {lang_name} ({variant_name})")
        
        dialog.destroy()
        
    def populate_dialog_language_combo(self):
        """Rellena el combo de idiomas del diálogo"""
        # Limpiar el store
        self.dialog_lang_store.clear()
        
        # Añadir todos los idiomas
        for lang in self.lang_manager.get_all_languages():
            self.dialog_lang_store.append([lang["code"], lang["name"]])
    
    def on_dialog_language_changed(self, combo):
        """Maneja el cambio de idioma en el diálogo"""
        iter = combo.get_active_iter()
        if iter is not None:
            lang_code = self.dialog_lang_store[iter][0]
            
            # Actualizar el combo de variantes
            self.dialog_variant_store.clear()
            
            # Obtener las variantes para este idioma
            variants = self.lang_manager.get_language_variants(lang_code)
            
            for variant in variants:
                self.dialog_variant_store.append([
                    variant["code"], 
                    variant["name"], 
                    variant.get("timezone", "")
                ])
            
            # Seleccionar la primera variante por defecto
            if len(variants) > 0:
                self.dialog_variant_combo.set_active(0)
            
            # Actualizar la información
            self.update_dialog_info()
    
    def on_dialog_variant_changed(self, combo):
        """Maneja el cambio de variante en el diálogo"""
        # Actualizar la información
        self.update_dialog_info()
    
    def update_dialog_info(self):
        """Actualiza la información mostrada en el diálogo"""
        lang_iter = self.dialog_lang_combo.get_active_iter()
        variant_iter = self.dialog_variant_combo.get_active_iter()
        
        if lang_iter is not None and variant_iter is not None:
            lang_name = self.dialog_lang_store[lang_iter][1]
            variant_name = self.dialog_variant_store[variant_iter][1]
            timezone = self.dialog_variant_store[variant_iter][2]
            
            self.dialog_info_label.set_markup(f"<b>Idioma:</b> {lang_name}\n<b>Región:</b> {variant_name}")
            
            if timezone:
                self.dialog_timezone_label.set_markup(f"<b>Zona horaria:</b> {timezone}")
            else:
                self.dialog_timezone_label.set_markup("<b>Zona horaria:</b> <i>no especificada</i>")
    
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
        return self.default_timezone
