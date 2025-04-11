#!/usr/bin/env python3
import gi
import os
import json
import sys
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, Gio, GLib, Adw

# Importar módulos
from modules.dexter_category import CategoryManager
from modules.dexter_documents import DocumentManager
from modules.dexter_editor import Editor
from modules.dexter_config import ConfigManager
from modules.dexter_backup import BackupManager
from modules.dexter_about import AboutManager
from modules.dexter_file_manager import FileManager

class DexterOrganizer(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuración básica de la ventana
        self.set_default_size(950, 700)
        
        # Asegurar instancia única
        self.app = kwargs.get('application')
        
        # Cargar configuración
        self.data_path = os.path.expanduser("~/.local/share/dexter-organizer")
        os.makedirs(self.data_path, exist_ok=True)
        self.config_file = os.path.join(self.data_path, "config.json")
        self.load_config()
        
        # Verificar si document_manager está inicializado correctamente
        if not hasattr(self, 'document_manager'):
            self.document_manager = DocumentManager(self)
        
        # Verificar si config.json tiene todas las claves necesarias
        required_keys = {"backup_path", "data_path", "font_family", "font_size", "theme"}
        if not required_keys.issubset(self.config.keys()):
            self.config.update({
                "backup_path": os.path.expanduser("~/Documentos/DexterBackups"),
                "data_path": self.data_path,
                "font_family": "Sans",
                "font_size": 10,
                "theme": "dark"
            })
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        
        # Estructura principal
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.main_box)
        
        # Contenido principal
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box.append(self.content_box)
        
        # Área de contenido principal
        self.main_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_content.set_hexpand(True)
        self.content_box.append(self.main_content)
        
        # Configurar CSS
        self.css_provider = Gtk.CssProvider()
        self.apply_theme()
        
        # Header Bar
        self.create_header()
        
        # Panel lateral
        self.create_sidebar()
        
        # Inicializar módulos
        self.current_module = None
        self.category_manager = CategoryManager(self)
        self.config_manager = ConfigManager(self)
        self.backup_manager = BackupManager(self)
        self.about_manager = AboutManager(self)
        self.file_manager = FileManager(self)
        
        # Mostrar vista de documentos por defecto
        self.show_documents()
        
        # Configurar acciones
        self.setup_actions()
        
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            self.config = {
                "backup_path": os.path.expanduser("~/Documentos/DexterBackups"),
                "data_path": self.data_path,
                "font_family": "Sans",
                "font_size": 10,
                "theme": "dark"
            }
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
                
    def apply_theme(self):
        theme = self.config.get("theme", "dark")
        css_file = "dexter_dark.css" if theme == "dark" else "dexter_light.css"
        
        # Buscar el archivo CSS en varias ubicaciones posibles
        possible_paths = [
            # Si se ejecuta directamente desde el directorio del proyecto
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f'assets/{css_file}'),
            # Si se ejecuta desde el enlace simbólico en /usr/bin
            os.path.join('/usr/share/dexter-organizer', f'assets/{css_file}')
        ]
        
        # Obtener el display por defecto
        display = Gdk.Display.get_default()
        
        css_loaded = False
        for css_path in possible_paths:
            try:
                if os.path.exists(css_path):
                    print(f"Intentando cargar CSS desde: {css_path}")
                    self.css_provider.load_from_path(css_path)
                    
                    # Asegurar que el proveedor CSS se aplique a toda la aplicación
                    Gtk.StyleContext.add_provider_for_display(
                        display,
                        self.css_provider,
                        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                    )
                    print(f"CSS cargado correctamente desde: {css_path}")
                    
                    # Aplicar clases CSS específicas a componentes
                    if self.main_box:
                        self.main_box.add_css_class("main-box")
                    
                    # Forzar actualización de la interfaz
                    self.queue_draw()
                    
                    css_loaded = True
                    break
            except Exception as e:
                print(f"Error al cargar CSS desde {css_path}: {e}")
                
        if not css_loaded:
            print("No se pudo cargar ningún archivo CSS. Usando estilo predeterminado.")
            
    def create_header(self):
        header = Gtk.HeaderBar()
        header.set_show_title_buttons(True)
        
        # Búsqueda (ocupando todo el espacio disponible)
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        search_box.set_hexpand(True)
        
        # Crear el buscador
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_hexpand(True)  # Expandir horizontalmente
        self.search_entry.set_size_request(-1, 30)  # Altura fija para mejor apariencia
        self.search_entry.set_margin_start(10)
        self.search_entry.set_margin_end(10)
        self.search_entry.connect("search-changed", self.on_search_changed)
        
        # Añadir el buscador al contenedor
        search_box.append(self.search_entry)
        
        # Hacer que el buscador ocupe todo el espacio disponible
        header.set_title_widget(search_box)
        self.set_titlebar(header)
        
        # Botón menú (ahora primero en el lado derecho)
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        header.pack_end(menu_button)
        
        # Botón Toggle tema (ahora segundo en el lado derecho)
        self.theme_button = Gtk.Button()
        if self.config.get("theme", "dark") == "dark":
            self.theme_button.set_icon_name("weather-clear-symbolic")
        else:
            self.theme_button.set_icon_name("weather-clear-night-symbolic")
        self.theme_button.connect("clicked", self.toggle_theme)
        header.pack_end(self.theme_button)
        
        # Crear el menú usando un modelo simple
        menu_model = Gio.Menu()
        
        # Añadir elementos al menú
        config_item = Gio.MenuItem.new("Configuración", None)
        config_item.set_detailed_action("app.config")
        menu_model.append_item(config_item)
        
        about_item = Gio.MenuItem.new("Acerca de", None)
        about_item.set_detailed_action("app.about")
        menu_model.append_item(about_item)
        
        # Asignar el modelo al botón de menú
        menu_button.set_menu_model(menu_model)
        
        # Configurar las acciones directamente en la aplicación
        app = self.get_application()
        
        # Acción de configuración
        config_action = Gio.SimpleAction.new("config", None)
        config_action.connect("activate", lambda a, p: self.show_config())
        app.add_action(config_action)
        
        # Acción de acerca de
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", lambda a, p: self.show_about())
        app.add_action(about_action)
        
    def create_sidebar(self):
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        sidebar.set_size_request(200, -1)
        sidebar.add_css_class("sidebar")
        
        # Logo en la parte superior (solo texto)
        logo_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        logo_box.set_margin_top(15)
        logo_box.set_margin_bottom(15)
        logo_box.set_halign(Gtk.Align.CENTER)
        
        # Título principal
        app_name = Gtk.Label(label="<b>DexterOrganizer</b>")
        app_name.set_use_markup(True)
        app_name.add_css_class("title")
        
        # Subtítulo
        app_subtitle = Gtk.Label(label="Gestor de Archivos")
        app_subtitle.set_margin_top(2)
        app_subtitle.add_css_class("subtitle")
        
        logo_box.append(app_name)
        logo_box.append(app_subtitle)
        sidebar.append(logo_box)
        
        # Separador después del logo
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_bottom(10)
        sidebar.append(separator)
        
        # Botones de acción
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        action_box.set_margin_top(10)
        action_box.set_margin_bottom(10)
        action_box.set_margin_start(10)
        action_box.set_margin_end(10)
        
        add_button = Gtk.Button(icon_name="list-add-symbolic")
        add_button.set_tooltip_text("Añadir Documento")
        add_button.connect("clicked", self.on_add_document)
        
        edit_button = Gtk.Button(icon_name="document-edit-symbolic")
        edit_button.set_tooltip_text("Editar Documento")
        edit_button.connect("clicked", self.on_edit_document)
        
        delete_button = Gtk.Button(icon_name="user-trash-symbolic")
        delete_button.set_tooltip_text("Eliminar Documento")
        delete_button.connect("clicked", self.on_delete_document)
        
        action_box.append(add_button)
        action_box.append(edit_button)
        action_box.append(delete_button)
        action_box.set_halign(Gtk.Align.CENTER)
        sidebar.append(action_box)
        
        # Separador después de los botones
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator2.set_margin_bottom(10)
        sidebar.append(separator2)
        
        # Título de categorías
        categories_label = Gtk.Label(label="<b>Categorías</b>")
        categories_label.set_use_markup(True)
        categories_label.set_halign(Gtk.Align.START)
        categories_label.set_margin_start(10)
        categories_label.set_margin_bottom(5)
        sidebar.append(categories_label)
        
        # Lista de categorías
        self.categories_box = Gtk.ListBox()
        self.categories_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.categories_box.add_css_class("categories-list")
        self.categories_box.connect("row-selected", self.on_category_selected)
        
        # Añadir "Todos los documentos"
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        box.set_margin_top(5)
        box.set_margin_bottom(5)
        box.set_margin_start(5)
        box.set_margin_end(5)
        
        icon = Gtk.Image.new_from_icon_name("folder-symbolic")
        label = Gtk.Label(label="Todos los Documentos")
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)
        
        box.append(icon)
        box.append(label)
        row.set_child(box)
        # Usar un atributo en lugar de set_data
        row.category_id = 0
        
        self.categories_box.append(row)
        
        # Cargar categorías desde el archivo
        categories_file = os.path.join(self.data_path, "categories.json")
        try:
            with open(categories_file, 'r') as f:
                categories = json.load(f)
                
            for category in categories:
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
                box.set_margin_top(5)
                box.set_margin_bottom(5)
                box.set_margin_start(5)
                box.set_margin_end(5)
                
                icon = Gtk.Image.new_from_icon_name("folder-symbolic")
                label = Gtk.Label(label=category["name"])
                label.set_hexpand(True)
                label.set_halign(Gtk.Align.START)
                
                box.append(icon)
                box.append(label)
                row.set_child(box)
                # Usar un atributo en lugar de set_data
                row.category_id = category["id"]
                
                self.categories_box.append(row)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
            
        # Seleccionar "Todos los documentos" por defecto
        self.categories_box.select_row(self.categories_box.get_row_at_index(0))
        
        # Scrolled Window para categorías
        categories_scroll = Gtk.ScrolledWindow()
        categories_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        categories_scroll.set_vexpand(True)
        categories_scroll.set_child(self.categories_box)
        sidebar.append(categories_scroll)
        
        # Añadir sidebar al contenedor principal
        self.content_box.prepend(sidebar)
        
    def setup_actions(self):
        # Eliminar acciones existentes si las hay
        for action_name in ["config", "about"]:
            if self.lookup_action(action_name):
                self.remove_action(action_name)
                print(f"Acción {action_name} eliminada")
        
        # Acción para mostrar la configuración
        config_action = Gio.SimpleAction.new("config", None)
        config_action.connect("activate", self.on_config_action)
        self.add_action(config_action)
        print("Acción de configuración añadida")
        
        # Acción para mostrar acerca de
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_action)
        self.add_action(about_action)
        print("Acción de acerca de añadida")
        
    def on_config_action(self, action, param):
        print("Acción de configuración activada")
        self.show_config()
        
    def on_about_action(self, action, param):
        print("Acción de acerca de activada")
        self.show_about()
        
    def clear_main_content(self):
        for child in self.main_content:
            self.main_content.remove(child)
            
    def show_documents(self, category_id=None):
        self.clear_main_content()
        self.current_module = "documents"
        
        # Filtrar por categoría si se especifica
        if category_id is not None and category_id > 0:
            # Implementar filtrado por categoría
            pass
            
        self.main_content.append(self.document_manager.get_container())
        
    def show_editor(self, document=None):
        self.clear_main_content()
        self.current_module = "editor"
        
        editor = Editor(self, document, self.on_document_saved)
        self.main_content.append(editor.get_container())
        
    def show_config(self, action=None, param=None):
        self.clear_main_content()
        self.current_module = "config"
        self.main_content.append(self.config_manager.get_container())
        
    def show_backup(self):
        self.clear_main_content()
        self.current_module = "backup"
        self.main_content.append(self.backup_manager.get_container())
        
    def show_about(self, action=None, param=None):
        self.clear_main_content()
        self.current_module = "about"
        self.main_content.append(self.about_manager.get_container())
        
    def show_file_manager(self):
        self.clear_main_content()
        self.current_module = "file_manager"
        self.main_content.append(self.file_manager.get_container())
        
    def toggle_theme(self, button):
        # Cambiar el tema
        current_theme = self.config.get("theme", "dark")
        new_theme = "light" if current_theme == "dark" else "dark"
        self.config["theme"] = new_theme
        
        # Actualizar el botón
        if new_theme == "light":
            button.set_icon_name("weather-clear-night-symbolic")
        else:
            button.set_icon_name("weather-clear-symbolic")
        
        print(f"Cambiando de tema {current_theme} a {new_theme}")
        
        # Guardar la configuración
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
        
        # Eliminar el proveedor CSS anterior
        display = Gdk.Display.get_default()
        try:
            Gtk.StyleContext.remove_provider_for_display(display, self.css_provider)
        except Exception as e:
            print(f"Error al eliminar proveedor CSS: {e}")
        
        # Crear un nuevo proveedor CSS y aplicarlo
        self.css_provider = Gtk.CssProvider()
        
        # Determinar la ruta del archivo CSS
        css_file = "dexter_dark.css" if new_theme == "dark" else "dexter_light.css"
        
        # Buscar el archivo CSS en varias ubicaciones posibles
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f'assets/{css_file}'),
            os.path.join('/usr/share/dexter-organizer', f'assets/{css_file}')
        ]
        
        # Cargar el CSS
        css_loaded = False
        for css_path in possible_paths:
            if os.path.exists(css_path):
                try:
                    print(f"Cargando CSS desde: {css_path}")
                    self.css_provider.load_from_path(css_path)
                    Gtk.StyleContext.add_provider_for_display(
                        display,
                        self.css_provider,
                        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                    )
                    css_loaded = True
                    print(f"CSS cargado correctamente")
                    break
                except Exception as e:
                    print(f"Error al cargar CSS: {e}")
        
        if not css_loaded:
            print("No se pudo cargar el CSS")
        
        # Forzar redibujado completo
        self.queue_draw()
        
        # Reiniciar la aplicación para aplicar el tema completamente
        print("Reiniciando la aplicación para aplicar el tema...")
        self.get_application().quit()
        # Iniciar la aplicación nuevamente
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    def on_search_changed(self, entry):
        search_text = entry.get_text().lower()
        
        # Implementar búsqueda de documentos
        if self.current_module == "documents":
            # Filtrar documentos según el texto de búsqueda
            pass
            
    def on_category_selected(self, list_box, row):
        if row is None:
            return
            
        # Usar el atributo en lugar de get_data
        category_id = getattr(row, 'category_id', 0)
        self.show_documents(category_id)
        
    def on_add_document(self, button):
        self.show_editor()
        
    def on_edit_document(self, button):
        # Obtener el documento seleccionado del DocumentManager
        selected_document = self.document_manager.selected_document
        if selected_document:
            self.show_editor(selected_document)
        else:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Ningún documento seleccionado"
            )
            dialog.format_secondary_text("Por favor, selecciona un documento para editar.")
            dialog.run()
            dialog.destroy()
            
    def on_delete_document(self, button):
        # Delegar al DocumentManager
        self.document_manager.on_delete_document(button)
        
    def on_document_saved(self, document):
        if document:
            # Si es un documento nuevo, añadirlo a la lista
            documents_file = os.path.join(self.data_path, "documents.json")
            try:
                with open(documents_file, 'r') as f:
                    documents = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                documents = []
                
            # Comprobar si el documento ya existe
            existing_doc = next((d for d in documents if d["id"] == document["id"]), None)
            if existing_doc:
                # Actualizar documento existente
                for i, doc in enumerate(documents):
                    if doc["id"] == document["id"]:
                        documents[i] = document
                        break
            else:
                # Añadir nuevo documento
                documents.append(document)
                
            # Guardar documentos
            with open(documents_file, 'w') as f:
                json.dump(documents, f)
                
        # Volver a la vista de documentos
        self.show_documents()

class DexterOrganizerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.dexteros.organizer",
                        flags=Gio.ApplicationFlags.FLAGS_NONE)
        
    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = DexterOrganizer(application=self)
        win.present()

def main():
    app = DexterOrganizerApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    main()
