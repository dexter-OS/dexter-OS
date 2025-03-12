#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gi
import gettext
import subprocess
import sys

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

# Configurar traducción
_ = gettext.gettext

class LanguagePage:
    """Página de selección de idioma del instalador DexterOS"""
    
    def __init__(self, app):
        """Inicializa la página de selección de idioma"""
        self.app = app
        self.scale = 1
        
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
        icon_path = "/usr/share/dexter-installer/images/icons/idioma.svg"
        try:
            icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 48, 48)
            icon_image = Gtk.Image.new_from_pixbuf(icon_pixbuf)
        except Exception as e:
            print(f"Error cargando el icono de idioma: {e}")
            icon_image = None
    
        # Título de la página con esquinas redondeadas
        title_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title_container.get_style_context().add_class("title-header")  # Aplicar la clase CSS
        title_container.set_hexpand(True)
        
        # Añadir el icono si se cargó correctamente
        if icon_image:
            title_container.pack_start(icon_image, False, False, 10)
            
        # Contenedor vertical para títulos
        title_labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    
        # Título de la página
        title = Gtk.Label()
        title.set_markup("<span foreground='white' size='xx-large' weight='bold'>{}</span>".format(
            _("¿En qué idioma quieres instalar DexterOS?")))
        title.set_halign(Gtk.Align.START)
        title.set_margin_start(10)
        title.set_margin_top(10)
        title.set_margin_bottom(10)
        
        subtitle = Gtk.Label()
        subtitle.set_markup("<span foreground='white' size='medium'>{}</span>".format(
            _("Selecciona tu idioma de preferencia")))
        subtitle.set_halign(Gtk.Align.CENTER)
        subtitle.set_margin_start(350)
        subtitle.set_margin_bottom(10)
        
        # Añadir los labels al title_labels
        title_labels.pack_start(title, False, False, 0)
        title_labels.pack_start(subtitle, False, False, 0)

        # Añadir title_labels al title_container
        title_container.pack_start(title_labels, False, False, 0)

        # Añadir title_container al contenedor principal
        self.content.pack_start(title_container, False, False, 0)

        # Scrolled Window para la lista de idiomas
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        
        # Crear TreeView
        self.treeview = Gtk.TreeView()
        self.treeview.set_headers_visible(True)
        
        # Columna de banderas
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_pixbuf = Gtk.TreeViewColumn(_("Banderas"), renderer_pixbuf, pixbuf=0)
        column_pixbuf.set_min_width(50)
        column_pixbuf.set_max_width(80)
        column_pixbuf.set_sort_column_id(0)  # Permite ordenar por esta columna
        column_pixbuf.set_clickable(True)    # Hace la columna clickable
        self.treeview.append_column(column_pixbuf)
        
        # Columna de idioma
        renderer_text = Gtk.CellRendererText()
        renderer_text.set_property("foreground", "white")
        column_text = Gtk.TreeViewColumn(_("Idioma"), renderer_text, text=1)
        column_text.set_expand(True)
        column_text.set_sort_column_id(1)  # Permite ordenar por esta columna
        column_text.set_clickable(True)    # Hace la columna clickable
        column_text.set_resizable(True)    # Permite redimensionar la columna
        self.treeview.append_column(column_text)
        
        # Columna de país
        renderer_text2 = Gtk.CellRendererText()
        renderer_text2.set_property("foreground", "white")
        column_text2 = Gtk.TreeViewColumn(_("Localización"), renderer_text2, text=2)
        column_text2.set_expand(True)
        column_text2.set_sort_column_id(2)  # Permite ordenar por esta columna
        column_text2.set_clickable(True)    # Hace la columna clickable
        column_text2.set_resizable(True)    # Permite redimensionar la columna
        self.treeview.append_column(column_text2)
        
        # Crear modelo para el TreeView
        self.store = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str)  # bandera, idioma, país, locale
        self.treeview.set_model(self.store)
        
        # Conectar señal de selección
        self.treeview.connect("cursor-changed", self.on_language_selected)
        
        # Añadir TreeView al ScrolledWindow
        scrolled_window.add(self.treeview)
        
        # Aplicar color de fondo
        background_box = Gtk.Box()
        background_box.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.129, 0.157, 0.212, 1.0))  # #212836
        background_box.add(scrolled_window)
        
        self.content.pack_start(background_box, True, True, 0)
        
        # Aplicar estilos CSS
        css_provider = Gtk.CssProvider()
        css = """
        treeview {
            background-color: #212836;
            color: #40E0D0;
        }
        
        treeview header button {
            background-color: #1e1e1e;
            color: #40E0D0;
            font-weight: bold;
            border: none;
            border-radius: 0;
            box-shadow: none;
            text-shadow: none;
        }
        
        treeview header button:hover {
            background-color: #1e1e1e;
            color: #00FFFF;
        }
        
        treeview header button:active {
            background-color: #4c566a;
        }
        
        treeview row:selected {
            background-color: #3584e4;
            color: white;
        }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Cargar idiomas
        self.load_languages()
    
    def load_languages(self):
        """Cargar idiomas y países en el modelo"""
        try:
            # Cargar nombres de idiomas - ISO 639-1 (códigos de 2 letras)
            languages = {}
            try:
                output = subprocess.getoutput("isoquery --iso 639-2 | cut -f3,4-")
                for line in output.splitlines():
                    parts = line.split('\t')
                    if len(parts) >= 2 and parts[0].strip():  # asegurarse de que el código existe
                        code = parts[0].strip()
                        name = parts[1].strip()
                        languages[code] = name
            except Exception as e:
                print(f"ERROR: Al cargar idiomas: {e}")
            
            # Cargar nombres de países - ISO 3166-1 (códigos de 2 letras)
            countries = {}
            try:
                output = subprocess.getoutput("isoquery --iso 3166-1 | cut -f1,4-")
                for line in output.splitlines():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        code = parts[0].strip()
                        name = parts[1].strip()
                        countries[code] = name
            except Exception as e:
                print(f"ERROR: Al cargar países: {e}")
            
            # Obtener locales soportados
            locales = []
            try:
                output = subprocess.getoutput("awk -F'[@ .]' '/UTF-8/{ print $1 }' /usr/share/i18n/SUPPORTED | sort | uniq")
                locales = [loc for loc in output.splitlines() if '_' in loc]
            except Exception as e:
                print(f"ERROR: Al obtener locales: {e}")
            
            # Añadir entradas al modelo
            for locale in locales:
                try:
                    if '_' in locale:
                        lang_code, country_code = locale.split('_')
                        
                        # Obtener el nombre del idioma
                        language_name = languages.get(lang_code, lang_code)
                        
                        # Obtener el nombre del país
                        country_name = countries.get(country_code, country_code)
                        
                        # Cargar bandera
                        flag_path = f"/usr/share/dexter-installer/images/flags/{country_code.lower()}.svg"
                        if not os.path.exists(flag_path):
                            flag_path = f"/usr/share/dexter-installer/images/flags/{country_code.lower()}.png"
                        
                        pixbuf = None
                        if os.path.exists(flag_path):
                            try:
                                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(flag_path, 24, 24)
                            except Exception as e:
                                print(f"ERROR: Al cargar bandera {flag_path}: {e}")
                        
                        # Añadir al modelo
                        self.store.append([pixbuf, language_name, country_name, locale])
                except Exception as e:
                    print(f"ERROR: Al procesar locale {locale}: {e}")
            
            # Ordenar el modelo por idioma inicialmente
            self.store.set_sort_column_id(1, Gtk.SortType.ASCENDING)
            
            # Seleccionar el idioma actual del sistema
            try:
                current_locale = os.environ.get('LANG', 'en_US.UTF-8').split('.')[0]
                
                iter = self.store.get_iter_first()
                while iter:
                    if self.store.get_value(iter, 3) == current_locale:
                        path = self.store.get_path(iter)
                        self.treeview.set_cursor(path)
                        self.treeview.scroll_to_cell(path)
                        break
                    iter = self.store.iter_next(iter)
            except Exception as e:
                print(f"ERROR: Al seleccionar locale actual: {e}")
            
        except Exception as e:
            print(f"ERROR CRÍTICO en load_languages: {e}")
            import traceback
            traceback.print_exc()
    
    def on_language_selected(self, treeview):
        """Manejar la selección de idioma"""
        selection = treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            language = model.get_value(iter, 1)
            country = model.get_value(iter, 2)
            locale = model.get_value(iter, 3)
            
            # Configurar el idioma seleccionado
            self.app.config.language = locale  # Cambiar de setup a config
            print(f"Idioma seleccionado: {language} ({country}) - Locale: {locale}")
    
    def get_content(self):
        """Retorna el contenido de la página"""
        return self.content
    
    def validate(self):
        """Valida la selección de idioma"""
        selection = self.treeview.get_selection()
        model, iter = selection.get_selected()
        return iter is not None
    
    def save(self):
        """Guarda la selección de idioma"""
        selection = self.treeview.get_selection()
        model, iter = selection.get_selected()
        
        if iter:
            language = model.get_value(iter, 1)
            country = model.get_value(iter, 2)
            locale = model.get_value(iter, 3)
            
            # Guardar configuración de idioma
            self.app.config.language = locale  # Cambiar de setup a config
            print(f"Guardando idioma: {language} ({country}) - Locale: {locale}")
            
            return True
        return False
