#!/usr/bin/env python3
import gi
import os
import json
import datetime
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk, Gio

class DocumentManager:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.data_path = os.path.expanduser("~/.local/share/dexter-organizer")
        self.documents_file = os.path.join(self.data_path, "documents.json")
        self.categories_file = os.path.join(self.data_path, "categories.json")
        
        # Contenedor principal
        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.container.set_margin_top(20)
        self.container.set_margin_bottom(20)
        self.container.set_margin_start(20)
        self.container.set_margin_end(20)
        
        # Título
        title = Gtk.Label(label="<b>Documentos</b>")
        title.set_use_markup(True)
        title.set_halign(Gtk.Align.START)
        self.container.append(title)
        
        # Área de documentos
        self.documents_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.container.append(self.documents_box)
        
        # Botones de acción
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_box.set_halign(Gtk.Align.CENTER)
        
        self.add_button = Gtk.Button(label="Añadir Documento")
        self.add_button.connect("clicked", self.on_add_document)
        
        self.edit_button = Gtk.Button(label="Editar Documento")
        self.edit_button.connect("clicked", self.on_edit_document)
        self.edit_button.set_sensitive(False)
        
        self.delete_button = Gtk.Button(label="Eliminar Documento")
        self.delete_button.connect("clicked", self.on_delete_document)
        self.delete_button.set_sensitive(False)
        
        action_box.append(self.add_button)
        action_box.append(self.edit_button)
        action_box.append(self.delete_button)
        
        self.container.append(action_box)
        
        # Área de visualización de documento
        self.document_view_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.document_view_box.set_margin_top(20)
        
        self.document_title = Gtk.Label()
        self.document_title.set_halign(Gtk.Align.START)
        
        self.document_info = Gtk.Label()
        self.document_info.set_halign(Gtk.Align.START)
        
        self.document_content = Gtk.TextView()
        self.document_content.set_editable(False)
        self.document_content.set_wrap_mode(Gtk.WrapMode.WORD)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_child(self.document_content)
        
        self.html_view_button = Gtk.Button(label="Ver como HTML")
        self.html_view_button.connect("clicked", self.toggle_html_view)
        self.html_view_button.set_visible(False)
        
        self.document_view_box.append(self.document_title)
        self.document_view_box.append(self.document_info)
        self.document_view_box.append(self.html_view_button)
        self.document_view_box.append(scrolled_window)
        
        self.container.append(self.document_view_box)
        self.document_view_box.set_visible(False)
        
        # Cargar documentos
        self.documents = []
        self.categories = []
        self.selected_document = None
        self.html_view_mode = False
        self.load_documents()
        
    def get_container(self):
        return self.container
        
    def load_categories(self):
        try:
            with open(self.categories_file, 'r') as f:
                self.categories = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.categories = []
            
    def load_documents(self):
        # Limpiar el contenedor de documentos
        for child in self.documents_box:
            self.documents_box.remove(child)
            
        # Cargar categorías
        self.load_categories()
            
        # Cargar documentos desde el archivo JSON
        try:
            with open(self.documents_file, 'r') as f:
                documents_data = json.load(f)
                
                # Convertir el formato actual al formato esperado
                self.documents = []
                
                # Verificar si es el formato nuevo (diccionario con categorías como claves)
                if isinstance(documents_data, dict):
                    for category_id, docs in documents_data.items():
                        if isinstance(docs, list):
                            for doc in docs:
                                if isinstance(doc, dict) and "id" in doc and "name" in doc:
                                    # Convertir al formato esperado
                                    new_doc = {
                                        "id": doc["id"],
                                        "name": doc["name"].split(".")[0] if "." in doc["name"] else doc["name"],
                                        "extension": f".{doc['type']}" if "type" in doc else ".txt",
                                        "content": doc.get("content", ""),
                                        "category_id": category_id,
                                        "date_created": doc.get("date_created", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                        "date_modified": doc.get("date_modified", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                    }
                                    self.documents.append(new_doc)
                # Si es el formato antiguo (lista de documentos)
                elif isinstance(documents_data, list):
                    for doc in documents_data:
                        if isinstance(doc, dict) and "id" in doc and "name" in doc and "extension" in doc:
                            self.documents.append(doc)
                
                print(f"Documentos cargados: {len(self.documents)}")
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error al cargar documentos: {e}")
            self.documents = []
            # Crear un archivo vacío con el formato esperado
            with open(self.documents_file, 'w') as f:
                json.dump([], f)
        
        # Crear lista de documentos
        if not self.documents:
            no_documents = Gtk.Label(label="No hay documentos. Añade un nuevo documento.")
            no_documents.set_halign(Gtk.Align.CENTER)
            self.documents_box.append(no_documents)
        else:
            list_box = Gtk.ListBox()
            list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
            list_box.connect("row-selected", self.on_document_selected)
            
            for document in self.documents:
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                box.set_margin_top(5)
                box.set_margin_bottom(5)
                box.set_margin_start(5)
                box.set_margin_end(5)
                
                # Icono según extensión
                icon_name = "text-x-generic"
                try:
                    if isinstance(document, dict) and "extension" in document:
                        if document["extension"] == ".txt":
                            icon_name = "text-x-generic"
                        elif document["extension"] == ".md":
                            icon_name = "text-markdown"
                        elif document["extension"] == ".html":
                            icon_name = "text-html"
                        elif document["extension"] == ".py":
                            icon_name = "text-x-python"
                        elif document["extension"] == ".sh":
                            icon_name = "text-x-script"
                except Exception as e:
                    print(f"Error al procesar documento: {e}")
                    print(f"Documento: {document}")
                
                icon = Gtk.Image.new_from_icon_name(icon_name)
                box.append(icon)
                
                # Nombre del documento
                try:
                    if isinstance(document, dict) and "name" in document and "extension" in document:
                        label = Gtk.Label(label=document["name"] + document["extension"])
                    else:
                        label = Gtk.Label(label="Documento sin nombre")
                        print(f"Documento con formato incorrecto: {document}")
                except Exception as e:
                    label = Gtk.Label(label="Error en documento")
                    print(f"Error al mostrar nombre del documento: {e}")
                
                label.set_halign(Gtk.Align.START)
                box.append(label)
                
                row.set_child(box)
                try:
                    if isinstance(document, dict) and "id" in document:
                        # Usar un atributo en lugar de set_data
                        row.document_id = document["id"]
                    else:
                        # Asignar un ID temporal
                        row.document_id = "error_id"
                except Exception as e:
                    print(f"Error al asignar ID al documento: {e}")
                    row.document_id = "error_id"
                
                list_box.append(row)
                
            self.documents_box.append(list_box)
            
    def on_document_selected(self, list_box, row):
        if row is not None:
            # Usar el atributo en lugar de get_data
            document_id = getattr(row, 'document_id', None)
            self.selected_document = next((d for d in self.documents if d["id"] == document_id), None)
            
            if self.selected_document:
                self.edit_button.set_sensitive(True)
                self.delete_button.set_sensitive(True)
                
                # Mostrar el documento
                self.document_title.set_markup(f"<b>{self.selected_document['name']}{self.selected_document['extension']}</b>")
                
                # Buscar el nombre de la categoría
                category_name = "Sin categoría"
                for category in self.categories:
                    if category["id"] == self.selected_document["category_id"]:
                        category_name = category["name"]
                        break
                
                # Formatear la fecha
                date_str = self.selected_document.get("date_modified", "Desconocida")
                
                self.document_info.set_markup(f"<i>Categoría: {category_name} | Última modificación: {date_str}</i>")
                
                # Mostrar el contenido
                buffer = self.document_content.get_buffer()
                buffer.set_text(self.selected_document["content"])
                
                # Mostrar u ocultar el botón de HTML
                self.html_view_mode = False
                if self.selected_document["extension"] == ".html":
                    self.html_view_button.set_visible(True)
                    self.html_view_button.set_label("Ver como HTML")
                else:
                    self.html_view_button.set_visible(False)
                
                self.document_view_box.set_visible(True)
            else:
                self.document_view_box.set_visible(False)
        else:
            self.selected_document = None
            self.edit_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)
            self.document_view_box.set_visible(False)
            
    def toggle_html_view(self, button):
        if not self.selected_document or self.selected_document["extension"] != ".html":
            return
            
        self.html_view_mode = not self.html_view_mode
        
        if self.html_view_mode:
            # Mostrar como HTML
            button.set_label("Ver como código")
            
            # Crear un WebView para mostrar el HTML
            try:
                gi.require_version('WebKit', '6.0')
                from gi.repository import WebKit
                
                # Eliminar el TextView
                for child in self.document_view_box:
                    if isinstance(child, Gtk.ScrolledWindow):
                        self.document_view_box.remove(child)
                        break
                
                # Crear WebView
                web_view = WebKit.WebView()
                web_view.load_html(self.selected_document["content"], None)
                
                scrolled_window = Gtk.ScrolledWindow()
                scrolled_window.set_vexpand(True)
                scrolled_window.set_child(web_view)
                
                self.document_view_box.append(scrolled_window)
            except (ImportError, ValueError):
                # Si WebKit no está disponible, mostrar un mensaje
                dialog = Gtk.MessageDialog(
                    transient_for=self.parent,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="No se puede mostrar HTML"
                )
                dialog.format_secondary_text("WebKit no está disponible en el sistema.")
                dialog.run()
                dialog.destroy()
                
                button.set_label("Ver como HTML")
                self.html_view_mode = False
        else:
            # Mostrar como código
            button.set_label("Ver como HTML")
            
            # Eliminar el WebView
            for child in self.document_view_box:
                if isinstance(child, Gtk.ScrolledWindow):
                    self.document_view_box.remove(child)
                    break
            
            # Restaurar el TextView
            self.document_content = Gtk.TextView()
            self.document_content.set_editable(False)
            self.document_content.set_wrap_mode(Gtk.WrapMode.WORD)
            
            buffer = self.document_content.get_buffer()
            buffer.set_text(self.selected_document["content"])
            
            scrolled_window = Gtk.ScrolledWindow()
            scrolled_window.set_vexpand(True)
            scrolled_window.set_child(self.document_content)
            
            self.document_view_box.append(scrolled_window)
            
    def on_add_document(self, button):
        # Verificar si hay categorías
        if not self.categories:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="No hay categorías disponibles"
            )
            dialog.format_secondary_text("Debes crear al menos una categoría antes de añadir documentos.")
            dialog.run()
            dialog.destroy()
            return
            
        dialog = Gtk.Dialog(title="Añadir Documento", 
                           transient_for=self.parent,
                           modal=True)
        
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Añadir", Gtk.ResponseType.OK)
        
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
        
        for category in self.categories:
            cat_combo.append_text(category["name"])
        cat_combo.set_active(0)
        
        cat_box.append(cat_label)
        cat_box.append(cat_combo)
        content_area.append(cat_box)
        
        # Contenido
        content_label = Gtk.Label(label="Contenido:")
        content_label.set_halign(Gtk.Align.START)
        content_area.append(content_label)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_min_content_height(200)
        
        content_text = Gtk.TextView()
        content_text.set_wrap_mode(Gtk.WrapMode.WORD)
        
        scrolled_window.set_child(content_text)
        content_area.append(scrolled_window)
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            document_name = name_entry.get_text().strip()
            document_ext = ext_combo.get_active_text()
            category_index = cat_combo.get_active()
            
            if document_name and category_index >= 0:
                category_id = self.categories[category_index]["id"]
                
                buffer = content_text.get_buffer()
                start, end = buffer.get_bounds()
                document_content = buffer.get_text(start, end, False)
                
                new_id = 1
                if self.documents:
                    new_id = max(d["id"] for d in self.documents) + 1
                    
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                new_document = {
                    "id": new_id,
                    "name": document_name,
                    "extension": document_ext,
                    "category_id": category_id,
                    "content": document_content,
                    "date_created": now,
                    "date_modified": now
                }
                
                self.documents.append(new_document)
                self.save_documents()
                self.load_documents()
                
        dialog.destroy()
        
    def on_edit_document(self, button):
        if self.selected_document is None:
            return
            
        dialog = Gtk.Dialog(title="Editar Documento", 
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
        name_entry.set_text(self.selected_document["name"])
        name_entry.set_hexpand(True)
        name_box.append(name_label)
        name_box.append(name_entry)
        content_area.append(name_box)
        
        # Categoría
        cat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cat_label = Gtk.Label(label="Categoría:")
        cat_label.set_width_chars(10)
        cat_combo = Gtk.ComboBoxText()
        
        selected_index = 0
        for i, category in enumerate(self.categories):
            cat_combo.append_text(category["name"])
            if category["id"] == self.selected_document["category_id"]:
                selected_index = i
        
        cat_combo.set_active(selected_index)
        
        cat_box.append(cat_label)
        cat_box.append(cat_combo)
        content_area.append(cat_box)
        
        # Contenido
        content_label = Gtk.Label(label="Contenido:")
        content_label.set_halign(Gtk.Align.START)
        content_area.append(content_label)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_min_content_height(200)
        
        content_text = Gtk.TextView()
        content_text.set_wrap_mode(Gtk.WrapMode.WORD)
        
        buffer = content_text.get_buffer()
        buffer.set_text(self.selected_document["content"])
        
        scrolled_window.set_child(content_text)
        content_area.append(scrolled_window)
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            document_name = name_entry.get_text().strip()
            category_index = cat_combo.get_active()
            
            if document_name and category_index >= 0:
                category_id = self.categories[category_index]["id"]
                
                buffer = content_text.get_buffer()
                start, end = buffer.get_bounds()
                document_content = buffer.get_text(start, end, False)
                
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                for document in self.documents:
                    if document["id"] == self.selected_document["id"]:
                        document["name"] = document_name
                        document["category_id"] = category_id
                        document["content"] = document_content
                        document["date_modified"] = now
                        break
                        
                self.save_documents()
                self.load_documents()
                
                # Actualizar la vista del documento
                self.document_view_box.set_visible(False)
                self.selected_document = None
                
        dialog.destroy()
        
    def on_delete_document(self, button):
        if self.selected_document is None:
            return
            
        dialog = Gtk.Dialog(title="Eliminar Documento", 
                           transient_for=self.parent,
                           modal=True)
        
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Eliminar", Gtk.ResponseType.OK)
        
        content_area = dialog.get_content_area()
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_start(10)
        content_area.set_margin_end(10)
        content_area.set_spacing(10)
        
        label = Gtk.Label(label=f"¿Estás seguro de que deseas eliminar el documento '{self.selected_document['name']}{self.selected_document['extension']}'?")
        content_area.append(label)
        
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        dialog.show()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.documents = [d for d in self.documents if d["id"] != self.selected_document["id"]]
            self.save_documents()
            self.load_documents()
            
            self.selected_document = None
            self.edit_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)
            self.document_view_box.set_visible(False)
                
        dialog.destroy()
        
    def save_documents(self):
        with open(self.documents_file, 'w') as f:
            json.dump(self.documents, f)
            
    def get_documents(self):
        return self.documents
