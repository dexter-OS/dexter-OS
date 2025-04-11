#!/usr/bin/env python3
import gi
import os
import json
import datetime
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk, Pango

class Editor:
    def __init__(self, parent_window, document=None, on_save_callback=None):
        self.parent = parent_window
        self.document = document
        self.on_save_callback = on_save_callback
        self.data_path = os.path.expanduser("~/.local/share/dexter-organizer")
        self.categories_file = os.path.join(self.data_path, "categories.json")
        
        # Contenedor principal
        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.container.set_margin_top(20)
        self.container.set_margin_bottom(20)
        self.container.set_margin_start(20)
        self.container.set_margin_end(20)
        
        # Título
        if document:
            title = Gtk.Label(label=f"<b>Editando: {document['name']}{document['extension']}</b>")
        else:
            title = Gtk.Label(label="<b>Nuevo Documento</b>")
        title.set_use_markup(True)
        title.set_halign(Gtk.Align.START)
        self.container.append(title)
        
        # Información del documento
        if document:
            # Buscar el nombre de la categoría
            category_name = "Sin categoría"
            try:
                with open(self.categories_file, 'r') as f:
                    categories = json.load(f)
                    for category in categories:
                        if category["id"] == document["category_id"]:
                            category_name = category["name"]
                            break
            except (FileNotFoundError, json.JSONDecodeError):
                pass
                
            info = Gtk.Label(label=f"<i>Categoría: {category_name} | Última modificación: {document.get('date_modified', 'Desconocida')}</i>")
            info.set_use_markup(True)
            info.set_halign(Gtk.Align.START)
            self.container.append(info)
        
        # Editor de texto
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Configurar fuente monoespaciada para código
        font_desc = Pango.FontDescription("Monospace 10")
        self.text_view.override_font(font_desc)
        
        # Establecer el contenido si existe
        if document:
            buffer = self.text_view.get_buffer()
            buffer.set_text(document["content"])
        
        scrolled_window.set_child(self.text_view)
        self.container.append(scrolled_window)
        
        # Botones de acción
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_box.set_halign(Gtk.Align.END)
        action_box.set_margin_top(10)
        
        cancel_button = Gtk.Button(label="Cancelar")
        cancel_button.connect("clicked", self.on_cancel)
        
        save_button = Gtk.Button(label="Guardar")
        save_button.connect("clicked", self.on_save)
        save_button.add_css_class("suggested-action")
        
        action_box.append(cancel_button)
        action_box.append(save_button)
        
        self.container.append(action_box)
        
        # Configuración de atajos de teclado
        self.setup_shortcuts()
        
    def get_container(self):
        return self.container
        
    def setup_shortcuts(self):
        # Crear acciones para los atajos de teclado
        action = Gio.SimpleAction.new("save", None)
        action.connect("activate", self.on_save)
        self.parent.add_action(action)
        
        # Ctrl+S para guardar
        self.parent.set_accels_for_action("win.save", ["<Control>s"])
        
    def on_cancel(self, button):
        # Mostrar diálogo de confirmación si hay cambios
        buffer = self.text_view.get_buffer()
        start, end = buffer.get_bounds()
        current_content = buffer.get_text(start, end, False)
        
        if self.document and current_content != self.document["content"]:
            dialog = Gtk.Dialog(title="Confirmar Cancelar", 
                               transient_for=self.parent,
                               modal=True)
            
            dialog.add_button("Descartar Cambios", Gtk.ResponseType.OK)
            dialog.add_button("Continuar Editando", Gtk.ResponseType.CANCEL)
            
            content_area = dialog.get_content_area()
            content_area.set_margin_top(10)
            content_area.set_margin_bottom(10)
            content_area.set_margin_start(10)
            content_area.set_margin_end(10)
            
            label = Gtk.Label(label="Hay cambios sin guardar. ¿Estás seguro de que deseas descartarlos?")
            content_area.append(label)
            
            dialog.set_default_response(Gtk.ResponseType.CANCEL)
            dialog.show()
            
            response = dialog.run()
            dialog.destroy()
            
            if response != Gtk.ResponseType.OK:
                return
        
        # Volver a la vista de documentos
        if self.on_save_callback:
            self.on_save_callback(None)
        
    def on_save(self, *args):
        buffer = self.text_view.get_buffer()
        start, end = buffer.get_bounds()
        content = buffer.get_text(start, end, False)
        
        if not content.strip():
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="El documento está vacío"
            )
            dialog.format_secondary_text("Por favor, añade algún contenido antes de guardar.")
            dialog.run()
            dialog.destroy()
            return
        
        # Si es un documento existente, actualizarlo
        if self.document:
            self.document["content"] = content
            self.document["date_modified"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if self.on_save_callback:
                self.on_save_callback(self.document)
        # Si es un documento nuevo, mostrar diálogo para nombre y categoría
        else:
            self.show_new_document_dialog(content)
    
    def show_new_document_dialog(self, content):
        # Verificar si hay categorías
        try:
            with open(self.categories_file, 'r') as f:
                categories = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            categories = []
            
        if not categories:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="No hay categorías disponibles"
            )
            dialog.format_secondary_text("Debes crear al menos una categoría antes de guardar documentos.")
            dialog.run()
            dialog.destroy()
            return
            
        dialog = Gtk.Dialog(title="Guardar Documento", 
                           transient_for=self.parent,
                           modal=True)
        
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Guardar", Gtk.ResponseType.OK)
        
        content_area = dialog.get_content_area()
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_start(10)
        content_area.set_margin_end(10)
        content_area.set_spacing(10)
        
        # Nombre del documento
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        name_label = Gtk.Label(label="Nombre:")
        name_label.set_width_chars(10)
        name_entry = Gtk.Entry()
        name_entry.set_hexpand(True)
        name_box.append(name_label)
        name_box.append(name_entry)
        content_area.append(name_box)
        
        # Extensión del documento
        ext_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ext_label = Gtk.Label(label="Extensión:")
        ext_label.set_width_chars(10)
        ext_combo = Gtk.ComboBoxText()
        for ext in [".txt", ".md", ".html", ".py", ".sh"]:
            ext_combo.append_text(ext)
        ext_combo.set_active(0)
        ext_box.append(ext_label)
        ext_box.append(ext_combo)
        content_area.append(ext_box)
        
        # Categoría
        cat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cat_label = Gtk.Label(label="Categoría:")
        cat_label.set_width_chars(10)
        cat_combo = Gtk.ComboBoxText()
        
        for category in categories:
            cat_combo.append_text(category["name"])
        cat_combo.set_active(0)
        
        cat_box.append(cat_label)
        cat_box.append(cat_combo)
        content_area.append(cat_box)
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            document_name = name_entry.get_text().strip()
            document_ext = ext_combo.get_active_text()
            category_index = cat_combo.get_active()
            
            if document_name and category_index >= 0:
                category_id = categories[category_index]["id"]
                
                # Cargar documentos existentes para obtener un nuevo ID
                documents_file = os.path.join(self.data_path, "documents.json")
                try:
                    with open(documents_file, 'r') as f:
                        documents = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    documents = []
                    
                new_id = 1
                if documents:
                    new_id = max(d["id"] for d in documents) + 1
                    
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                new_document = {
                    "id": new_id,
                    "name": document_name,
                    "extension": document_ext,
                    "category_id": category_id,
                    "content": content,
                    "date_created": now,
                    "date_modified": now
                }
                
                if self.on_save_callback:
                    self.on_save_callback(new_document)
                
        dialog.destroy()
        
    def get_content(self):
        buffer = self.text_view.get_buffer()
        start, end = buffer.get_bounds()
        return buffer.get_text(start, end, False)
