#!/usr/bin/env python3

"""
Dexter Organizer - Aplicación para organización de documentos
Author: Victor oubiña Faubel - oubinav78@gmail.com
Website: https://sourceforge.net/projects/dexter-gnome/
"""

import os
import sys
import json
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GLib, Gio, WebKit2, Pango

class DexterOrganizer(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="com.dexter.organizer",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)
        self.window = None
        self.categories = {}
        self.current_category = None
        self.current_document = None
        self.edit_mode = False
        self.data_path = os.path.join(GLib.get_user_data_dir(), "dexter-organizer")
        self.data_file = os.path.join(self.data_path, "data.json")
        
        # Asegurar que el directorio de datos existe
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
            
        # Inicializar documentos y carpeta
        self.documents_path = os.path.join(self.data_path, "documents")
        if not os.path.exists(self.documents_path):
            os.makedirs(self.documents_path)
            
        # Cargar datos al iniciar
        self.load_data()
        self.dark_theme = True

    def on_activate(self, app):
        # Verificar si ya hay una instancia en ejecución
        if not self.window:
        
            self.load_css_theme()
            
            # Crear ventana principal
            self.window = Gtk.ApplicationWindow(application=app)
   
            # Crear un HeaderBar
            headerbar = Gtk.HeaderBar()
            headerbar.set_show_close_button(True)
            headerbar.set_title("Dexter Organizer")
            self.window.set_titlebar(headerbar)

            self.window.set_default_size(950, 700)
            self.window.set_position(Gtk.WindowPosition.CENTER)
            self.window.set_name("main-window")
            
            # Añadir justo antes de headerbar.pack_end(menu_button)
            theme_switch = Gtk.Switch()
            theme_switch.set_active(self.dark_theme)
            theme_switch.connect("notify::active", self.on_theme_switch_activated)

            # Para añadir los iconos (opcional)
            moon_icon = Gtk.Image.new_from_icon_name("weather-clear-night-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
            sun_icon = Gtk.Image.new_from_icon_name("weather-clear-symbolic", Gtk.IconSize.SMALL_TOOLBAR)

            switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            switch_box.pack_start(moon_icon, False, False, 0)
            switch_box.pack_start(theme_switch, False, False, 0)
            switch_box.pack_start(sun_icon, False, False, 0)

            # Crear layout principal
            main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.window.add(main_box)
            
            # Panel lateral
            sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            sidebar.set_size_request(180, -1)
            sidebar.get_style_context().add_class("sidebar")
            
            # Logo/Título
            sidebar_header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            sidebar_header.get_style_context().add_class("sidebar-header")
            
            title_label = Gtk.Label(label="DexterOrganizer")
            title_label.get_style_context().add_class("app-title")
            subtitle_label = Gtk.Label(label="Mantenimiento del Sistema")
            subtitle_label.get_style_context().add_class("app-subtitle")
            
            # Crear una fila de botones de acción
            action_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            action_buttons_box.set_halign(Gtk.Align.CENTER)
            action_buttons_box.set_spacing(5)
            
            # Botón Añadir
            add_button = Gtk.Button()
            add_button.set_image(Gtk.Image.new_from_icon_name("list-add", Gtk.IconSize.BUTTON))
            add_button.connect("clicked", self.on_add_clicked)
            add_button.get_style_context().add_class("sidebar-action-button")
            
            # Botón Editar
            edit_button = Gtk.Button()
            edit_button.set_image(Gtk.Image.new_from_icon_name("document-edit", Gtk.IconSize.BUTTON))
            edit_button.connect("clicked", self.on_edit_clicked)
            edit_button.get_style_context().add_class("sidebar-action-button")
            
            # Botón Eliminar
            delete_button = Gtk.Button()
            delete_button.set_image(Gtk.Image.new_from_icon_name("edit-delete", Gtk.IconSize.BUTTON))
            delete_button.connect("clicked", self.on_delete_clicked)
            delete_button.get_style_context().add_class("sidebar-action-button")
            
            # Añadir botones al contenedor
            action_buttons_box.pack_start(add_button, False, False, 0)
            action_buttons_box.pack_start(edit_button, False, False, 0)
            action_buttons_box.pack_start(delete_button, False, False, 0)
            
            # Añadir elementos al sidebar_header en el orden correcto
            sidebar_header.pack_start(title_label, False, False, 0)
            sidebar_header.pack_start(subtitle_label, False, False, 0)
            
            # Añadir sidebar_header al sidebar
            sidebar.pack_start(sidebar_header, False, False, 0)
            sidebar.pack_start(action_buttons_box, False, False, 0)
          
            # Contenedor de categorías (scrollable)
            categories_scroll = Gtk.ScrolledWindow()
            categories_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            
            self.categories_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.categories_box.get_style_context().add_class("categories-box")
            
            categories_scroll.add(self.categories_box)
            sidebar.pack_start(categories_scroll, True, True, 0)
            
            # Panel principal
            main_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            main_panel.get_style_context().add_class("main-panel")
            
            # Barra de herramientas
            toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            toolbar.get_style_context().add_class("toolbar")

            # Botón de menú
            menu_button = Gtk.Button()
            menu_button.set_image(Gtk.Image.new_from_icon_name("open-menu", Gtk.IconSize.BUTTON))
            menu_button.get_style_context().add_class("menu-button")

            # Crear menú popover
            self.popover = Gtk.Popover()
            self.popover.set_relative_to(menu_button)

            popover_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            popover_box.set_margin_top(10)
            popover_box.set_margin_bottom(10)
            popover_box.set_margin_start(10)
            popover_box.set_margin_end(10)
            popover_box.set_spacing(10)

            config_button = Gtk.ModelButton()
            config_button.set_label("Configuración")
            config_button.connect("clicked", self.on_config_clicked)

            about_button = Gtk.ModelButton()
            about_button.set_label("Acerca de Dexter Organizer")
            about_button.connect("clicked", self.on_about_clicked)

            popover_box.pack_start(config_button, False, False, 0)
            popover_box.pack_start(about_button, False, False, 0)

            self.popover.add(popover_box)
            menu_button.connect("clicked", self.on_menu_clicked)

            # Añadir botones al header
            headerbar.pack_end(menu_button)
            headerbar.pack_end(switch_box)
            
            # Panel de contenido
            self.content_panel = Gtk.Stack()
            self.content_panel.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.content_panel.set_transition_duration(200)
            
            # Página de bienvenida
            welcome_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            welcome_page.set_halign(Gtk.Align.CENTER)
            welcome_page.set_valign(Gtk.Align.CENTER)
            
            welcome_label = Gtk.Label()
            welcome_label.set_markup("<span size='xx-large'>Bienvenido a Dexter Organizer</span>")
            welcome_label.set_margin_bottom(20)
            
            info_label = Gtk.Label(label="Utilice el botón Añadir para crear nuevas categorías y documentos.")
            
            welcome_page.pack_start(welcome_label, False, False, 0)
            welcome_page.pack_start(info_label, False, False, 0)
            
            self.content_panel.add_named(welcome_page, "welcome")
            
            # Página de Configuración
            config_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            config_page.set_margin_top(20)
            config_page.set_margin_bottom(20)
            config_page.set_margin_start(20)
            config_page.set_margin_end(20)

            config_title = Gtk.Label()
            config_title.set_markup("<span size='xx-large'>Configuración de Dexter Organizer</span>")
            config_title.set_halign(Gtk.Align.START)
            config_title.set_margin_bottom(20)

            # Notebook para pestañas
            config_notebook = Gtk.Notebook()

            # Pestaña de Backup
            backup_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            backup_page.set_spacing(15)
            backup_page.set_margin_top(15)
            backup_page.set_margin_bottom(15)
            backup_page.set_margin_start(15)
            backup_page.set_margin_end(15)

            backup_label = Gtk.Label()
            backup_label.set_markup("<span size='large'>Copia de seguridad</span>")
            backup_label.set_halign(Gtk.Align.START)
            backup_label.set_margin_bottom(10)

            backup_info = Gtk.Label(
                label="Puede crear una copia de seguridad de sus categorías y documentos, "
                     "o restaurar una copia previamente realizada."
            )
            backup_info.set_line_wrap(True)
            backup_info.set_halign(Gtk.Align.START)
            backup_info.set_margin_bottom(20)

            # Botones de backup y restore
            backup_button = Gtk.Button(label="Crear copia de seguridad")
            backup_button.set_margin_bottom(10)
            backup_button.connect("clicked", self.on_create_backup_clicked)

            restore_button = Gtk.Button(label="Restaurar copia de seguridad")
            restore_button.connect("clicked", self.on_restore_backup_clicked)

            backup_page.pack_start(backup_label, False, False, 0)
            backup_page.pack_start(backup_info, False, False, 0)
            backup_page.pack_start(backup_button, False, False, 0)
            backup_page.pack_start(restore_button, False, False, 0)

            # Añadir pestaña
            config_notebook.append_page(backup_page, Gtk.Label(label="Copias de seguridad"))

            config_page.pack_start(config_title, False, False, 0)
            config_page.pack_start(config_notebook, True, True, 0)
            
            # Botón para volver a la pantalla principal
            back_button_config = Gtk.Button(label="Volver")
            back_button_config.connect("clicked", lambda w: self.content_panel.set_visible_child_name("welcome"))
            back_button_config.set_halign(Gtk.Align.END)
            back_button_config.set_margin_top(5)
            config_page.pack_start(back_button_config, False, False, 0)

            # Página Acerca de
            about_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            about_page.set_margin_top(20)
            about_page.set_margin_bottom(20)
            about_page.set_margin_start(20)
            about_page.set_margin_end(20)

            about_title = Gtk.Label()
            about_title.set_markup("<span size='xx-large'>Acerca de Dexter Organizer</span>")
            about_title.set_halign(Gtk.Align.START)
            about_title.set_margin_bottom(20)

            # Información sobre la aplicación
            about_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            about_box.set_spacing(10)
            about_box.set_halign(Gtk.Align.CENTER)
            about_box.set_valign(Gtk.Align.CENTER)

            # Logo
            try:
                logo = Gtk.Image.new_from_icon_name("dexter-organizer", Gtk.IconSize.DIALOG)
                logo.set_pixel_size(128)
                about_box.pack_start(logo, False, False, 10)
            except Exception:
                pass  # Si no se puede cargar el logo, continuamos sin él

            app_name = Gtk.Label()
            app_name.set_markup("<span size='x-large'>Dexter Organizer</span>")
            about_box.pack_start(app_name, False, False, 0)

            version = Gtk.Label(label="Versión 1.0")
            about_box.pack_start(version, False, False, 0)

            author = Gtk.Label(label="Desarrollado por Víctor Oubiña Faubel")
            about_box.pack_start(author, False, False, 5)

            email = Gtk.Label()
            email.set_markup("<a href='mailto:oubinav78@gmail.com'>oubinav78@gmail.com</a>")
            about_box.pack_start(email, False, False, 0)

            website = Gtk.Label()
            website.set_markup("<a href='https://sourceforge.net/projects/dexter-gnome/'>Proyecto Dexter</a>")
            about_box.pack_start(website, False, False, 5)

            description = Gtk.Label(label="Aplicación para organización de documentos")
            description.set_line_wrap(True)
            description.set_max_width_chars(60)
            about_box.pack_start(description, False, False, 10)

            about_page.pack_start(about_title, False, False, 0)
            about_page.pack_start(about_box, True, True, 0)
            
            # Botón para volver a la pantalla principal
            back_button_about = Gtk.Button(label="Volver")
            back_button_about.connect("clicked", lambda w: self.content_panel.set_visible_child_name("welcome"))
            back_button_about.set_halign(Gtk.Align.END)
            back_button_about.set_margin_top(5)
            about_page.pack_start(back_button_about, False, False, 0)

            # Añadir las páginas al panel de contenido
            self.content_panel.add_named(config_page, "config")
            self.content_panel.add_named(about_page, "about")
            
            # Área de texto para editar documentos
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
            
            save_button = Gtk.Button(label="Guardar")
            save_button.connect("clicked", self.on_save_document)
            save_button.get_style_context().add_class("save-button")
            
            self.doc_toolbar.pack_start(self.view_mode_button, False, False, 0)
            self.doc_toolbar.pack_end(save_button, False, False, 0)
            
            self.document_container.pack_start(self.doc_toolbar, False, False, 0)
            self.document_container.pack_start(self.document_view_stack, True, True, 0)
            
            # Añadir al panel principal
            main_panel.pack_start(toolbar, False, False, 0)
            main_panel.pack_start(self.content_panel, True, True, 0)
            
            # Añadir paneles al layout principal
            main_box.pack_start(sidebar, False, False, 0)
            main_box.pack_start(main_panel, True, True, 0)
            
            # Cargar categorías
            self.load_categories()
            
            # Mostrar todo
            self.window.show_all()
            
            # Ocultar el botón de guardar inicialmente
            save_button.set_visible(False)
            self.doc_toolbar.set_visible(False)

    def on_theme_switch_activated(self, switch, gparam):
        self.dark_theme = switch.get_active()
        self.load_css_theme()

    def load_css_theme(self):
        css_provider = Gtk.CssProvider()
        css_file = "dexter_dark.css" if self.dark_theme else "dexter_light.css"
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", css_file)
        css_provider.load_from_path(path)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.categories = data.get('categories', {})
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error al cargar datos: {e}")
                self.categories = {}
        else:
            self.categories = {}
            self.save_data()
    
    def save_data(self):
        try:
            with open(self.data_file, 'w') as f:
                json.dump({'categories': self.categories}, f, indent=4)
        except IOError as e:
            print(f"Error al guardar datos: {e}")
    
    def load_categories(self):
        # Limpiar el panel de categorías
        for child in self.categories_box.get_children():
            self.categories_box.remove(child)
        
        # Añadir las categorías
        for category_name in sorted(self.categories.keys()):
            self.add_category_to_sidebar(category_name)
        
        # Mostrar todos los widgets
        self.categories_box.show_all()
    
    def add_category_to_sidebar(self, category_name):
        category_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        category_box.get_style_context().add_class("category-box")
        
        # Botón principal de categoría
        category_button = Gtk.Button()
        category_button.set_relief(Gtk.ReliefStyle.NONE)
        category_button.get_style_context().add_class("category-button")
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        # Añadir icono de expansión
        expander_icon = Gtk.Image.new_from_icon_name("pan-end-symbolic", Gtk.IconSize.MENU)
        button_box.pack_start(expander_icon, False, False, 5)
        
        # Etiqueta de categoría
        label = Gtk.Label(label=category_name)
        label.set_halign(Gtk.Align.START)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        
        button_box.pack_start(label, True, True, 5)
        
        category_button.add(button_box)
        
        # Lista de documentos
        documents_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        documents_box.get_style_context().add_class("documents-box")
        documents_box.set_margin_start(4)
        
        # Añadir documentos
        for doc_id, doc_info in self.categories[category_name].items():
            doc_button = Gtk.Button()
            doc_button.set_relief(Gtk.ReliefStyle.NONE)
            doc_button.get_style_context().add_class("document-button")
            
            doc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            
            # Etiqueta de documento (sin icono)
            doc_label = Gtk.Label(label=doc_info['name'])
            doc_label.set_halign(Gtk.Align.START)
            doc_label.set_ellipsize(Pango.EllipsizeMode.END)
        
            doc_box.pack_start(doc_label, True, True, 5)
            
            doc_button.add(doc_box)
            doc_button.connect("clicked", self.on_document_clicked, category_name, doc_id)
        
            documents_box.pack_start(doc_button, False, False, 0)
        
        # Estado inicial: documentos ocultos, excepto si es la categoría seleccionada
        is_expanded = (category_name == self.current_category)
        documents_box.set_visible(is_expanded)
        
        # Si está expandida, mostrar icono de expansión adecuado
        if is_expanded:
            expander_icon.set_from_icon_name("pan-down-symbolic", Gtk.IconSize.MENU)
        
        # Función para manejar la expansión/contracción
        def on_category_toggled(button):
            # Cambiar visibilidad de los documentos
            documents_visible = documents_box.get_visible()
            documents_box.set_visible(not documents_visible)
            
            # Cambiar icono de expansión
            if documents_visible:
                expander_icon.set_from_icon_name("pan-end-symbolic", Gtk.IconSize.MENU)
            else:
                expander_icon.set_from_icon_name("pan-down-symbolic", Gtk.IconSize.MENU)
        
            # Establecer esta categoría como la seleccionada actualmente
            self.current_category = category_name
            self.current_document = None
        
            # Actualizar la visualización de la categoría seleccionada
            self.update_selected_category(category_name)
        
            # Al expandir/contraer, también navegar a la categoría
            self.on_category_clicked(None, category_name)
        
        # Conectar señal
        category_button.connect("clicked", on_category_toggled)
        
        # Añadir al panel lateral
        category_box.pack_start(category_button, False, False, 0)
        category_box.pack_start(documents_box, False, False, 0)
        
        self.categories_box.pack_start(category_box, False, False, 0)
    
    def on_category_clicked(self, button, category_name):
        # Establecer la categoría actual y quitar documento actual
        self.current_category = category_name
        self.current_document = None
        
        # Actualizar la visualización de la categoría seleccionada
        self.update_selected_category(category_name)
        
        # Crear una página para mostrar los documentos de la categoría
        category_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        category_page.set_margin_top(20)
        category_page.set_margin_bottom(20)
        category_page.set_margin_start(20)
        category_page.set_margin_end(20)
        
        # Título de la categoría
        title_label = Gtk.Label()
        title_label.set_markup(f"<span size='xx-large'>{category_name}</span>")
        title_label.set_halign(Gtk.Align.START)
        title_label.set_margin_bottom(20)
        
        category_page.pack_start(title_label, False, False, 0)
        
        # Lista de documentos en formato de grid
        docs_grid = Gtk.FlowBox()
        docs_grid.set_valign(Gtk.Align.START)
        docs_grid.set_max_children_per_line(4)
        docs_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        docs_grid.set_column_spacing(20)
        docs_grid.set_row_spacing(20)
        
        for doc_id, doc_info in self.categories[category_name].items():
            # Crear un botón para cada documento
            doc_button = Gtk.Button()
            doc_button.set_relief(Gtk.ReliefStyle.NONE)
            doc_button.get_style_context().add_class("document-grid-item")
            
            doc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            doc_box.set_spacing(10)
            
            doc_label = Gtk.Label(label=doc_info['name'])
            
            doc_box.pack_start(doc_label, False, False, 0)
            
            doc_button.add(doc_box)
            doc_button.connect("clicked", self.on_document_clicked, category_name, doc_id)
            
            docs_grid.add(doc_button)
        
        # Scrollable para la grid
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(docs_grid)
        
        category_page.pack_start(scroll, True, True, 0)
        
        # Añadir un datos específicos a la página para identificar que es una página de categoría
        category_page.set_data("category", category_name)
        
        # Añadir y mostrar la página
        if self.content_panel.get_child_by_name(f"category_{category_name}"):
            self.content_panel.remove(self.content_panel.get_child_by_name(f"category_{category_name}"))
    
        self.content_panel.add_named(category_page, f"category_{category_name}")
        self.content_panel.set_visible_child_name(f"category_{category_name}")
    
        # Asegurar que la categoría sigue seleccionada
        self.current_category = category_name
    
    def on_document_clicked(self, button, category_name, doc_id):
        print(f"Documento seleccionado: {category_name} - {doc_id}")
    
        self.current_category = category_name
        self.current_document = doc_id
        self.edit_mode = False
        
        # Actualizar la visualización de la categoría y documento seleccionados
        self.update_selected_document(category_name, doc_id)
    
        doc_info = self.categories[category_name][doc_id]
        doc_path = os.path.join(self.documents_path, doc_id)
        
        # Leer el contenido del documento
        try:
            with open(doc_path, 'r') as f:
                content = f.read()
            print(f"Contenido del documento: {content[:100]}...")
        except IOError:
            print(f"Error al leer el documento: {e}")
            content = ""
        
        # Configurar el área de texto
        self.text_buffer.set_text(content)
        self.text_view.set_editable(False)
        
        # Configurar el botón de modo de vista
        is_html = doc_info['type'] == 'html'
        self.view_mode_button.set_sensitive(is_html)
        
        # Mostrar en modo texto por defecto
        self.document_view_stack.set_visible_child_name("text")
        
        # Si es HTML, también cargar en webview
        if is_html:
            self.web_view.load_html(content, None)
        
        # Mostrar la barra de herramientas del documento
        self.doc_toolbar.set_visible(True)
        
        # Botón guardar no visible en modo lectura
        for child in self.doc_toolbar.get_children():
            if isinstance(child, Gtk.Button) and child.get_label() == "Guardar":
                child.set_visible(False)
        
        # Añadir y mostrar el contenedor de documento
        if self.content_panel.get_child_by_name("document_view"):
            self.content_panel.remove(self.content_panel.get_child_by_name("document_view"))
        
        self.content_panel.add_named(self.document_container, "document_view")
        self.content_panel.set_visible_child_name("document_view")
        
        print("Documento mostrado en el contenedor")
    
    def toggle_view_mode(self, button):
        current_mode = self.document_view_stack.get_visible_child_name()
        
        if current_mode == "text":
            self.document_view_stack.set_visible_child_name("web")
            button.set_label("Vista Código")
        else:
            self.document_view_stack.set_visible_child_name("text")
            button.set_label("Vista Web")
    
    def on_add_clicked(self, button):
        # Diálogo para añadir nuevo documento o categoría
        dialog = Gtk.Dialog(
            title="Añadir",
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL,
            buttons=(
                "Cancelar", Gtk.ResponseType.CANCEL,
                "Aceptar", Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(450, 300)
        dialog.get_style_context().add_class("dialog")
        
        content_area = dialog.get_content_area()
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_start(10)
        content_area.set_margin_end(10)
        content_area.set_spacing(10)
        
        # Crear un notebook para las pestañas
        notebook = Gtk.Notebook()
        notebook.set_tab_pos(Gtk.PositionType.TOP)
        
        # Página para añadir categoría
        category_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        category_page.set_margin_top(15)
        category_page.set_margin_bottom(15)
        category_page.set_margin_start(15)
        category_page.set_margin_end(15)
        category_page.set_spacing(15)
        
        category_label = Gtk.Label(label="Nombre de la categoría:")
        category_label.set_halign(Gtk.Align.START)
    
        category_entry = Gtk.Entry()
        category_entry.set_activates_default(True)
    
        category_page.pack_start(category_label, False, False, 0)
        category_page.pack_start(category_entry, False, False, 0)
        
        # Página para añadir documento
        document_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        document_page.set_margin_top(15)
        document_page.set_margin_bottom(15)
        document_page.set_margin_start(15)
        document_page.set_margin_end(15)
        document_page.set_spacing(15)
    
        doc_name_label = Gtk.Label(label="Nombre del documento:")
        doc_name_label.set_halign(Gtk.Align.START)
    
        doc_name_entry = Gtk.Entry()
        doc_name_entry.set_activates_default(True)
        
        # Selector de categoría
        category_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        category_box.set_spacing(5)
    
        category_selector_label = Gtk.Label(label="Categoría:")
        category_selector_label.set_halign(Gtk.Align.START)
        
        category_combo = Gtk.ComboBoxText()
        for category in sorted(self.categories.keys()):
            category_combo.append_text(category)
    
        if len(self.categories) > 0:
            category_combo.set_active(0)
    
        new_category_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        new_category_box.set_spacing(10)
    
        new_category_label = Gtk.Label(label="Nueva categoría:")
        new_category_entry = Gtk.Entry()
    
        new_category_box.pack_start(new_category_label, False, False, 0)
        new_category_box.pack_start(new_category_entry, True, True, 0)
    
        category_box.pack_start(category_selector_label, False, False, 0)
        category_box.pack_start(category_combo, False, False, 0)
        category_box.pack_start(new_category_box, False, False, 0)
        
        # Selector de tipo de documento
        type_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        type_box.set_spacing(5)
        type_box.set_margin_top(10)
    
        type_label = Gtk.Label(label="Tipo de documento:")
        type_label.set_halign(Gtk.Align.START)
    
        type_combo = Gtk.ComboBoxText()
        type_combo.append_text("Texto (.txt)")
        type_combo.append_text("Markdown (.md)")
        type_combo.append_text("HTML (.html)")
        type_combo.set_active(0)
    
        type_box.pack_start(type_label, False, False, 0)
        type_box.pack_start(type_combo, False, False, 0)
    
        # Añadir widgets a la página de documento
        document_page.pack_start(doc_name_label, False, False, 0)
        document_page.pack_start(doc_name_entry, False, False, 0)
        document_page.pack_start(category_box, False, False, 0)
        document_page.pack_start(type_box, False, False, 0)
    
        # Estado inicial - ocultar opción de nueva categoría
        new_category_box.set_visible(False)
        
        # Añadir pestañas al notebook
        category_tab_label = Gtk.Label(label="Categoría")
        document_tab_label = Gtk.Label(label="Documento")
    
        notebook.append_page(category_page, category_tab_label)
        notebook.append_page(document_page, document_tab_label)
    
        # Añadir notebook al diálogo
        content_area.pack_start(notebook, True, True, 0)
    
        # Conectar señales
        def on_category_changed(widget):
            # Mostrar campo de nueva categoría si se selecciona "Nueva categoría"
            text = category_combo.get_active_text()
            if text == "Nueva categoría":
                new_category_box.set_visible(True)
            else:
                new_category_box.set_visible(False)
        
        # Añadir opción "Nueva categoría" si hay categorías
        if len(self.categories) > 0:
            category_combo.append_text("Nueva categoría")
            category_combo.connect("changed", on_category_changed)
    
        dialog.show_all()
    
        # Hacer que el botón "Aceptar" sea el predeterminado
        dialog.set_default_response(Gtk.ResponseType.OK)
    
        # Correr el diálogo
        response = dialog.run()
    
        if response == Gtk.ResponseType.OK:
            # Obtener la pestaña activa
            current_page = notebook.get_current_page()
        
            if current_page == 0:  # Pestaña de Categoría
                category_name = category_entry.get_text().strip()
            
                if category_name:
                    if category_name not in self.categories:
                        self.categories[category_name] = {}
                        self.save_data()
                        self.load_categories()
                    else:
                        self.show_error_dialog("La categoría ya existe.")
                else:
                    self.show_error_dialog("Nombre de categoría vacío.")
                
            else:  # Pestaña de Documento
                doc_name = doc_name_entry.get_text().strip()
            
                if doc_name:
                    doc_type_idx = type_combo.get_active()
                    doc_type = ["txt", "md", "html"][doc_type_idx]
                
                    # Determinar la categoría
                    if len(self.categories) > 0:
                        selected_category = category_combo.get_active_text()
                    
                        if selected_category == "Nueva categoría":
                            new_cat_name = new_category_entry.get_text().strip()
                            if new_cat_name:
                                if new_cat_name not in self.categories:
                                    self.categories[new_cat_name] = {}
                                    selected_category = new_cat_name
                                else:
                                    self.show_error_dialog("La categoría ya existe.")
                                    dialog.destroy()
                                    return
                            else:
                                self.show_error_dialog("Nombre de categoría vacío.")
                                dialog.destroy()
                                return
                    else:
                        # Si no hay categorías, crear una con el nombre "Documentos"
                        selected_category = "Documentos"
                        self.categories[selected_category] = {}
                
                    # Crear el documento
                    doc_id = f"{doc_name.lower().replace(' ', '_')}_{GLib.get_monotonic_time()}"
                    self.categories[selected_category][doc_id] = {
                        'name': doc_name,
                        'type': doc_type,
                        'created': GLib.get_monotonic_time()
                    }
                
                    # Crear archivo físico
                    doc_path = os.path.join(self.documents_path, doc_id)
                    with open(doc_path, 'w') as f:
                        f.write("")
                
                    self.save_data()
                    self.load_categories()
                
                    # Abrir el documento creado
                    self.current_category = selected_category
                    self.current_document = doc_id
                    self.on_document_clicked(None, selected_category, doc_id)
                    self.on_edit_clicked(None)  # Iniciar en modo edición
                else:
                    self.show_error_dialog("Nombre de documento vacío.")
    
        dialog.destroy()
    
    def on_edit_clicked(self, button):
        if self.current_document and self.current_category:
            self.edit_mode = True
            self.text_view.set_editable(True)
            
            # Mostrar botón guardar
            for child in self.doc_toolbar.get_children():
                if isinstance(child, Gtk.Button) and child.get_label() == "Guardar":
                    child.set_visible(True)
    
    def on_save_document(self, button):
        if self.current_document and self.current_category:
            # Obtener contenido actualizado
            start, end = self.text_buffer.get_bounds()
            content = self.text_buffer.get_text(start, end, True)
            
            # Guardar contenido
            doc_path = os.path.join(self.documents_path, self.current_document)
            try:
                with open(doc_path, 'w') as f:
                    f.write(content)
                
                # Si es HTML, actualizar la vista web
                doc_info = self.categories[self.current_category][self.current_document]
                if doc_info['type'] == 'html':
                    self.web_view.load_html(content, None)
                
                # Volver a modo lectura
                self.edit_mode = False
                self.text_view.set_editable(False)
                
                # Ocultar botón guardar
                for child in self.doc_toolbar.get_children():
                    if isinstance(child, Gtk.Button) and child.get_label() == "Guardar":
                        child.set_visible(False)
            except IOError as e:
                self.show_error_dialog(f"Error al guardar: {e}")
    
    def on_delete_clicked(self, button):
        if self.current_category:
            if self.current_document:
                # Eliminar documento
                self.delete_document()
            else:
                # Eliminar categoría directamente sin verificar la página actual
                self.delete_category()
        else:
            self.show_info_dialog("Para eliminar, primero seleccione una categoría o documento.")

    def show_info_dialog(self, message):
        """Muestra un diálogo informativo"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()
    
    def delete_document(self):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"¿Está seguro de que desea eliminar el documento {self.categories[self.current_category][self.current_document]['name']}?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Eliminar físicamente el archivo
            doc_path = os.path.join(self.documents_path, self.current_document)
            try:
                if os.path.exists(doc_path):
                    os.remove(doc_path)
            except OSError as e:
                print(f"Error al eliminar archivo: {e}")
            
            # Eliminar de los datos
            del self.categories[self.current_category][self.current_document]
            self.save_data()
            
            # Recargar la interfaz
            self.load_categories()
            
            # Mostrar la vista de categoría
            self.on_category_clicked(None, self.current_category)
            self.current_document = None
    
    def delete_category(self):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"¿Está seguro de que desea eliminar la categoría {self.current_category} y todos sus documentos?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Eliminar físicamente todos los archivos de la categoría
            for doc_id in self.categories[self.current_category]:
                doc_path = os.path.join(self.documents_path, doc_id)
                try:
                    if os.path.exists(doc_path):
                        os.remove(doc_path)
                except OSError as e:
                    print(f"Error al eliminar archivo: {e}")
            
            # Eliminar la categoría
            del self.categories[self.current_category]
            self.save_data()
            
            # Recargar la interfaz
            self.load_categories()
            
            # Mostrar pantalla de bienvenida
            self.content_panel.set_visible_child_name("welcome")
            self.current_category = None
            self.current_document = None
    
    def toggle_theme(self, button):
        # Cargar proveedores de CSS
        css_provider_light = Gtk.CssProvider()
        css_provider_dark = Gtk.CssProvider()
    
        # Rutas a los archivos CSS de temas
        css_light_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "dexter_light.css")
        css_dark_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "dexter_dark.css")
    
        # Obtener el contexto de estilo actual
        screen = Gdk.Screen.get_default()
    
        try:
            # Cargar los archivos CSS
            css_provider_light.load_from_path(css_light_file)
            css_provider_dark.load_from_path(css_dark_file)
        
            # Obtener la configuración actual de temas
            settings = Gtk.Settings.get_default()

            if button.get_active():
                # Cambiar a tema oscuro
                settings.set_property("gtk-application-prefer-dark-theme", True)
                Gtk.StyleContext.remove_provider_for_screen(screen, css_provider_light)
                Gtk.StyleContext.add_provider_for_screen(screen, css_provider_dark, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            else:
                # Cambiar a tema claro
                settings.set_property("gtk-application-prefer-dark-theme", False)
                Gtk.StyleContext.remove_provider_for_screen(screen, css_provider_dark)
                Gtk.StyleContext.add_provider_for_screen(screen, css_provider_light, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
        except Exception as e:
            print(f"Error al cambiar el tema: {e}")
    
    def on_menu_clicked(self, button):
        # Asegurarse de que el popover esté visible y se muestre correctamente
        self.popover.show_all()
        self.popover.popup()
    
    def on_config_clicked(self, button):
        self.popover.popdown()
        self.content_panel.set_visible_child_name("config")
    
    def on_about_clicked(self, button):
        self.popover.popdown()
        self.content_panel.set_visible_child_name("about")
        
    def on_create_backup_clicked(self, button):
        file_chooser = Gtk.FileChooserDialog(
            title="Guardar copia de seguridad",
            parent=self.window,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            buttons=(
                "Cancelar", Gtk.ResponseType.CANCEL,
                "Guardar", Gtk.ResponseType.ACCEPT
            )
        )
        
        file_chooser.set_default_size(800, 600)
        
        response = file_chooser.run()
        
        if response == Gtk.ResponseType.ACCEPT:
            folder_path = file_chooser.get_filename()
            file_chooser.destroy()
            
            # Mostrar diálogo de progreso
            progress_dialog = Gtk.Dialog(
                title="Creando copia de seguridad",
                parent=self.window,
                flags=Gtk.DialogFlags.MODAL
            )
            progress_dialog.set_default_size(300, 100)
            
            content_area = progress_dialog.get_content_area()
            content_area.set_margin_top(15)
            content_area.set_margin_bottom(15)
            content_area.set_margin_start(15)
            content_area.set_margin_end(15)
            content_area.set_spacing(10)
            
            label = Gtk.Label(label="Creando copia de seguridad, por favor espere...")
            progress_bar = Gtk.ProgressBar()
            progress_bar.pulse()
            
            content_area.pack_start(label, False, False, 0)
            content_area.pack_start(progress_bar, False, False, 0)
            
            progress_dialog.show_all()
            
            # Realizar backup en segundo plano
            def backup_task():
                backup_path = self.create_backup(folder_path)
                
                GLib.idle_add(progress_dialog.destroy)
                
                if backup_path:
                    GLib.idle_add(self.show_success_dialog, f"Copia de seguridad creada correctamente en:\n{backup_path}")
                else:
                    GLib.idle_add(self.show_error_dialog, "Error al crear la copia de seguridad.")
                
                return False
            
            # Mantener el progreso animado
            def pulse_progress():
                progress_bar.pulse()
                return True
            
            # Iniciar animación
            GLib.timeout_add(100, pulse_progress)
            
            # Iniciar tarea en segundo plano
            GLib.idle_add(backup_task)
        else:
            file_chooser.destroy()

    def on_restore_backup_clicked(self, button):
        file_chooser = Gtk.FileChooserDialog(
            title="Seleccionar copia de seguridad",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                "Cancelar", Gtk.ResponseType.CANCEL,
                "Abrir", Gtk.ResponseType.ACCEPT
            )
        )
        
        file_chooser.set_default_size(800, 600)
        
        # Filtro para archivos zip
        filter_zip = Gtk.FileFilter()
        filter_zip.set_name("Archivos ZIP")
        filter_zip.add_pattern("*.zip")
        file_chooser.add_filter(filter_zip)
        
        response = file_chooser.run()
        
        if response == Gtk.ResponseType.ACCEPT:
            backup_path = file_chooser.get_filename()
            file_chooser.destroy()
            
            # Confirmar restauración
            confirm_dialog = Gtk.MessageDialog(
                transient_for=self.window,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text="¿Está seguro de que desea restaurar esta copia de seguridad?"
            )
            confirm_dialog.format_secondary_text(
                "Esta acción reemplazará todas las categorías y documentos actuales. "
                "Los datos no se podrán recuperar una vez realizada la restauración."
            )
            
            confirm_response = confirm_dialog.run()
            confirm_dialog.destroy()
            
            if confirm_response == Gtk.ResponseType.YES:
                # Mostrar diálogo de progreso
                progress_dialog = Gtk.Dialog(
                    title="Restaurando copia de seguridad",
                    parent=self.window,
                    flags=Gtk.DialogFlags.MODAL
                )
                progress_dialog.set_default_size(300, 100)
                
                content_area = progress_dialog.get_content_area()
                content_area.set_margin_top(15)
                content_area.set_margin_bottom(15)
                content_area.set_margin_start(15)
                content_area.set_margin_end(15)
                content_area.set_spacing(10)
                
                label = Gtk.Label(label="Restaurando copia de seguridad, por favor espere...")
                progress_bar = Gtk.ProgressBar()
                progress_bar.pulse()
                
                content_area.pack_start(label, False, False, 0)
                content_area.pack_start(progress_bar, False, False, 0)
                
                progress_dialog.show_all()
                
                # Realizar restauración en segundo plano
                def restore_task():
                    success = self.restore_backup(backup_path)
                    
                    GLib.idle_add(progress_dialog.destroy)
                    
                    if success:
                        GLib.idle_add(self.show_success_dialog, "Copia de seguridad restaurada correctamente.")
                    else:
                        GLib.idle_add(self.show_error_dialog, "Error al restaurar la copia de seguridad.")
                    
                    return False
                
                # Mantener el progreso animado
                def pulse_progress():
                    progress_bar.pulse()
                    return True
                
                # Iniciar animación
                GLib.timeout_add(100, pulse_progress)
                
                # Iniciar tarea en segundo plano
                GLib.idle_add(restore_task)
        else:
            file_chooser.destroy()
    
    def create_backup(self, path):
        """Crea un backup de los datos y documentos"""
        import shutil
        import time
        
        timestamp = time.strftime("%d-%m-%Y")
        backup_filename = f"Backup-Dexter-Organizer-{timestamp}.zip"
        backup_path = os.path.join(path, backup_filename)
        
        try:
            import zipfile
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Añadir archivo data.json
                zipf.write(self.data_file, os.path.basename(self.data_file))
                
                # Añadir documentos
                for category_name, docs in self.categories.items():
                    for doc_id in docs:
                        doc_path = os.path.join(self.documents_path, doc_id)
                        if os.path.exists(doc_path):
                            zipf.write(doc_path, os.path.join('documents', doc_id))
            
            return backup_path
        except Exception as e:
            print(f"Error al crear backup: {e}")
            return None
    
    def restore_backup(self, backup_path):
        """Restaura un backup de los datos y documentos"""
        import zipfile
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Extraer en un directorio temporal
                import tempfile
                temp_dir = tempfile.mkdtemp()
                zipf.extractall(temp_dir)
                
                # Restaurar data.json
                data_file_temp = os.path.join(temp_dir, os.path.basename(self.data_file))
                if os.path.exists(data_file_temp):
                    with open(data_file_temp, 'r') as f:
                        data = json.load(f)
                        self.categories = data.get('categories', {})
                    
                    # Copiar a ubicación final
                    import shutil
                    shutil.copy2(data_file_temp, self.data_file)
                
                # Restaurar documentos
                docs_dir_temp = os.path.join(temp_dir, 'documents')
                if os.path.exists(docs_dir_temp):
                    for doc_id in os.listdir(docs_dir_temp):
                        doc_path_temp = os.path.join(docs_dir_temp, doc_id)
                        doc_path_final = os.path.join(self.documents_path, doc_id)
                        shutil.copy2(doc_path_temp, doc_path_final)
                
                # Limpiar
                shutil.rmtree(temp_dir)
                
                # Recargar UI
                self.load_categories()
                self.content_panel.set_visible_child_name("welcome")
                self.current_category = None
                self.current_document = None
                
                return True
        except Exception as e:
            print(f"Error al restaurar backup: {e}")
            return False
    
    def update_selected_category(self, category_name):
        """Actualiza la visualización de la categoría seleccionada"""
        # Recorrer todas las categorías y quitar la clase 'selected'
        for category_box in self.categories_box.get_children():
            # El primer hijo de category_box debería ser el botón de categoría
            for child in category_box.get_children():
                if isinstance(child, Gtk.Button):
                    child.get_style_context().remove_class("selected")
                    # También eliminar selección de todos los documentos
                    if len(category_box.get_children()) > 1:
                        docs_box = category_box.get_children()[1]
                        for doc_button in docs_box.get_children():
                            doc_button.get_style_context().remove_class("selected")
        
        # Ahora marcar la categoría seleccionada
        for category_box in self.categories_box.get_children():
            for child in category_box.get_children():
                if isinstance(child, Gtk.Button):
                    # Verificar si esta es la categoría que queremos marcar
                    label_widget = None
                    for button_child in child.get_children():
                        if isinstance(button_child, Gtk.Box):
                            for box_child in button_child.get_children():
                                if isinstance(box_child, Gtk.Label) and box_child.get_text() == category_name:
                                    label_widget = box_child
                                    break
                    
                    if label_widget:
                        child.get_style_context().add_class("selected")
                        break

    def update_selected_document(self, category_name, doc_id):
        """Actualiza la visualización del documento seleccionado"""
        # Primero actualizar la categoría seleccionada
        self.update_selected_category(category_name)
        
        # Ahora buscar y marcar el documento seleccionado
        for category_box in self.categories_box.get_children():
            for child in category_box.get_children():
                if isinstance(child, Gtk.Button):
                    # Verificar si esta es la categoría correcta
                    is_correct_category = False
                    for button_child in child.get_children():
                        if isinstance(button_child, Gtk.Box):
                            for box_child in button_child.get_children():
                                if isinstance(box_child, Gtk.Label) and box_child.get_text() == category_name:
                                    is_correct_category = True
                                    break
                    
                    if is_correct_category and len(category_box.get_children()) > 1:
                        # Buscar el documento en esta categoría
                        docs_box = category_box.get_children()[1]
                        for doc_button in docs_box.get_children():
                            doc_button.get_style_context().remove_class("selected")
                            
                            # Verificar si este es el documento correcto
                            doc_info = self.categories[category_name][doc_id]
                            doc_name = doc_info['name']
                            
                            for button_child in doc_button.get_children():
                                if isinstance(button_child, Gtk.Box):
                                    for box_child in button_child.get_children():
                                        if isinstance(box_child, Gtk.Label) and box_child.get_text() == doc_name:
                                            doc_button.get_style_context().add_class("selected")
                                            break
    
    def show_success_dialog(self, message):
        """Muestra un diálogo de éxito"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()
    
    def show_error_dialog(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

def main():
    app = DexterOrganizer()
    return app.run(sys.argv)

if __name__ == "__main__":
    sys.exit(main())
