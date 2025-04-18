#!/usr/bin/env python3

import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2, GLib, Gdk, GtkSource, Pango

class DexterView(Gtk.Box):
    def __init__(self, parent_window=None):
        super(DexterView, self).__init__(orientation=Gtk.Orientation.VERTICAL)
        self.parent_window = parent_window
        self.document = None
        self.is_html = False
        self.view_mode = "normal"  # normal o code para HTML
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.set_name("dexter-view")
        
        # Contenedor principal
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.set_name("view-main-box")
        self.main_box.set_hexpand(True)
        self.main_box.set_vexpand(True)
        
        # Header con información del documento
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.header_box.set_name("view-header-box")
        self.header_box.set_margin_start(10)
        self.header_box.set_margin_end(10)
        self.header_box.set_margin_top(10)
        self.header_box.set_margin_bottom(10)
        
        # Icono del documento
        self.doc_icon = Gtk.Image.new_from_icon_name("text-x-generic-symbolic", Gtk.IconSize.DIALOG)
        self.doc_icon.set_name("view-document-icon")
        
        # Info del documento
        self.info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.info_box.set_margin_start(10)
        
        # Título del documento
        self.title_label = Gtk.Label(label="Documento")
        self.title_label.set_name("view-document-title")
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.set_hexpand(True)
        
        # Tipo de documento
        self.type_label = Gtk.Label(label="Tipo: Documento de texto")
        self.type_label.set_name("view-document-type")
        self.type_label.set_halign(Gtk.Align.START)
        
        # Añadir etiquetas al info_box
        self.info_box.pack_start(self.title_label, False, False, 0)
        self.info_box.pack_start(self.type_label, False, False, 5)
        
        # Botón para alternar vista de HTML (solo visible para HTML)
        self.view_mode_button = Gtk.Button()
        self.view_mode_button.set_relief(Gtk.ReliefStyle.NONE)
        self.view_mode_button.set_name("view-mode-button")
        self.view_mode_button.set_tooltip_text("Cambiar vista")
        self.view_mode_button.set_image(Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON))
        self.view_mode_button.connect("clicked", self.toggle_view_mode)
        self.view_mode_button.set_no_show_all(True)  # Oculto por defecto
        
        # Añadir elementos al header
        self.header_box.pack_start(self.doc_icon, False, False, 0)
        self.header_box.pack_start(self.info_box, True, True, 0)
        self.header_box.pack_end(self.view_mode_button, False, False, 0)
        
        # Separador después del header
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        
        # Contenedor para el visor de documentos (se definirá según el tipo)
        self.viewer_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.viewer_container.set_name("viewer-container")
        self.viewer_container.set_hexpand(True)
        self.viewer_container.set_vexpand(True)
        
        # Añadir todo al contenedor principal
        self.main_box.pack_start(self.header_box, False, False, 0)
        self.main_box.pack_start(separator, False, False, 0)
        self.main_box.pack_start(self.viewer_container, True, True, 0)
        
        # Añadir el contenedor principal a este widget
        self.pack_start(self.main_box, True, True, 0)
        
        # Mostrar todos los widgets
        self.show_all()
    
    def load_document(self, document):
        """Carga un documento en el visor"""
        self.document = document
        if not document:
            return
        
        # Actualizar información del documento
        self.title_label.set_text(document.get('name', 'Documento sin nombre'))
        
        # Determinar tipo de archivo
        file_type = document.get('file_type', '').lower()
        self.type_label.set_text(f"Tipo: {file_type.upper()}")
        
        # Obtener icono apropiado
        if self.parent_window:
            icon_name = self.parent_window.get_icon_for_file_type(file_type)
            self.doc_icon.set_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        
        # Limpiar el contenedor del visor
        for child in self.viewer_container.get_children():
            self.viewer_container.remove(child)
        
        # Configurar el visor según el tipo de archivo
        content = document.get('content', '')
        
        # Verificar si es un archivo HTML
        self.is_html = file_type == 'html'
        if self.is_html:
            self.view_mode_button.set_visible(True)
            self.setup_html_viewer(content)
        else:
            self.view_mode_button.set_visible(False)
            self.setup_text_viewer(content, file_type)
        
        # Mostrar todos los widgets
        self.show_all()
    
    def setup_text_viewer(self, content, file_type):
        """Configura un visor de texto para documentos no HTML"""
        # Crear ScrolledWindow para el texto
        scroll = Gtk.ScrolledWindow()
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)
        
        # Determinar si debemos usar un visor de código fuente
        code_types = ['py', 'js', 'html', 'css', 'c', 'cpp', 'java', 'xml', 'json']
        
        if file_type in code_types:
            # Usar GtkSourceView para documentos de código
            try:
                buffer = GtkSource.Buffer()
                buffer.set_text(content)
                
                # Intentar configurar el resaltado de sintaxis
                lang_manager = GtkSource.LanguageManager.get_default()
                language = lang_manager.guess_language(f"file.{file_type}", None)
                if language:
                    buffer.set_language(language)
                
                # Habilitar el resaltado de sintaxis
                buffer.set_highlight_syntax(True)
                
                # Crear el visor
                source_view = GtkSource.View.new_with_buffer(buffer)
                source_view.set_show_line_numbers(True)
                source_view.set_highlight_current_line(True)
                source_view.set_auto_indent(True)
                source_view.set_insert_spaces_instead_of_tabs(True)
                source_view.set_tab_width(4)
                source_view.set_editable(False)  # Solo lectura
                source_view.override_font(Pango.FontDescription("Monospace 10"))
                
                scroll.add(source_view)
            except:
                # Fallback a TextView si hay error
                buffer = Gtk.TextBuffer()
                buffer.set_text(content)
                text_view = Gtk.TextView.new_with_buffer(buffer)
                text_view.set_editable(False)  # Solo lectura
                text_view.override_font(Pango.FontDescription("Monospace 10"))
                scroll.add(text_view)
        else:
            # Usar TextView para documentos de texto plano
            buffer = Gtk.TextBuffer()
            buffer.set_text(content)
            text_view = Gtk.TextView.new_with_buffer(buffer)
            text_view.set_editable(False)  # Solo lectura
            text_view.set_wrap_mode(Gtk.WrapMode.WORD)
            scroll.add(text_view)
        
        self.viewer_container.pack_start(scroll, True, True, 0)
    
    def setup_html_viewer(self, content):
        """Configura un visor para documentos HTML según el modo de vista"""
        if self.view_mode == "normal":
            # Vista normal (renderizar HTML)
            webview = WebKit2.WebView()
            webview.load_html(content, "file:///")
            
            # Contenedor para el WebView
            web_scroll = Gtk.ScrolledWindow()
            web_scroll.set_hexpand(True)
            web_scroll.set_vexpand(True)
            web_scroll.add(webview)
            
            self.viewer_container.pack_start(web_scroll, True, True, 0)
        else:
            # Vista de código
            self.setup_text_viewer(content, 'html')
    
    def toggle_view_mode(self, button):
        """Alterna entre vista normal y vista de código para HTML"""
        if not self.is_html or not self.document:
            return
        
        if self.view_mode == "normal":
            self.view_mode = "code"
            button.set_tooltip_text("Ver HTML renderizado")
        else:
            self.view_mode = "normal"
            button.set_tooltip_text("Ver código HTML")
        
        # Recargar el documento con el nuevo modo
        content = self.document.get('content', '')
        
        # Limpiar el contenedor del visor
        for child in self.viewer_container.get_children():
            self.viewer_container.remove(child)
        
        # Configurar el visor con el nuevo modo
        self.setup_html_viewer(content)
        
        # Mostrar todos los widgets
        self.show_all()
    
    def load_module(self, parent_container):
        """Método para cargar este módulo en el contenedor principal"""
        if parent_container is not None:
            # Limpiar el contenedor
            for child in parent_container.get_children():
                parent_container.remove(child)
            
            # Añadir este módulo
            parent_container.add(self)
            parent_container.show_all()
