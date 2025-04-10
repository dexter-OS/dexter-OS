#!/usr/bin/env python3

"""
Dexter Organizer - Módulo de edición de documentos
Author: Victor Oubiña Faubel - oubinav78@gmail.com
Website: https://sourceforge.net/projects/dexter-gnome/
"""

import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2

class DexterEditor:
    def __init__(self, app):
        """
        Inicializa el editor de documentos.
        
        Args:
            app: Instancia principal de la aplicación DexterOrganizer
        """
        self.app = app
        
        # Referencia a los widgets principales
        self.window = app.window
        self.content_panel = app.content_panel
        self.documents_path = app.file_manager.documents_path
        
        # Crear Stack para manejar diferentes vistas del documento
        self.document_view_stack = Gtk.Stack()
        self.document_view_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        
        # Vista de texto
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.get_style_context().add_class("document-text-view")
        self.text_buffer = self.text_view.get_buffer()
        
        text_scroll = Gtk.ScrolledWindow()
        text_scroll.add(self.text_view)
        
        # Vista web para HTML
        self.web_view = WebKit2.WebView()
        web_scroll = Gtk.ScrolledWindow()
        web_scroll.add(self.web_view)
        
        self.document_view_stack.add_named(text_scroll, "text")
        self.document_view_stack.add_named(web_scroll, "web")
        
        # Contenedor para los documentos con barra de herramientas
        self.document_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Barra de herramientas de documento
        self.doc_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.doc_toolbar.get_style_context().add_class("doc-toolbar")
        
        self.view_mode_button = Gtk.Button(label="Vista Web")
        self.view_mode_button.connect("clicked", self.toggle_view_mode)
        self.view_mode_button.set_sensitive(False)
        self.view_mode_button.get_style_context().add_class("view-mode-button")
        
        self.save_button = Gtk.Button(label="Guardar")
        self.save_button.connect("clicked", self.on_save_document)
        self.save_button.get_style_context().add_class("save-button")
        
        self.doc_toolbar.pack_start(self.view_mode_button, False, False, 0)
        self.doc_toolbar.pack_end(self.save_button, False, False, 0)
        
        self.document_container.pack_start(self.doc_toolbar, False, False, 0)
        self.document_container.pack_start(self.document_view_stack, True, True, 0)
        
        # Estado inicial
        self.save_button.set_visible(False)
        self.doc_toolbar.set_visible(False)
        self.edit_mode = False

    def toggle_view_mode(self, button):
        """Alterna entre la vista de texto y web para documentos HTML"""
        current_mode = self.document_view_stack.get_visible_child_name()
        
        if current_mode == "text":
            self.document_view_stack.set_visible_child_name("web")
            button.set_label("Vista Código")
        else:
            self.document_view_stack.set_visible_child_name("text")
            button.set_label("Vista Web")
    
    def show_document(self, category_name, doc_id):
        """
        Muestra un documento en el área principal
        
        Args:
            category_name: Nombre de la categoría
            doc_id: ID del documento
        """
        print(f"Editor: Mostrando documento {category_name}/{doc_id}")
        
        # Obtener información del documento
        doc_info = self.app.categories[category_name][doc_id]
        doc_path = os.path.join(self.documents_path, doc_id)
        
        # Leer el contenido del documento
        try:
            with open(doc_path, 'r') as f:
                content = f.read()
            print(f"Contenido del documento cargado: {len(content)} caracteres")
        except Exception as e:
            print(f"Error al leer el documento: {e}")
            content = ""
        
        # Configurar el área de texto con el contenido
        self.text_buffer.set_text(content)
        self.text_view.set_editable(False)
    
        # Configurar el botón de modo de vista para HTML
        is_html = doc_info['type'] == 'html'
        self.view_mode_button.set_sensitive(is_html)
    
        # Mostrar en modo texto por defecto
        self.document_view_stack.set_visible_child_name("text")
    
        # Si es HTML, también cargar en webview
        if is_html:
            self.web_view.load_html(content, None)
        
        # Desactivar modo edición
        self.edit_mode = False
    
        # Mostrar la barra de herramientas del documento
        self.doc_toolbar.set_visible(True)
    
        # Botón guardar no visible en modo lectura
        self.save_button.set_visible(False)
        
        # Añadir y mostrar el contenedor de documento
        if self.content_panel.get_child_by_name("document_view"):
            # Necesitamos remover y volver a añadir para forzar la actualización
            self.content_panel.remove(self.content_panel.get_child_by_name("document_view"))
    
        self.content_panel.add_named(self.document_container, "document_view")
        self.content_panel.set_visible_child_name("document_view")
    
        # Forzar actualización de la interfaz
        self.document_container.show_all()
        self.content_panel.show_all()
        
        # Procesamiento de eventos pendientes para asegurar que la interfaz se actualiza
        i = 0
        while Gtk.events_pending() and i < 10:
            Gtk.main_iteration()
            i += 1
    
        # Mantener el botón guardar oculto después de show_all
        self.save_button.set_visible(False)
    
        # Forzar actualización final
        self.window.queue_draw()
    
        print("Documento mostrado en el contenedor")
        return True
    
    def enable_edit_mode(self):
        """Activa el modo de edición para el documento actual"""
        if not self.app.current_document or not self.app.current_category:
            print("No hay documento seleccionado para editar")
            return False
            
        print(f"Activando modo edición para: {self.app.current_category}/{self.app.current_document}")
        
        # Asegurarse de que estamos viendo el documento correcto
        if self.content_panel.get_visible_child_name() != "document_view":
            self.show_document(self.app.current_category, self.app.current_document)
        
            # Procesar eventos pendientes después de mostrar el documento
            while Gtk.events_pending():
                Gtk.main_iteration()
        
        # Activar modo edición
        self.edit_mode = True
        self.text_view.set_editable(True)
    
        # Asegurarse de que estamos en modo texto (no web)
        self.document_view_stack.set_visible_child_name("text")
        
        # Mostrar botón guardar
        self.save_button.set_visible(True)
        self.save_button.set_sensitive(True)
    
        # Forzar actualización de la interfaz
        self.window.show_all()
    
        # Mantener el botón guardar visible después de show_all
        self.save_button.set_visible(True)
    
        # Dar foco al área de texto
        self.text_view.grab_focus()
    
        # Procesar eventos pendientes finales
        while Gtk.events_pending():
            Gtk.main_iteration()
    
        return True
    
    def on_save_document(self, button):
        """Guarda el documento actual"""
        if not self.app.current_document or not self.app.current_category:
            return
            
        print(f"Guardando documento: {self.app.current_category}/{self.app.current_document}")
        
        # Obtener contenido actualizado
        start, end = self.text_buffer.get_bounds()
        content = self.text_buffer.get_text(start, end, True)
        
        # Guardar contenido
        doc_path = os.path.join(self.documents_path, self.app.current_document)
        try:
            with open(doc_path, 'w') as f:
                f.write(content)
            print(f"Documento guardado: {len(content)} caracteres")
            
            # Si es HTML, actualizar la vista web
            doc_info = self.app.categories[self.app.current_category][self.app.current_document]
            if doc_info['type'] == 'html':
                self.web_view.load_html(content, None)
            
            # Volver a modo lectura
            self.edit_mode = False
            self.text_view.set_editable(False)
            
            # Ocultar botón guardar
            self.save_button.set_visible(False)
            
            # Mostrar mensaje de éxito
            self.app.show_success_dialog("Documento guardado correctamente")
            
        except Exception as e:
            print(f"Error al guardar: {e}")
            self.app.show_error_dialog(f"Error al guardar: {e}")
