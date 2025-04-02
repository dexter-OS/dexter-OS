#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pestaña para la limpieza del sistema.
Permite ejecutar tareas de limpieza basadas en archivos XML.
"""

import os
import gi
import subprocess
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Vte, GLib, Gdk, Pango

from utils.utils import _, format_bytes
from utils.cleanup_manager import CleanupManager

class CleanupTab(Gtk.Box):
    """Pestaña de limpieza del sistema"""
    
    def __init__(self, parent_window):
        """Inicializar la pestaña de limpieza"""
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.parent_window = parent_window
        self.cleanup_manager = CleanupManager()
        
        self.set_border_width(10)
        
        # Crear área de contenido principal
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.pack_start(content_box, True, True, 0)
        
        # Panel izquierdo (árbol de limpiadores)
        left_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        left_panel.set_size_request(300, -1)
        
        # Título del panel izquierdo
        left_title = Gtk.Label(label=_("Limpiadores del Sistema"))
        left_title.set_halign(Gtk.Align.START)
        left_panel.pack_start(left_title, False, False, 0)
        
        # Árbol de limpiadores
        self.create_cleaners_tree(left_panel)
        
        # Opciones adicionales
        self.create_options_box(left_panel)
        
        content_box.pack_start(left_panel, False, False, 0)
        
        # Panel derecho (terminal y controles)
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        # Título del panel derecho
        right_title = Gtk.Label(label=_("Resultados"))
        right_title.set_halign(Gtk.Align.START)
        right_panel.pack_start(right_title, False, False, 0)
        
        # Crear terminal para mostrar salida
        self.create_terminal(right_panel)
        
        # Botones de acción
        self.create_action_buttons(right_panel)
        
        content_box.pack_start(right_panel, True, True, 0)
        
        # Variables de estado
        self.selected_items = []
        self.cleaning = False
    
    def create_cleaners_tree(self, parent_box):
        """Crear el árbol de limpiadores"""
        # ScrolledWindow para el árbol
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_shadow_type(Gtk.ShadowType.IN)
        parent_box.pack_start(scrolled_window, True, True, 0)
        
        # Modelo de datos para el árbol
        self.cleaner_store = Gtk.TreeStore(bool, str, str, str, str, str)  # seleccionado, id, nombre, descripción, categoría, archivo
        
        # TreeView
        self.cleaner_tree = Gtk.TreeView(model=self.cleaner_store)
        self.cleaner_tree.set_headers_visible(True)
        
        # Columna de selección (checkbox)
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.on_cleaner_toggled)
        column_toggle = Gtk.TreeViewColumn(_(""), renderer_toggle, active=0)
        self.cleaner_tree.append_column(column_toggle)
        
        # Columna de nombre
        renderer_text = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn(_("Nombre"), renderer_text, text=2)
        column_name.set_expand(True)
        self.cleaner_tree.append_column(column_name)
        
        # Columna de categoría
        renderer_text = Gtk.CellRendererText()
        column_category = Gtk.TreeViewColumn(_("Categoría"), renderer_text, text=4)
        self.cleaner_tree.append_column(column_category)
        
        # Cargar limpiadores
        self.load_cleaners()
        
        # Conectar señal de selección
        self.cleaner_tree.connect("cursor-changed", self.on_cleaner_selected)
        
        scrolled_window.add(self.cleaner_tree)
    
    def load_cleaners(self):
        """Cargar los limpiadores desde los archivos XML de forma asíncrona"""
        self.cleaner_store.clear()
        
        # Añadir mensaje de carga
        loading_iter = self.cleaner_store.append(None, [
            False, 
            _("Cargando limpiadores..."), 
            _("Cargando limpiadores..."), 
            _("Por favor espere mientras se cargan los limpiadores disponibles"), 
            "", 
            ""])
        
        # Función para realizar la carga en segundo plano
        def load_cleaners_async():
            try:
                # Obtener todos los limpiadores
                cleaner_files = self.cleanup_manager.get_cleaner_files()
                
                # Crear un diccionario para agrupar por categoría
                categories = {}
                
                for cleaner_file in cleaner_files:
                    cleaner_info = self.cleanup_manager.parse_cleaner_file(cleaner_file["path"])
                    
                    if cleaner_info:
                        category = cleaner_info.get("category", "general")
                        
                        if category not in categories:
                            categories[category] = []
                        
                        categories[category].append(cleaner_info)
                
                # Filtrar limpiadores irrelevantes si está configurado
                filtered_categories = {}
                for category, cleaners in categories.items():
                    filtered_cleaners = self.cleanup_manager.filter_irrelevant_cleaners(cleaners)
                    if filtered_cleaners:
                        filtered_categories[category] = filtered_cleaners
                
                # Actualizar UI en el hilo principal
                GLib.idle_add(self.update_cleaner_tree, filtered_categories)
            except Exception as e:
                print(f"Error al cargar limpiadores: {e}")
                GLib.idle_add(self.show_error_message, str(e))
            
            return False
        
        # Ejecutar la carga en un timeout para dar tiempo a que la UI se actualice
        GLib.timeout_add(100, load_cleaners_async)
    
    def update_cleaner_tree(self, filtered_categories):
        """Actualizar el árbol de limpiadores con los datos cargados"""
        # Limpiar el TreeStore
        self.cleaner_store.clear()
        
        # Añadir al TreeStore agrupado por categoría
        for category, cleaners in filtered_categories.items():
            # Nodo de categoría
            category_iter = self.cleaner_store.append(None, [False, "", category, "", category, ""])
            
            for cleaner in cleaners:
                # Añadir limpiador
                cleaner_iter = self.cleaner_store.append(category_iter, [
                    False,
                    cleaner.get("label", ""),  # Cambiado a label para mostrar correctamente
                    cleaner.get("label", ""),  # Cambiado a label para mostrar correctamente
                    cleaner.get("description", ""),
                    cleaner.get("id", ""),  # Usar ID en lugar de categoría
                    cleaner.get("file", "")
                ])
                
                # Añadir opciones del limpiador
                for option in cleaner.get("options", []):
                    self.cleaner_store.append(cleaner_iter, [
                        False,
                        option.get("label", ""),
                        option.get("label", ""),
                        option.get("description", ""),
                        f"{cleaner.get('id', '')}.{option.get('id', '')}",  # Formato ID.option_id
                        ""
                    ])
        
        # Expandir todas las categorías
        self.cleaner_tree.expand_all()
        
        return False
        
    def show_error_message(self, message):
        """Mostrar mensaje de error en el árbol"""
        self.cleaner_store.clear()
        self.cleaner_store.append(None, [
            False, 
            _("Error al cargar limpiadores"), 
            _("Error al cargar limpiadores"), 
            message, 
            "", 
            ""])
        return False
    
    def create_options_box(self, parent_box):
        """Crear caja de opciones adicionales"""
        options_frame = Gtk.Frame(label=_("Opciones"))
        parent_box.pack_start(options_frame, False, False, 0)
        
        options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        options_box.set_border_width(5)
        options_frame.add(options_box)
        
        # Opción para limpieza total (incluir archivos de root)
        self.total_cleanup_check = Gtk.CheckButton(label=_("Limpieza total (incluir archivos de root)"))
        options_box.pack_start(self.total_cleanup_check, False, False, 0)
        
        # Opción para sobrescribir contenido
        self.overwrite_check = Gtk.CheckButton(label=_("Sobrescribir contenido para evitar recuperación"))
        options_box.pack_start(self.overwrite_check, False, False, 0)
        
        # Botón para eliminar kernels antiguos
        self.kernels_button = Gtk.Button(label=_("Eliminar kernels antiguos"))
        self.kernels_button.connect("clicked", self.on_remove_kernels_clicked)
        options_box.pack_start(self.kernels_button, False, False, 5)
    
    def create_terminal(self, parent_box):
        """Crear terminal para mostrar salida"""
        # Frame para la terminal
        terminal_frame = Gtk.Frame()
        parent_box.pack_start(terminal_frame, True, True, 0)
        
        # Terminal
        self.terminal = Vte.Terminal()
        self.terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)
        self.terminal.set_scroll_on_output(True)
        self.terminal.set_scrollback_lines(10000)
        
        # Establecer fuente monoespaciada
        font_desc = Pango.FontDescription("Monospace 10")
        self.terminal.set_font(font_desc)
        
        # Colores de la terminal
        self.terminal.set_color_background(Gdk.RGBA(0.0, 0.0, 0.0, 1.0))
        self.terminal.set_color_foreground(Gdk.RGBA(1.0, 1.0, 1.0, 1.0))
        
        # ScrolledWindow para la terminal
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add(self.terminal)
        
        terminal_frame.add(scrolled_window)
        
        # Mostrar mensaje inicial
        self.write_to_terminal(_("Terminal lista para mostrar operaciones de limpieza.\n"))
        self.write_to_terminal(_("Seleccione los elementos a limpiar en el panel izquierdo.\n"))
    
    def create_action_buttons(self, parent_box):
        """Crear botones de acción"""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        parent_box.pack_start(button_box, False, False, 0)
        
        # Etiqueta de información
        self.info_label = Gtk.Label()
        self.info_label.set_markup(_("Seleccione limpiadores para ver detalles"))
        button_box.pack_start(self.info_label, True, True, 0)
        
        # Botón para limpiar
        self.clean_button = Gtk.Button(label=_("Limpiar Sistema"))
        self.clean_button.connect("clicked", self.on_clean_clicked)
        self.clean_button.set_sensitive(False)
        button_box.pack_start(self.clean_button, False, False, 0)
    
    def on_cleaner_toggled(self, renderer, path):
        """Manejar cambio en la selección de un limpiador"""
        iter_path = Gtk.TreePath.new_from_string(path)
        iter = self.cleaner_store.get_iter(iter_path)
        
        if iter:
            # Cambiar estado de selección
            current_value = self.cleaner_store[iter][0]
            self.cleaner_store[iter][0] = not current_value
            
            # Si es un nodo padre, cambiar todos los hijos
            if self.cleaner_store.iter_has_child(iter):
                self.toggle_children(iter, not current_value)
            
            # Actualizar lista de comandos seleccionados
            self.update_selected_items()
    
    def toggle_children(self, parent_iter, selected):
        """Cambiar el estado de selección de todos los hijos de un nodo"""
        n_children = self.cleaner_store.iter_n_children(parent_iter)
        
        for i in range(n_children):
            child_iter = self.cleaner_store.iter_nth_child(parent_iter, i)
            
            if child_iter:
                # Cambiar estado del hijo
                self.cleaner_store[child_iter][0] = selected
                
                # Si el hijo tiene hijos, cambiarlos también
                if self.cleaner_store.iter_has_child(child_iter):
                    self.toggle_children(child_iter, selected)
    
    def update_selected_items(self):
        """Actualizar la lista de elementos seleccionados"""
        self.selected_items = []
        
        # Recorrer todo el árbol buscando elementos seleccionados
        self.collect_selected_items(None)
        
        # Actualizar interfaz
        if self.selected_items:
            # Estimar tamaño
            estimation = self.cleanup_manager.estimate_cleanup_size(
                [item["id"] for item in self.selected_items if item["type"] == "command"])
            
            # Actualizar etiqueta de información
            self.info_label.set_markup(
                _("Espacio de disco que se recuperará: <b>{0}</b> · Archivos que se eliminarán: <b>{1}</b>").format(
                    estimation["size_formatted"], estimation["files"]))
            
            # Habilitar botón de limpieza
            self.clean_button.set_sensitive(True)
        else:
            self.info_label.set_markup(_("Seleccione limpiadores para ver detalles"))
            self.clean_button.set_sensitive(False)
    
    def collect_selected_items(self, parent_iter):
        """Recolectar todos los elementos seleccionados en el árbol"""
        model = self.cleaner_store
        
        if parent_iter is None:
            # Comenzar desde la raíz
            n_children = model.iter_n_children(None)
            
            for i in range(n_children):
                child_iter = model.iter_nth_child(None, i)
                self.collect_selected_items(child_iter)
        else:
            # Verificar si este elemento está seleccionado
            if model[parent_iter][0]:  # Columna 0 = seleccionado
                item_type = "category"
                
                # Determinar el tipo de ítem
                if model[parent_iter][4] == "command":
                    item_type = "command"
                elif model.iter_parent(parent_iter) is not None:
                    parent_type = model[model.iter_parent(parent_iter)][4]
                    if parent_type != "category":
                        item_type = "cleaner"
                
                # Añadir a la lista si es un comando
                if item_type == "command":
                    self.selected_items.append({
                        "id": model[parent_iter][1],
                        "name": model[parent_iter][2],
                        "description": model[parent_iter][3],
                        "type": item_type
                    })
            
            # Procesar hijos
            if model.iter_has_child(parent_iter):
                n_children = model.iter_n_children(parent_iter)
                
                for i in range(n_children):
                    child_iter = model.iter_nth_child(parent_iter, i)
                    self.collect_selected_items(child_iter)
    
    def on_cleaner_selected(self, treeview):
        """Manejar selección de un limpiador en el árbol"""
        selection = treeview.get_selection()
        model, iter_sel = selection.get_selected()
        
        if iter_sel:
            # Mostrar descripción en la terminal
            name = model[iter_sel][2]
            description = model[iter_sel][3]
            
            self.terminal.reset(True, True)
            self.write_to_terminal(_("Seleccionado: {0}\n\n").format(name))
            
            if description:
                self.write_to_terminal(_("Descripción: {0}\n\n").format(description))
            
            # Si es un comando, mostrar más detalles
            if model[iter_sel][4] == "command":
                # Aquí se podría mostrar más información sobre las acciones del comando
                pass
    
    def on_clean_clicked(self, button):
        """Manejar clic en botón de limpiar"""
        if not self.selected_items:
            return
        
        # Mostrar diálogo de confirmación
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_("¿Ejecutar limpieza del sistema?")
        )
        
        # Obtener estimación
        command_ids = [item["id"] for item in self.selected_items if item["type"] == "command"]
        estimation = self.cleanup_manager.estimate_cleanup_size(command_ids)
        
        dialog.format_secondary_text(
            _("Se eliminarán {0} archivos liberando {1} de espacio.\n¿Desea continuar?").format(
                estimation["files"], estimation["size_formatted"]))
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Ejecutar limpieza
            self.execute_cleanup()
    
    def execute_cleanup(self):
        """Ejecutar la limpieza del sistema"""
        if self.cleaning:
            return
        
        self.cleaning = True
        
        # Deshabilitar botones durante la limpieza
        self.clean_button.set_sensitive(False)
        
        # Limpiar terminal
        self.terminal.reset(True, True)
        
        # Mostrar mensaje de inicio
        self.write_to_terminal(_("Iniciando limpieza del sistema...\n\n"))
        
        # Obtener opciones
        total_cleanup = self.total_cleanup_check.get_active()
        overwrite = self.overwrite_check.get_active()
        
        # Obtener IDs de comandos seleccionados
        command_ids = [item["id"] for item in self.selected_items if item["type"] == "command"]
        
        # Ejecutar limpieza en segundo plano
        def cleanup_thread():
            # Ejecutar limpieza
            results = self.cleanup_manager.execute_cleanup(
                command_ids=command_ids,
                overwrite=overwrite,
                callback=self.write_to_terminal
            )
            
            # Actualizar UI en el hilo principal
            GLib.idle_add(self.cleanup_completed, results)
            return False
        
        GLib.timeout_add(100, cleanup_thread)
    
    def cleanup_completed(self, results):
        """Manejar finalización de limpieza"""
        self.cleaning = False
        
        # Mostrar resultados
        self.write_to_terminal("\n" + "-" * 50 + "\n")
        
        if results["success"]:
            self.write_to_terminal(_("Limpieza completada con éxito.\n"))
        else:
            self.write_to_terminal(_("La limpieza completó con algunos errores.\n"))
        
        # Habilitar botones
        self.clean_button.set_sensitive(True)
        
        return False
    
    def write_to_terminal(self, text):
        """Escribir texto en la terminal"""
        if hasattr(self, 'terminal'):
            text = str(text)
            if not text.endswith('\n'):
                text += '\n'
            self.terminal.feed(text.encode())
    
    def on_remove_kernels_clicked(self, button):
        """Manejar clic en botón de eliminar kernels antiguos"""
        # Obtener kernels antiguos
        old_kernels = self.cleanup_manager.get_old_kernels()
        
        if not old_kernels:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=_("No se encontraron kernels antiguos")
            )
            dialog.format_secondary_text(_("No hay kernels antiguos que eliminar."))
            dialog.run()
            dialog.destroy()
            return
        
        # Mostrar diálogo de confirmación
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_("¿Eliminar kernels antiguos?")
        )
        
        secondary_text = _("Se eliminarán los siguientes kernels antiguos:\n")
        for kernel in old_kernels:
            secondary_text += f"- {kernel['package']}\n"
        
        dialog.format_secondary_text(secondary_text)
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Limpiar terminal
            self.terminal.reset(True, True)
            
            # Mostrar mensaje de inicio
            self.write_to_terminal(_("Eliminando kernels antiguos...\n\n"))
            
            # Ejecutar limpieza en segundo plano
            def remove_kernels_thread():
                # Eliminar kernels
                success, message = self.cleanup_manager.remove_old_kernels(
                    callback=self.write_to_terminal
                )
                
                # Actualizar UI en el hilo principal
                GLib.idle_add(self.write_to_terminal, "\n" + "-" * 50 + "\n")
                
                if success:
                    GLib.idle_add(self.write_to_terminal, 
                                 _("Kernels antiguos eliminados con éxito.\n"))
                else:
                    GLib.idle_add(self.write_to_terminal, 
                                 _("Error al eliminar kernels antiguos: {0}\n").format(message))
                
                return False
            
            GLib.timeout_add(100, remove_kernels_thread)
    
    def shred_files(self, files):
        """Destruir archivos de forma segura"""
        if not files:
            return
        
        # Limpiar terminal
        self.terminal.reset(True, True)
        
        # Mostrar mensaje
        self.write_to_terminal(_("Destruyendo archivos de forma segura...\n\n"))
        
        for file_path in files:
            self.write_to_terminal(_("Destruyendo: {0}\n").format(file_path))
        
        # Ejecutar shred en segundo plano
        def shred_thread():
            for file_path in files:
                try:
                    # Usar shred para sobrescribir el archivo varias veces
                    process = subprocess.Popen(
                        ['shred', '-vzn', '3', file_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True
                    )
                    
                    for line in process.stdout:
                        GLib.idle_add(self.write_to_terminal, line)
                    
                    process.wait()
                    
                    # Eliminar el archivo
                    os.remove(file_path)
                    GLib.idle_add(self.write_to_terminal, 
                                 _("Archivo destruido: {0}\n").format(file_path))
                except Exception as e:
                    GLib.idle_add(self.write_to_terminal, 
                                 _("Error al destruir {0}: {1}\n").format(file_path, str(e)))
            
            GLib.idle_add(self.write_to_terminal, "\n" + _("Operación completada.\n"))
            return False
        
        GLib.timeout_add(100, shred_thread)
    
    def shred_directory(self, directory):
        """Destruir una carpeta y su contenido de forma segura"""
        if not directory:
            return
        
        # Limpiar terminal
        self.terminal.reset(True, True)
        
        # Mostrar mensaje
        self.write_to_terminal(_("Destruyendo carpeta de forma segura: {0}\n\n").format(directory))
        
        # Ejecutar en segundo plano
        def shred_dir_thread():
            try:
                # Recorrer todos los archivos del directorio
                for root, dirs, files in os.walk(directory, topdown=False):
                    # Primero destruir archivos
                    for file in files:
                        file_path = os.path.join(root, file)
                        GLib.idle_add(self.write_to_terminal, 
                                     _("Destruyendo: {0}\n").format(file_path))
                        
                        try:
                            # Usar shred para sobrescribir el archivo
                            subprocess.run(
                                ['shred', '-zn', '3', file_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )
                            
                            # Eliminar el archivo
                            os.remove(file_path)
                        except Exception as e:
                            GLib.idle_add(self.write_to_terminal, 
                                         _("Error: {0}\n").format(str(e)))
                    
                    # Luego eliminar directorios vacíos
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        try:
                            os.rmdir(dir_path)
                            GLib.idle_add(self.write_to_terminal, 
                                         _("Carpeta eliminada: {0}\n").format(dir_path))
                        except Exception as e:
                            GLib.idle_add(self.write_to_terminal, 
                                         _("Error al eliminar carpeta {0}: {1}\n").format(dir_path, str(e)))
                
                # Finalmente eliminar el directorio raíz
                try:
                    os.rmdir(directory)
                    GLib.idle_add(self.write_to_terminal, 
                                 _("Carpeta principal eliminada: {0}\n").format(directory))
                except Exception as e:
                    GLib.idle_add(self.write_to_terminal, 
                                 _("Error al eliminar carpeta principal: {0}\n").format(str(e)))
                
                GLib.idle_add(self.write_to_terminal, "\n" + _("Operación completada.\n"))
            except Exception as e:
                GLib.idle_add(self.write_to_terminal, 
                             _("Error al procesar directorio: {0}\n").format(str(e)))
            
            return False
        
        GLib.timeout_add(100, shred_dir_thread)
    
    def clean_free_space(self, directory):
        """Limpiar espacio libre en un sistema de archivos"""
        if not directory:
            return
        
        # Limpiar terminal
        self.terminal.reset(True, True)
        
        # Mostrar mensaje
        self.write_to_terminal(_("Limpiando espacio libre en: {0}\n\n").format(directory))
        
        # Ejecutar en segundo plano
        def clean_space_thread():
            success, message = self.cleanup_manager.clean_free_space(
                directory,
                callback=self.write_to_terminal
            )
            
            GLib.idle_add(self.write_to_terminal, "\n" + "-" * 50 + "\n")
            
            if success:
                GLib.idle_add(self.write_to_terminal, 
                             _("Limpieza de espacio libre completada con éxito.\n"))
            else:
                GLib.idle_add(self.write_to_terminal, 
                             _("Error en la limpieza de espacio libre: {0}\n").format(message))
            
            return False
        
        GLib.timeout_add(100, clean_space_thread)