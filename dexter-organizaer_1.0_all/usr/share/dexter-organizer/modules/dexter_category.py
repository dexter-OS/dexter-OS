#!/usr/bin/env python3
import gi
import os
import json
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

class CategoryManager:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.data_path = os.path.expanduser("~/.local/share/dexter-organizer")
        self.categories_file = os.path.join(self.data_path, "categories.json")
        
        # Contenedor principal
        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.container.set_margin_top(20)
        self.container.set_margin_bottom(20)
        self.container.set_margin_start(20)
        self.container.set_margin_end(20)
        
        # Título
        title = Gtk.Label(label="<b>Gestión de Categorías</b>")
        title.set_use_markup(True)
        title.set_halign(Gtk.Align.START)
        self.container.append(title)
        
        # Área de categorías
        self.categories_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.container.append(self.categories_box)
        
        # Botones de acción
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_box.set_halign(Gtk.Align.CENTER)
        
        self.add_button = Gtk.Button(label="Añadir Categoría")
        self.add_button.connect("clicked", self.on_add_category)
        
        self.edit_button = Gtk.Button(label="Editar Categoría")
        self.edit_button.connect("clicked", self.on_edit_category)
        self.edit_button.set_sensitive(False)
        
        self.delete_button = Gtk.Button(label="Eliminar Categoría")
        self.delete_button.connect("clicked", self.on_delete_category)
        self.delete_button.set_sensitive(False)
        
        action_box.append(self.add_button)
        action_box.append(self.edit_button)
        action_box.append(self.delete_button)
        
        self.container.append(action_box)
        
        # Cargar categorías
        self.categories = []
        self.selected_category = None
        self.load_categories()
        
    def get_container(self):
        return self.container
        
    def load_categories(self):
        # Limpiar el contenedor de categorías
        for child in self.categories_box:
            self.categories_box.remove(child)
            
        # Cargar categorías desde el archivo JSON
        try:
            with open(self.categories_file, 'r') as f:
                self.categories = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.categories = []
            with open(self.categories_file, 'w') as f:
                json.dump(self.categories, f)
                
        # Crear lista de categorías
        if not self.categories:
            no_categories = Gtk.Label(label="No hay categorías. Añade una nueva categoría.")
            no_categories.set_halign(Gtk.Align.CENTER)
            self.categories_box.append(no_categories)
        else:
            list_box = Gtk.ListBox()
            list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
            list_box.connect("row-selected", self.on_category_selected)
            
            for category in self.categories:
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                box.set_margin_top(5)
                box.set_margin_bottom(5)
                box.set_margin_start(5)
                box.set_margin_end(5)
                
                label = Gtk.Label(label=category["name"])
                label.set_halign(Gtk.Align.START)
                box.append(label)
                
                row.set_child(box)
                # Usar atributo normal de Python en lugar de set_data
                setattr(row, 'category_id', category["id"])
                list_box.append(row)
                
            self.categories_box.append(list_box)
            
    def on_category_selected(self, list_box, row):
        if row is not None:
            # Usar atributo normal de Python en lugar de get_data
            category_id = getattr(row, 'category_id', None)
            self.selected_category = next((c for c in self.categories if c["id"] == category_id), None)
            self.edit_button.set_sensitive(True)
            self.delete_button.set_sensitive(True)
        else:
            self.selected_category = None
            self.edit_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)
            
    def on_add_category(self, button):
        dialog = Gtk.Dialog(title="Añadir Categoría", 
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
        
        label = Gtk.Label(label="Nombre de la categoría:")
        content_area.append(label)
        
        entry = Gtk.Entry()
        entry.set_activates_default(True)
        content_area.append(entry)
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            category_name = entry.get_text().strip()
            if category_name:
                new_id = 1
                if self.categories:
                    new_id = max(c["id"] for c in self.categories) + 1
                    
                new_category = {
                    "id": new_id,
                    "name": category_name
                }
                
                self.categories.append(new_category)
                self.save_categories()
                self.load_categories()
                
        dialog.destroy()
        
    def on_edit_category(self, button):
        if self.selected_category is None:
            return
            
        dialog = Gtk.Dialog(title="Editar Categoría", 
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
        
        label = Gtk.Label(label="Nombre de la categoría:")
        content_area.append(label)
        
        entry = Gtk.Entry()
        entry.set_text(self.selected_category["name"])
        entry.set_activates_default(True)
        content_area.append(entry)
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.show()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            category_name = entry.get_text().strip()
            if category_name:
                for category in self.categories:
                    if category["id"] == self.selected_category["id"]:
                        category["name"] = category_name
                        break
                        
                self.save_categories()
                self.load_categories()
                
        dialog.destroy()
        
    def on_delete_category(self, button):
        if self.selected_category is None:
            return
            
        dialog = Gtk.Dialog(title="Eliminar Categoría", 
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
        
        label = Gtk.Label(label=f"¿Estás seguro de que deseas eliminar la categoría '{self.selected_category['name']}'?")
        content_area.append(label)
        
        warning = Gtk.Label(label="<b>Advertencia:</b> Se eliminarán todos los documentos asociados a esta categoría.")
        warning.set_use_markup(True)
        content_area.append(warning)
        
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        dialog.show()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # Eliminar documentos asociados a esta categoría
            documents_file = os.path.join(self.data_path, "documents.json")
            try:
                with open(documents_file, 'r') as f:
                    documents = json.load(f)
                    
                documents = [doc for doc in documents if doc["category_id"] != self.selected_category["id"]]
                
                with open(documents_file, 'w') as f:
                    json.dump(documents, f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
                
            # Eliminar la categoría
            self.categories = [c for c in self.categories if c["id"] != self.selected_category["id"]]
            self.save_categories()
            self.load_categories()
            
            self.selected_category = None
            self.edit_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)
                
        dialog.destroy()
        
    def save_categories(self):
        with open(self.categories_file, 'w') as f:
            json.dump(self.categories, f)
            
    def get_categories(self):
        return self.categories
