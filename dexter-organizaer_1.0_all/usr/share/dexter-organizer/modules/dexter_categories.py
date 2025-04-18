#!/usr/bin/env python3

import os
import json
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf, Pango, Gdk

class DexterCategorys(Gtk.Box):
    def __init__(self, parent_window=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.parent_window = parent_window
        self.categories = []
        self.documents = []
        self.selected_category = None
        self.after_save_callback = None
        self.init_ui()
        self.load_data()
    
    def connect_after_save(self, callback):
        """Registra una función callback que se llamará después de guardar cambios"""
        self.after_save_callback = callback
        
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        self.set_border_width(15)
        self.set_hexpand(True)
        self.set_vexpand(True)
        
        # Contenedor principal con dos paneles lado a lado
        main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_paned.set_position(250)  # Posición inicial del divisor
        main_paned.set_wide_handle(True)  # Mango más ancho para mejor usabilidad
        
        # Panel izquierdo: Lista de categorías
        self.categories_frame = Gtk.Frame()
        self.categories_frame.set_shadow_type(Gtk.ShadowType.NONE)
        self.categories_frame.set_name("categories-frame")
        
        # ScrolledWindow para la lista de categorías
        categories_scroll = Gtk.ScrolledWindow()
        categories_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        categories_scroll.set_min_content_width(200)
        
        # Contenedor vertical para las categorías
        self.categories_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.categories_box.set_name("categories-box")
        self.categories_box.set_margin_top(10)
        self.categories_box.set_margin_bottom(10)
        self.categories_box.set_margin_start(10)
        self.categories_box.set_margin_end(10)
        
        # Título de categorías
        categories_title = Gtk.Label(label="Categorías")
        categories_title.set_name("categories-title")
        categories_title.set_halign(Gtk.Align.START)
        categories_title.set_margin_bottom(10)
        self.categories_box.pack_start(categories_title, False, False, 0)
        
        # Aquí se añadirán dinámicamente las categorías
        
        # Botón para agregar nueva categoría
        add_category_button = Gtk.Button()
        add_category_button.set_relief(Gtk.ReliefStyle.NONE)
        add_category_button.set_name("add-category-button")
        
        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        add_icon = Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON)
        add_label = Gtk.Label(label="Nueva Categoría")
        add_box.pack_start(add_icon, False, False, 5)
        add_box.pack_start(add_label, False, False, 5)
        
        add_category_button.add(add_box)
        add_category_button.connect("clicked", self.on_add_category)
        
        self.categories_box.pack_end(add_category_button, False, False, 10)
        
        categories_scroll.add(self.categories_box)
        self.categories_frame.add(categories_scroll)
        
        # Panel derecho: Lista de documentos de la categoría seleccionada
        self.documents_frame = Gtk.Frame()
        self.documents_frame.set_shadow_type(Gtk.ShadowType.NONE)
        self.documents_frame.set_name("documents-frame")
        
        # ScrolledWindow para la lista de documentos
        documents_scroll = Gtk.ScrolledWindow()
        documents_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Contenedor para los documentos
        self.documents_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.documents_box.set_name("documents-box")
        self.documents_box.set_margin_top(10)
        self.documents_box.set_margin_bottom(10)
        self.documents_box.set_margin_start(15)
        self.documents_box.set_margin_end(15)
        
        # Contenedor para el título y botones de acción
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        header_box.set_margin_bottom(15)
        
        # Título de documentos
        self.documents_title = Gtk.Label(label="Documentos")
        self.documents_title.set_name("documents-title")
        self.documents_title.set_halign(Gtk.Align.START)
        self.documents_title.set_hexpand(True)
        header_box.pack_start(self.documents_title, True, True, 0)
        
        # Botones de acción para documentos
        add_doc_button = Gtk.Button()
        add_doc_button.set_tooltip_text("Añadir Documento")
        add_doc_button.set_relief(Gtk.ReliefStyle.NONE)
        add_doc_icon = Gtk.Image.new_from_icon_name("document-new-symbolic", Gtk.IconSize.BUTTON)
        add_doc_button.add(add_doc_icon)
        add_doc_button.connect("clicked", self.on_add_document)
        
        edit_doc_button = Gtk.Button()
        edit_doc_button.set_tooltip_text("Editar Documento")
        edit_doc_button.set_relief(Gtk.ReliefStyle.NONE)
        edit_doc_icon = Gtk.Image.new_from_icon_name("document-edit-symbolic", Gtk.IconSize.BUTTON)
        edit_doc_button.add(edit_doc_icon)
        edit_doc_button.connect("clicked", self.on_edit_document)
        
        delete_doc_button = Gtk.Button()
        delete_doc_button.set_tooltip_text("Eliminar Documento")
        delete_doc_button.set_relief(Gtk.ReliefStyle.NONE)
        delete_doc_icon = Gtk.Image.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON)
        delete_doc_button.add(delete_doc_icon)
        delete_doc_button.connect("clicked", self.on_delete_document)
        
        view_doc_button = Gtk.Button()
        view_doc_button.set_tooltip_text("Ver Documento")
        view_doc_button.set_relief(Gtk.ReliefStyle.NONE)
        view_doc_icon = Gtk.Image.new_from_icon_name("document-open-symbolic", Gtk.IconSize.BUTTON)
        view_doc_button.add(view_doc_icon)
        view_doc_button.connect("clicked", self.on_view_document)
        
        # Añadir botones al header
        header_box.pack_start(add_doc_button, False, False, 2)
        header_box.pack_start(edit_doc_button, False, False, 2)
        header_box.pack_start(delete_doc_button, False, False, 2)
        header_box.pack_start(view_doc_button, False, False, 2)
        
        self.documents_box.pack_start(header_box, False, False, 0)
        
        # FlowBox para mostrar documentos en una cuadrícula
        self.documents_flow = Gtk.FlowBox()
        self.documents_flow.set_valign(Gtk.Align.START)
        self.documents_flow.set_max_children_per_line(20)
        self.documents_flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.documents_flow.set_homogeneous(True)
        self.documents_flow.set_row_spacing(20)
        self.documents_flow.set_column_spacing(20)
        self.documents_flow.connect("child-activated", self.on_document_selected)
        
        self.documents_box.pack_start(self.documents_flow, True, True, 0)
        
        documents_scroll.add(self.documents_box)
        self.documents_frame.add(documents_scroll)
        
        # Agregar los paneles al divisor
        main_paned.pack1(self.categories_frame, False, False)
        main_paned.pack2(self.documents_frame, True, True)
        
        # Agregar el divisor al contenedor principal
        self.pack_start(main_paned, True, True, 0)
    
    def load_data(self):
        """Carga los datos de categorías y documentos desde los archivos JSON"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        categories_file = os.path.join(base_dir, "data", "categories.json")
        documents_file = os.path.join(base_dir, "data", "documents.json")
        
        # Asegurar que exista el directorio data
        data_dir = os.path.join(base_dir, "data")
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
                print(f"Directorio creado: {data_dir}")
            except Exception as e:
                print(f"Error al crear directorio: {e}")
        
        # Cargar categorías
        if os.path.exists(categories_file):
            try:
                with open(categories_file, 'r') as f:
                    self.categories = json.load(f).get('categories', [])
            except Exception as e:
                print(f"Error al cargar categorías: {e}")
                self.categories = []
        else:
            # Crear archivo de categorías vacío
            self.categories = []
            try:
                with open(categories_file, 'w') as f:
                    json.dump({"categories": []}, f, indent=4)
                print(f"Archivo de categorías creado: {categories_file}")
            except Exception as e:
                print(f"Error al crear archivo de categorías: {e}")
        
        # Cargar documentos
        if os.path.exists(documents_file):
            try:
                with open(documents_file, 'r') as f:
                    self.documents = json.load(f).get('documents', [])
            except Exception as e:
                print(f"Error al cargar documentos: {e}")
                self.documents = []
        else:
            # Crear archivo de documentos vacío
            self.documents = []
            try:
                with open(documents_file, 'w') as f:
                    json.dump({"documents": []}, f, indent=4)
                print(f"Archivo de documentos creado: {documents_file}")
            except Exception as e:
                print(f"Error al crear archivo de documentos: {e}")
        
        # Poblar la interfaz con las categorías cargadas
        self.populate_categories()
    
    def populate_categories(self):
        """Rellena la lista de categorías en la interfaz"""
        # Eliminar categorías previas (excepto título y botón de agregar)
        for child in self.categories_box.get_children()[1:-1]:
            self.categories_box.remove(child)
        
        # Añadir cada categoría
        for category in self.categories:
            category_button = self.create_category_button(category)
            # Insertar antes del último elemento (botón agregar)
            self.categories_box.pack_start(category_button, False, False, 0)
            self.categories_box.reorder_child(category_button, 1)  # Después del título
        
        # Mostrar todos los elementos
        self.categories_box.show_all()
        
        # Seleccionar la primera categoría por defecto
        if self.categories:
            first_category_button = self.categories_box.get_children()[1]
            first_category_button.clicked()
    
    def create_category_button(self, category):
        """Crea un botón para una categoría"""
        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_name(f"category-button-{category['id']}")
        button.category_id = category['id']  # Guardar ID para referencia
        
        # Contenedor horizontal para icono y etiqueta
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(5)
        box.set_margin_end(5)
        
        # Icono de la categoría
        icon_name = category.get('icon', 'folder-documents-symbolic')
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        
        # Si hay un color definido para la categoría, aplicarlo al icono
        if 'color' in category and category['color']:
            # Crear un estilo CSS para colorear el icono
            css_provider = Gtk.CssProvider()
            css = f"""
                #category-button-{category['id']} image {{
                    color: {category['color']};
                }}
            """
            css_provider.load_from_data(css.encode())
            icon_context = icon.get_style_context()
            icon_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Etiqueta de la categoría
        label = Gtk.Label(label=category['name'])
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        
        # Añadir icono y etiqueta al contenedor
        box.pack_start(icon, False, False, 0)
        box.pack_start(label, True, True, 0)
        
        button.add(box)
        
        # Conectar señal de clic
        button.connect("clicked", self.on_category_selected, category)
        
        return button
    
    def on_category_selected(self, button, category):
        """Maneja la selección de una categoría"""
        self.selected_category = category
        
        # Actualizar título
        self.documents_title.set_text(f"Documentos - {category['name']}")
        
        # Cargar documentos de esta categoría
        self.populate_documents(category['id'])
    
    def populate_documents(self, category_id):
        """Rellena el contenedor de documentos para la categoría seleccionada"""
        # Limpiar documentos previos
        for child in self.documents_flow.get_children():
            self.documents_flow.remove(child)
        
        # Filtrar documentos por categoría
        category_documents = [doc for doc in self.documents if doc['category_id'] == category_id]
        
        # Si no hay documentos, mostrar mensaje
        if not category_documents:
            empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            empty_box.set_halign(Gtk.Align.CENTER)
            empty_box.set_valign(Gtk.Align.CENTER)
            
            empty_icon = Gtk.Image.new_from_icon_name("folder-symbolic", Gtk.IconSize.DIALOG)
            empty_label = Gtk.Label(label="No hay documentos en esta categoría")
            empty_label.set_name("empty-category-label")
            
            empty_box.pack_start(empty_icon, False, False, 0)
            empty_box.pack_start(empty_label, False, False, 0)
            
            self.documents_flow.add(empty_box)
        else:
            # Añadir cada documento
            for doc in category_documents:
                doc_box = self.create_document_box(doc)
                self.documents_flow.add(doc_box)
        
        self.documents_flow.show_all()
    
    def create_document_box(self, document):
        """Crea una caja para representar un documento"""
        # Contenedor principal
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.START)
        box.set_name(f"document-box-{document['id']}")
        box.document_id = document['id']  # Guardar ID para referencia
        box.file_path = document['file_path']  # Guardar ruta para abrir documento
        
        # Frame para dar aspecto de tarjeta
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.OUT)
        
        inner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        inner_box.set_border_width(8)
        
        # Icono del documento
        icon_name = document.get('icon', 'text-x-generic-symbolic')
        icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        
        # Nombre del documento
        name_label = Gtk.Label(label=document['name'])
        name_label.set_max_width_chars(20)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.set_tooltip_text(document['name'])
        
        # Tipo de archivo
        file_type = document.get('file_type', '').upper()
        type_label = Gtk.Label(label=file_type)
        type_label.set_name("document-type-label")
        
        # Añadir elementos al contenedor
        inner_box.pack_start(icon, False, False, 5)
        inner_box.pack_start(name_label, False, False, 2)
        inner_box.pack_start(type_label, False, False, 2)
        
        frame.add(inner_box)
        box.pack_start(frame, True, True, 0)
        
        return box
    
    def on_document_selected(self, flowbox, flowbox_child):
        """Maneja la selección de un documento"""
        document_box = flowbox_child.get_child()
        document_id = document_box.document_id
        file_path = document_box.file_path
        
        # Buscar el documento por ID
        selected_document = next((doc for doc in self.documents if doc['id'] == document_id), None)
        
        if selected_document:
            print(f"Documento seleccionado: {selected_document['name']}")
            # Aquí se podría mostrar más información o abrir el documento
    
    def on_add_category(self, button):
        """Maneja el clic en el botón de agregar categoría"""
        # Crear diálogo para nueva categoría
        dialog = Gtk.Dialog(title="Nueva Categoría", parent=self.parent_window, flags=0)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        dialog.set_default_size(300, 200)
        
        # Contenedor para el formulario
        content_area = dialog.get_content_area()
        content_area.set_border_width(15)
        content_area.set_spacing(10)
        
        # Campo para el nombre
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        name_label = Gtk.Label(label="Nombre:")
        name_label.set_halign(Gtk.Align.START)
        name_entry = Gtk.Entry()
        name_entry.set_hexpand(True)
        name_box.pack_start(name_label, False, False, 0)
        name_box.pack_start(name_entry, True, True, 0)
        content_area.pack_start(name_box, False, False, 0)
        
        # Campo para la descripción
        desc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        desc_label = Gtk.Label(label="Descripción:")
        desc_label.set_halign(Gtk.Align.START)
        desc_entry = Gtk.Entry()
        desc_entry.set_hexpand(True)
        desc_box.pack_start(desc_label, False, False, 0)
        desc_box.pack_start(desc_entry, True, True, 0)
        content_area.pack_start(desc_box, False, False, 0)
        
        # Campo para el color
        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        color_label = Gtk.Label(label="Color:")
        color_label.set_halign(Gtk.Align.START)
        color_button = Gtk.ColorButton()
        color_box.pack_start(color_label, False, False, 0)
        color_box.pack_start(color_button, False, False, 0)
        content_area.pack_start(color_box, False, False, 0)
        
        # Campo para el icono (simplificado, se podría mejorar)
        icon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        icon_label = Gtk.Label(label="Icono:")
        icon_label.set_halign(Gtk.Align.START)
        icon_combo = Gtk.ComboBoxText()
        icons = ["folder-documents-symbolic", "folder-symbolic", "folder-pictures-symbolic", 
                "folder-music-symbolic", "folder-videos-symbolic", "folder-download-symbolic"]
        for icon in icons:
            icon_combo.append_text(icon)
        icon_combo.set_active(0)  # Seleccionar el primero por defecto
        icon_box.pack_start(icon_label, False, False, 0)
        icon_box.pack_start(icon_combo, True, True, 0)
        content_area.pack_start(icon_box, False, False, 0)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            name = name_entry.get_text()
            description = desc_entry.get_text()
            rgba = color_button.get_rgba()
            color = f"rgba({rgba.red*255},{rgba.green*255},{rgba.blue*255},{rgba.alpha})"
            icon = icon_combo.get_active_text()
            
            # Crear nueva categoría
            new_id = max([c['id'] for c in self.categories], default=0) + 1
            new_category = {
                "id": new_id,
                "name": name,
                "icon": icon,
                "color": color,
                "description": description
            }
            
            # Añadir a la lista y guardar
            self.categories.append(new_category)
            self.save_categories()
            
            # Actualizar la interfaz
            self.populate_categories()
        
        dialog.destroy()
    
    def on_add_document(self, button):
        """Maneja el clic en el botón de agregar documento"""
        if not self.selected_category:
            # Mostrar mensaje de error si no hay categoría seleccionada
            dialog = Gtk.MessageDialog(
                parent=self.parent_window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error"
            )
            dialog.format_secondary_text("Debe seleccionar una categoría primero.")
            dialog.run()
            dialog.destroy()
            return
        
        # Abrir diálogo de selección de archivo
        file_dialog = Gtk.FileChooserDialog(
            title="Seleccionar Documento",
            parent=self.parent_window,
            action=Gtk.FileChooserAction.OPEN
        )
        file_dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = file_dialog.run()
        
        if response == Gtk.ResponseType.OK:
            file_path = file_dialog.get_filename()
            file_name = os.path.basename(file_path)
            file_type = os.path.splitext(file_name)[1].lstrip('.')
            
            # Determinar el icono apropiado
            icon = self.get_icon_for_file_type(file_type)
            
            # Crear nuevo documento
            new_id = max([d['id'] for d in self.documents], default=0) + 1
            new_document = {
                "id": new_id,
                "category_id": self.selected_category['id'],
                "name": file_name,
                "file_path": file_path,
                "file_type": file_type,
                "icon": icon,
                "description": "",
                "date_created": GLib.DateTime.new_now_local().format("%Y-%m-%dT%H:%M:%S"),
                "date_modified": GLib.DateTime.new_now_local().format("%Y-%m-%dT%H:%M:%S"),
                "tags": []
            }
            
            # Añadir a la lista y guardar
            self.documents.append(new_document)
            self.save_documents()
            
            # Actualizar la interfaz
            self.populate_documents(self.selected_category['id'])
        
        file_dialog.destroy()
    
    def on_edit_document(self, button):
        """Maneja el clic en el botón de editar documento"""
        # Obtener el documento seleccionado
        selected = self.documents_flow.get_selected_children()
        
        if not selected:
            dialog = Gtk.MessageDialog(
                parent=self.parent_window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error"
            )
            dialog.format_secondary_text("Debe seleccionar un documento primero.")
            dialog.run()
            dialog.destroy()
            return
        
        document_box = selected[0].get_child()
        document_id = document_box.document_id
        
        # Buscar el documento por ID
        document = next((doc for doc in self.documents if doc['id'] == document_id), None)
        
        if document:
            # Crear diálogo para editar documento
            dialog = Gtk.Dialog(title="Editar Documento", parent=self.parent_window, flags=0)
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
            dialog.set_default_size(350, 250)
            
            # Contenedor para el formulario
            content_area = dialog.get_content_area()
            content_area.set_border_width(15)
            content_area.set_spacing(10)
            
            # Campo para el nombre
            name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            name_label = Gtk.Label(label="Nombre:")
            name_label.set_halign(Gtk.Align.START)
            name_entry = Gtk.Entry()
            name_entry.set_text(document['name'])
            name_entry.set_hexpand(True)
            name_box.pack_start(name_label, False, False, 0)
            name_box.pack_start(name_entry, True, True, 0)
            content_area.pack_start(name_box, False, False, 0)
            
            # Campo para la descripción
            desc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            desc_label = Gtk.Label(label="Descripción:")
            desc_label.set_halign(Gtk.Align.START)
            desc_entry = Gtk.Entry()
            desc_entry.set_text(document.get('description', ''))
            desc_entry.set_hexpand(True)
            desc_box.pack_start(desc_label, False, False, 0)
            desc_box.pack_start(desc_entry, True, True, 0)
            content_area.pack_start(desc_box, False, False, 0)
            
            # Campo para las etiquetas
            tags_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            tags_label = Gtk.Label(label="Etiquetas:")
            tags_label.set_halign(Gtk.Align.START)
            tags_entry = Gtk.Entry()
            tags_entry.set_text(', '.join(document.get('tags', [])))
            tags_entry.set_hexpand(True)
            tags_box.pack_start(tags_label, False, False, 0)
            tags_box.pack_start(tags_entry, True, True, 0)
            content_area.pack_start(tags_box, False, False, 0)
            
            # ComboBox para cambiar de categoría
            cat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            cat_label = Gtk.Label(label="Categoría:")
            cat_label.set_halign(Gtk.Align.START)
            cat_combo = Gtk.ComboBoxText()
            
            for i, cat in enumerate(self.categories):
                cat_combo.append_text(cat['name'])
                if cat['id'] == document['category_id']:
                    cat_combo.set_active(i)
            
            cat_box.pack_start(cat_label, False, False, 0)
            cat_box.pack_start(cat_combo, True, True, 0)
            content_area.pack_start(cat_box, False, False, 0)
            
            dialog.show_all()
            response = dialog.run()
            
            if response == Gtk.ResponseType.OK:
                # Actualizar documento
                document['name'] = name_entry.get_text()
                document['description'] = desc_entry.get_text()
                document['tags'] = [tag.strip() for tag in tags_entry.get_text().split(',') if tag.strip()]
                
                # Actualizar categoría si cambió
                new_cat_name = cat_combo.get_active_text()
                new_cat = next((c for c in self.categories if c['name'] == new_cat_name), None)
                if new_cat:
                    document['category_id'] = new_cat['id']
                
                document['date_modified'] = GLib.DateTime.new_now_local().format("%Y-%m-%dT%H:%M:%S")
                
                # Guardar cambios
                self.save_documents()
                
                # Actualizar interfaz
                self.populate_documents(self.selected_category['id'])
            
            dialog.destroy()
    
    def on_delete_document(self, button):
        """Maneja el clic en el botón de eliminar documento"""
        # Obtener el documento seleccionado
        selected = self.documents_flow.get_selected_children()
        
        if not selected:
            dialog = Gtk.MessageDialog(
                parent=self.parent_window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error"
            )
            dialog.format_secondary_text("Debe seleccionar un documento primero.")
            dialog.run()
            dialog.destroy()
            return
        
        document_box = selected[0].get_child()
        document_id = document_box.document_id
        
        # Confirmar eliminación
        dialog = Gtk.MessageDialog(
            parent=self.parent_window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Confirmar Eliminación"
        )
        dialog.format_secondary_text("¿Está seguro que desea eliminar este documento?")
        response = dialog.run()
        
        if response == Gtk.ResponseType.YES:
            # Eliminar el documento
            self.documents = [doc for doc in self.documents if doc['id'] != document_id]
            self.save_documents()
            
            # Actualizar interfaz
            self.populate_documents(self.selected_category['id'])
        
        dialog.destroy()
    
    def on_view_document(self, button):
        """Maneja el clic en el botón de ver documento"""
        # Obtener el documento seleccionado
        selected = self.documents_flow.get_selected_children()
        
        if not selected:
            dialog = Gtk.MessageDialog(
                parent=self.parent_window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error"
            )
            dialog.format_secondary_text("Debe seleccionar un documento primero.")
            dialog.run()
            dialog.destroy()
            return
        
        document_box = selected[0].get_child()
        file_path = document_box.file_path
        
        # Intentar abrir el documento con la aplicación predeterminada
        if os.path.exists(file_path):
            try:
                # Usar GIO para abrir con la aplicación predeterminada
                file_uri = GLib.filename_to_uri(file_path, None)
                Gtk.show_uri_on_window(self.parent_window, file_uri, Gdk.CURRENT_TIME)
            except Exception as e:
                dialog = Gtk.MessageDialog(
                    parent=self.parent_window,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Error al abrir documento"
                )
                dialog.format_secondary_text(f"No se pudo abrir el archivo: {str(e)}")
                dialog.run()
                dialog.destroy()
        else:
            dialog = Gtk.MessageDialog(
                parent=self.parent_window,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Archivo no encontrado"
            )
            dialog.format_secondary_text(f"No se encontró el archivo: {file_path}")
            dialog.run()
            dialog.destroy()
    
    def save_categories(self):
        """Guarda las categorías en el archivo JSON"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        categories_file = os.path.join(data_dir, "categories.json")
        
        # Asegurar que exista el directorio data
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
                print(f"Directorio creado: {data_dir}")
            except Exception as e:
                print(f"Error al crear directorio: {e}")
                return
        
        try:
            with open(categories_file, 'w') as f:
                json.dump({"categories": self.categories}, f, indent=4)
            print("Categorías guardadas correctamente")
            
            # Llamar al callback si está definido
            if self.after_save_callback:
                self.after_save_callback()
        except Exception as e:
            print(f"Error al guardar categorías: {e}")
    
    def save_documents(self):
        """Guarda los documentos en el archivo JSON"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        documents_file = os.path.join(data_dir, "documents.json")
        
        # Asegurar que exista el directorio data
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
                print(f"Directorio creado: {data_dir}")
            except Exception as e:
                print(f"Error al crear directorio: {e}")
                return
        
        try:
            with open(documents_file, 'w') as f:
                json.dump({"documents": self.documents}, f, indent=4)
            print("Documentos guardados correctamente")
            
            # Llamar al callback si está definido
            # Note: los documentos no afectan el sidebar, pero mantenemos coherencia
            if self.after_save_callback:
                self.after_save_callback()
        except Exception as e:
            print(f"Error al guardar documentos: {e}")
    
    def get_icon_for_file_type(self, file_type):
        """Devuelve el nombre del icono apropiado para un tipo de archivo"""
        icon_map = {
            # Documentos de texto
            'txt': 'text-x-generic-symbolic',
            'md': 'text-x-generic-symbolic',
            'rtf': 'text-x-generic-symbolic',
            
            # Documentos de Office
            'doc': 'x-office-document-symbolic',
            'docx': 'x-office-document-symbolic',
            'odt': 'x-office-document-symbolic',
            'xls': 'x-office-spreadsheet-symbolic',
            'xlsx': 'x-office-spreadsheet-symbolic',
            'ods': 'x-office-spreadsheet-symbolic',
            'ppt': 'x-office-presentation-symbolic',
            'pptx': 'x-office-presentation-symbolic',
            'odp': 'x-office-presentation-symbolic',
            
            # PDFs
            'pdf': 'x-office-document-symbolic',
            
            # Imágenes
            'jpg': 'image-x-generic-symbolic',
            'jpeg': 'image-x-generic-symbolic',
            'png': 'image-x-generic-symbolic',
            'gif': 'image-x-generic-symbolic',
            'svg': 'image-x-generic-symbolic',
            'bmp': 'image-x-generic-symbolic',
            
            # Audio
            'mp3': 'audio-x-generic-symbolic',
            'wav': 'audio-x-generic-symbolic',
            'ogg': 'audio-x-generic-symbolic',
            'flac': 'audio-x-generic-symbolic',
            
            # Video
            'mp4': 'video-x-generic-symbolic',
            'avi': 'video-x-generic-symbolic',
            'mkv': 'video-x-generic-symbolic',
            'mov': 'video-x-generic-symbolic',
            
            # Comprimidos
            'zip': 'package-x-generic-symbolic',
            'rar': 'package-x-generic-symbolic',
            'tar': 'package-x-generic-symbolic',
            'gz': 'package-x-generic-symbolic',
            '7z': 'package-x-generic-symbolic',
            
            # Código
            'py': 'text-x-script-symbolic',
            'js': 'text-x-script-symbolic',
            'html': 'text-x-script-symbolic',
            'css': 'text-x-script-symbolic',
            'c': 'text-x-script-symbolic',
            'cpp': 'text-x-script-symbolic',
            'java': 'text-x-script-symbolic',
            'php': 'text-x-script-symbolic'
        }
        
        return icon_map.get(file_type.lower(), 'text-x-generic-symbolic')
    
    def select_category_by_id(self, category_id):
        """Selecciona una categoría por su ID"""
        # Buscar la categoría por ID
        selected_category = next((cat for cat in self.categories if cat['id'] == category_id), None)
        
        if selected_category:
            # Buscar el botón correspondiente a esta categoría
            for i, child in enumerate(self.categories_box.get_children()):
                # Ignorar el título (índice 0) y el botón de agregar (último)
                if i > 0 and i < len(self.categories_box.get_children()) - 1:
                    button = child
                    if hasattr(button, 'category_id') and button.category_id == category_id:
                        # Simular un clic en el botón
                        button.clicked()
                        return True
        
        return False
    
    def load_module(self, parent_container):
        """Método para cargar este módulo en el contenedor principal"""
        # Limpiar el contenedor padre primero
        for child in parent_container.get_children():
            parent_container.remove(child)
        
        # Añadir este módulo al contenedor
        parent_container.add(self)
        parent_container.show_all()

if __name__ == "__main__":
    win = Gtk.Window(title="DexterCategorys")
    win.set_default_size(900, 600)
    win.connect("destroy", Gtk.main_quit)
    
    # Crear y añadir el widget de categorías
    categorys = DexterCategorys(win)
    win.add(categorys)
    
    # Mostrar todo y ejecutar
    win.show_all()
    Gtk.main()
