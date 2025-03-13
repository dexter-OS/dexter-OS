#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# DexterOS Installer - Página de configuración de teclado
# Version: 1.0
# Author: Victor Oubiña <oubinav78@gmail.com>
#

import os
import gi
import gettext
import subprocess

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

class KeyboardPage:
    """Página de selección de distribución de teclado"""
    
    def __init__(self, app):
        """Inicializa la página de configuración de teclado"""
        self.app = app
        
        # Configuración predeterminada de teclado
        self.default_layout = "es"
        self.default_variant = ""
        
        # Inicializar la configuración si no existe
        if not hasattr(app, 'setup'):
            class Setup:
                pass
            app.setup = Setup()
        
        # Establecer configuración predeterminada de teclado
        if not hasattr(app.setup, 'keyboard'):
            app.setup.keyboard = {
                'layout': self.default_layout,
                'variant': self.default_variant
            }
        
        # Cargar CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('/usr/share/dexter-installer/styles/style.css')
        
        # Aplicar proveedor CSS
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Crear contenedor principal
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.content.set_margin_bottom(15)
        self.content.set_size_request(850, 300)
        
        # Contenedor de título
        title_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title_container.get_style_context().add_class("title-header")
        title_container.set_hexpand(True)
        
        # Cargar ícono
        icon_path = "/usr/share/dexter-installer/images/icons/teclado.svg"
        try:
            icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 48, 48)
            icon_image = Gtk.Image.new_from_pixbuf(icon_pixbuf)
            title_container.pack_start(icon_image, False, False, 10)
        except Exception as e:
            print("Error cargando el icono de teclado:", e)
        
        # Etiquetas de título
        title_labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        title = Gtk.Label()
        title.set_markup("<span foreground='white' size='xx-large' weight='bold'>Configuración del Teclado</span>")
        title.set_halign(Gtk.Align.START)
        title.set_margin_start(10)
        title.set_margin_top(10)
        title.set_margin_bottom(5)
        
        subtitle = Gtk.Label()
        subtitle.set_markup("<span foreground='white' size='medium'>Seleccione la distribución de su teclado</span>")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_margin_start(200)
        subtitle.set_margin_bottom(10)
        
        title_labels.pack_start(title, False, False, 0)
        title_labels.pack_start(subtitle, False, False, 0)
        title_container.pack_start(title_labels, False, False, 0)
        
        self.content.pack_start(title_container, False, False, 0)
        
        # Contenedor principal para teclado y selectores
        main_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        main_content.set_halign(Gtk.Align.CENTER)
        main_content.set_margin_top(10)
        main_content.set_size_request(830, 300)  # Establecer límite explícito de tamaño
        
        # Cargar imagen del teclado
        keyboard_image = Gtk.Image()
        try:
            keyboard_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                '/usr/share/dexter-installer/images/keyboard.png', 
                700, 200,  # Ajusta estos valores según tu preferencia
                True  # Mantener proporción
            )
            keyboard_image.set_from_pixbuf(keyboard_pixbuf)
            keyboard_image.set_halign(Gtk.Align.CENTER)
            main_content.pack_start(keyboard_image, False, False, 10)
        except Exception as e:
            print("Error cargando imagen de teclado:", e)
        
        # Contenedor para selectores
        selector_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        # Selector de modelo de teclado
        model_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        model_label = Gtk.Label("Modelo de teclado:")
        model_label.get_style_context().add_class("label-text")
        
        self.model_combo = Gtk.ComboBoxText()
        self.model_combo.set_size_request(500, -1)
        self.model_combo.append_text("Generic 105 key-PC")
        self.model_combo.set_active(0)
        
        model_box.pack_start(model_label, False, False, 5)
        model_box.pack_start(self.model_combo, False, False, 0)
        selector_box.pack_start(model_box, False, False, 5)
        
        # Contenedor para los árboles (listas)
        tree_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Árbol de distribuciones
        layout_scroll = Gtk.ScrolledWindow()
        layout_scroll.set_size_request(300, 200)
        
        # Modelo para distribuciones
        self.layout_store = Gtk.ListStore(str, str)
        self.layout_tree = Gtk.TreeView(model=self.layout_store)
        
        # Columna de distribución
        layout_column = Gtk.TreeViewColumn("Layout", Gtk.CellRendererText(), text=0)
        self.layout_tree.append_column(layout_column)
        layout_column.set_expand(True)
        
        # Columna de descripción
        desc_column = Gtk.TreeViewColumn("Descripción", Gtk.CellRendererText(), text=1)
        self.layout_tree.append_column(desc_column)
        desc_column.set_expand(True)
        
        layout_scroll.add(self.layout_tree)
        tree_box.pack_start(layout_scroll, True, True, 0)
        
        # Árbol de variantes
        variant_scroll = Gtk.ScrolledWindow()
        variant_scroll.set_size_request(300, 200)
        
        # Modelo para variantes
        self.variant_store = Gtk.ListStore(str, str)
        self.variant_tree = Gtk.TreeView(model=self.variant_store)
        
        # Columna de variante
        variant_column = Gtk.TreeViewColumn("Variante", Gtk.CellRendererText(), text=0)
        self.variant_tree.append_column(variant_column)
        variant_column.set_expand(True)
        
        # Columna de descripción de variante
        variant_desc_column = Gtk.TreeViewColumn("Descripción", Gtk.CellRendererText(), text=1)
        self.variant_tree.append_column(variant_desc_column)
        variant_desc_column.set_expand(True)
        
        variant_scroll.add(self.variant_tree)
        tree_box.pack_start(variant_scroll, True, True, 0)
        
        # Añadir área de árboles al contenedor de selectores
        selector_box.pack_start(tree_box, False, False, 5)
        
        # Área de prueba de teclado
        test_frame = Gtk.Frame(label="Probar distribución de teclado")
        test_frame.set_margin_top(10)
        
        test_entry = Gtk.Entry()
        test_entry.set_placeholder_text("Escriba aquí para probar su distribución de teclado")
        test_frame.add(test_entry)
        selector_box.pack_start(test_frame, False, False, 5)
        
        # Añadir selectores al contenido principal
        main_content.pack_start(selector_box, False, False, 0)
        
        # Añadir contenido principal al contenedor principal
        self.content.pack_start(main_content, False, False, 0)
        
        # Cargar distribuciones de teclado
        self.load_keyboard_layouts()
        
        # Conectar señales
        self.layout_tree.connect('row-activated', self.on_layout_selected)
        self.variant_tree.connect('row-activated', self.on_variant_selected)
        
        # Configurar valores iniciales
        self.populate_initial_layout()
    
    def load_keyboard_layouts(self):
        """Cargar las distribuciones de teclado disponibles"""
        try:
            # Layouts más comunes
            common_layouts = [
                ('es', 'Español (España)'),
                ('us', 'English (US)'),
                ('fr', 'Français (Francia)'),
                ('de', 'Deutsch (Alemania)'),
                ('it', 'Italiano (Italia)'),
                ('gb', 'English (UK)'),
                ('latam', 'Español (Latinoamérica)'),
                ('br', 'Português (Brasil)'),
                ('ru', 'Русский (Rusia)'),
                ('ara', 'العربية (Árabe)')
            ]
            
            # Limpiar combo
            self.layout_store.clear()
            
            # Añadir layouts
            for code, name in common_layouts:
                self.layout_store.append([code, name])
        
        except Exception as e:
            print(f"Error cargando layouts de teclado: {e}")
            # Layout por defecto si falla
            self.layout_store.append(['es', 'Español (España)'])
    
    def load_keyboard_variants(self, layout):
        """Cargar las variantes de un layout específico"""
        # Limpiar variantes
        self.variant_store.clear()
        
        # Variantes predeterminadas para algunos layouts
        variants = {
            'es': [
                ('', 'Predeterminado'), 
                ('cat', 'Catalán'), 
                ('ast', 'Asturiano')
            ],
            'us': [
                ('', 'Predeterminado'), 
                ('dvorak', 'Dvorak'), 
                ('cherokee', 'Cherokee'), 
                ('classic', 'English (Classic Dvorak)'), 
                ('colemak', 'Colemak'), 
                ('colemak-dh', 'Colemak-DH'), 
                ('colemak-dh-iso', 'Colemak-DH ISO')
            ],
            'fr': [
                ('', 'Predeterminado'), 
                ('azerty', 'AZERTY'), 
                ('canadian', 'Canadá')
            ],
            'de': [('', 'Predeterminado'), ('neo', 'Neo 2')],
            'it': [('', 'Predeterminado')],
            'gb': [('', 'Predeterminado'), ('dvorak', 'Dvorak')],
            'latam': [('', 'Predeterminado')],
            'br': [('', 'Predeterminado')],
            'ru': [('', 'Predeterminado')],
            'ara': [('', 'Predeterminado')]
        }
        
        # Obtener las variantes para el layout actual
        current_variants = variants.get(layout, [('', 'Predeterminado')])
        
        # Añadir variantes
        for variant in current_variants:
            self.variant_store.append(variant)
    
    def on_layout_selected(self, tree_view, path, column):
        """Manejador cuando se selecciona un layout"""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        layout_code = model.get_value(iter, 0)
        
        # Cargar variantes para este layout
        self.load_keyboard_variants(layout_code)
        
        # Configurar layout actual
        if hasattr(self.app, 'setup'):
            self.app.setup.keyboard = {
                'layout': layout_code,
                'variant': ''
            }
    
    def on_variant_selected(self, tree_view, path, column):
        """Manejador cuando se selecciona una variante"""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        variant = model.get_value(iter, 0)
        
        if hasattr(self.app, 'setup'):
            # Obtener el código de layout actual
            layout_model = self.layout_tree.get_model()
            layout_iter = self.layout_tree.get_selection().get_selected()[1]
            layout_code = layout_model.get_value(layout_iter, 0)
            
            # Actualizar configuración de teclado
            self.app.setup.keyboard = {
                'layout': layout_code,
                'variant': variant or ''
            }
    
    def populate_initial_layout(self):
        """Establecer layout inicial"""
        # Seleccionar el layout español por defecto
        for i, row in enumerate(self.layout_store):
            if row[0] == self.default_layout:
                selection = self.layout_tree.get_selection()
                selection.select_path(Gtk.TreePath(i))
                break
        
        # Cargar variantes para el layout inicial
        self.load_keyboard_variants(self.default_layout)
    
    def get_content(self):
        """Devuelve el contenedor principal de la página"""
        return self.content
    
    def validate(self):
        """Valida que se haya seleccionado un layout"""
        try:
            # Verificar si hay una selección en el árbol de layouts
            selection = self.layout_tree.get_selection()
            model, iter = selection.get_selected()
            
            return (iter is not None and 
                    hasattr(self.app, 'setup') and 
                    hasattr(self.app.setup, 'keyboard') and 
                    self.app.setup.keyboard.get('layout'))
        except Exception as e:
            print(f"Error en validación de teclado: {e}")
            return False
    
    def save(self):
        """Guarda la configuración de teclado"""
        try:
            selection = self.layout_tree.get_selection()
            model, iter = selection.get_selected()
            
            if iter and hasattr(self.app, 'setup'):
                layout_code = model.get_value(iter, 0)
                
                # Obtener la variante seleccionada
                variant_selection = self.variant_tree.get_selection()
                variant_model, variant_iter = variant_selection.get_selected()
                variant = variant_model.get_value(variant_iter, 0) if variant_iter else ''
                
                self.app.setup.keyboard = {
                    'layout': layout_code,
                    'variant': variant
                }
                
                return self.app.setup.keyboard
        except Exception as e:
            print(f"Error guardando configuración de teclado: {e}")
        
        return {
            'layout': self.default_layout,
            'variant': self.default_variant
        }
