#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pestaña para la actualización del sistema.
Permite actualizar el sistema y gestionar paquetes APT.
"""

import os
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Vte, GLib, Gdk, Pango

from utils.utils import _
from utils.apt_manager import AptManager

class UpdateTab(Gtk.Box):
    """Pestaña de actualización del sistema"""
    
    def __init__(self, parent_window):
        """Inicializar la pestaña de actualización"""
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.parent_window = parent_window
        self.apt_manager = AptManager()
        
        self.set_border_width(10)
        
        # Título de la pestaña
        title_label = Gtk.Label(label=_("Actualización del Sistema"))
        title_label.set_halign(Gtk.Align.START)
        self.pack_start(title_label, False, False, 0)
        
        # Área de contenido principal
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_box.set_border_width(10)
        self.pack_start(content_box, True, True, 0)
        
        # Marco para la terminal
        terminal_frame = Gtk.Frame()
        content_box.pack_start(terminal_frame, True, True, 0)
        
        # Terminal para mostrar salida
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
        
        # Panel de controles
        control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        content_box.pack_start(control_box, False, False, 10)
        
        # Etiqueta de información
        self.info_label = Gtk.Label()
        self.info_label.set_markup(_("Sistema listo"))
        control_box.pack_start(self.info_label, True, True, 0)
        
        # Botón para administrar paquetes
        self.manage_button = Gtk.Button(label=_("Administrar Paquetes"))
        self.manage_button.connect("clicked", self.on_manage_clicked)
        control_box.pack_start(self.manage_button, False, False, 0)
        
        # Botón para actualizar
        self.update_button = Gtk.Button(label=_("Actualizar Sistema"))
        self.update_button.connect("clicked", self.on_update_clicked)
        control_box.pack_start(self.update_button, False, False, 0)
        
        # Escribir mensaje inicial en la terminal
        self.write_to_terminal(_("Terminal lista para mostrar el proceso de actualización.\n"))
        self.write_to_terminal(_("Haga clic en 'Actualizar Sistema' para iniciar.\n"))
    
    def on_manage_clicked(self, button):
        """Manejar clic en botón de administrar paquetes"""
        self.show_apt_manager()
    
    def on_update_clicked(self, button):
        """Manejar clic en botón de actualizar sistema"""
        # Deshabilitar botones durante la actualización
        self.update_button.set_sensitive(False)
        self.manage_button.set_sensitive(False)
        
        # Limpiar terminal
        self.terminal.reset(True, True)
        
        # Mostrar mensaje de inicio
        self.write_to_terminal(_("Iniciando actualización del sistema...\n\n"))
        
        # Actualizar etiqueta de información
        self.info_label.set_markup(_("Actualizando el sistema..."))
        
        # Ejecutar actualización en segundo plano
        def update_system_thread():
            # Ejecutar actualización
            success, message = self.apt_manager.perform_update(
                callback=self.write_to_terminal
            )
            
            # Actualizar UI en el hilo principal
            GLib.idle_add(self.update_completed)
            return False
        
        GLib.timeout_add(100, update_system_thread)
    
    def update_completed(self):
        """Manejar finalización de actualización"""
        # Mostrar mensaje final
        self.write_to_terminal("\n" + "-" * 50 + "\n")
        self.write_to_terminal(_("Actualización completada.\n"))
        
        # Actualizar etiqueta de información
        self.info_label.set_markup(_("Sistema actualizado"))
        
        # Habilitar botones
        self.update_button.set_sensitive(True)
        self.manage_button.set_sensitive(True)
        
        return False
    
    def write_to_terminal(self, text):
        """Escribir texto en la terminal"""
        if hasattr(self, 'terminal'):
            text = str(text)
            if not text.endswith('\n'):
                text += '\n'
            self.terminal.feed(text.encode())
    
    def show_apt_manager(self):
        """Mostrar diálogo de gestión de paquetes"""
        dialog = AptManagerDialog(self.parent_window, self.apt_manager)
        dialog.run()
        dialog.destroy()

class AptManagerDialog(Gtk.Dialog):
    """Diálogo para gestionar paquetes APT"""
    
    def __init__(self, parent, apt_manager):
        """Inicializar el diálogo de gestión de paquetes"""
        Gtk.Dialog.__init__(
            self,
            title=_("Administración de Paquetes"),
            transient_for=parent,
            flags=0,
            buttons=(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        )
        
        self.apt_manager = apt_manager
        self.set_default_size(800, 600)
        
        # Área de contenido
        content_area = self.get_content_area()
        content_area.set_border_width(10)
        
        # Notebook para pestañas
        self.notebook = Gtk.Notebook()
        content_area.pack_start(self.notebook, True, True, 0)
        
        # Verificar si existen archivos de preferencias
        pref_files = self.apt_manager.get_pref_files()
        
        if not pref_files:
            # No hay archivos de preferencias, mostrar pantalla inicial
            no_files_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            self.notebook.append_page(no_files_box, Gtk.Label(label=_("Gestión de APT")))
            self.create_no_files_ui(no_files_box)
        else:
            # Hay archivos, mostrar interfaz de gestión
            self.create_manager_ui(content_area)
        
        self.show_all()
    
    def create_no_files_ui(self, box):
        """Crear interfaz cuando no hay archivos pref"""
        info_label = Gtk.Label()
        info_label.set_markup(_("<b>No se encontraron archivos de preferencias de APT</b>"))
        info_label.set_justify(Gtk.Justification.CENTER)
        box.pack_start(info_label, False, False, 10)
        
        description = Gtk.Label()
        description.set_markup(_(
            "Los archivos de preferencias de APT permiten configurar prioridades de paquetes "
            "y bloquear actualizaciones de paquetes específicos.\n\n"
            "¿Qué desea hacer?"
        ))
        description.set_justify(Gtk.Justification.CENTER)
        box.pack_start(description, False, False, 10)
        
        # Botones de acción
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.pack_start(button_box, False, False, 20)
        
        empty_button = Gtk.Button(label=_("Crear archivos vacíos"))
        empty_button.connect("clicked", self.on_create_empty_files)
        button_box.pack_start(empty_button, True, True, 0)
        
        default_button = Gtk.Button(label=_("Cargar configuración predeterminada"))
        default_button.connect("clicked", self.on_load_default_files)
        button_box.pack_start(default_button, True, True, 0)
    
    def on_create_empty_files(self, button):
        """Crear archivos de preferencias vacíos"""
        # Crear archivos vacíos de bloqueo y prioridades
        self.apt_manager.save_pref_file("dexter-blocked.pref", 
                                         "# Paquetes bloqueados por DexterSOA\n\n")
        self.apt_manager.save_pref_file("dexter-prioritys.pref", 
                                         "# Prioridades de paquetes configuradas por DexterSOA\n\n")
        
        # Recrear la interfaz
        self.recreate_ui()
    
    def on_load_default_files(self, button):
        """Cargar archivos de preferencias predeterminados"""
        # Archivo de bloqueo predeterminado
        blocked_content = """# Paquetes bloqueados por DexterSOA
# Formato:
# Package: <paquete>
# Pin: version *
# Pin-Priority: -1
"""
        
        # Archivo de prioridades predeterminado
        priority_content = """# Prioridades de paquetes configuradas por DexterSOA
# Formato:
# Package: <paquete>
# Pin: <origen>
# Pin-Priority: <prioridad>
"""
        
        # Crear los archivos
        self.apt_manager.save_pref_file("dexter-blocked.pref", blocked_content)
        self.apt_manager.save_pref_file("dexter-prioritys.pref", priority_content)
        
        # Recrear la interfaz
        self.recreate_ui()
    
    def recreate_ui(self):
        """Recrear la interfaz del diálogo"""
        # Eliminar todas las páginas del notebook
        while self.notebook.get_n_pages() > 0:
            self.notebook.remove_page(-1)
        
        # Crear nueva interfaz
        self.create_manager_ui(self.get_content_area())
        self.show_all()
    
    def create_manager_ui(self, box):
        """Crear interfaz de gestión de paquetes"""
        # Pestaña de paquetes bloqueados
        blocked_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.notebook.append_page(blocked_page, Gtk.Label(label=_("Paquetes Bloqueados")))
        
        # Lista de paquetes bloqueados
        blocked_label = Gtk.Label(label=_("Paquetes bloqueados para actualización:"))
        blocked_label.set_halign(Gtk.Align.START)
        blocked_page.pack_start(blocked_label, False, False, 0)
        
        # ScrolledWindow para la lista
        blocked_scroll = Gtk.ScrolledWindow()
        blocked_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        blocked_scroll.set_shadow_type(Gtk.ShadowType.IN)
        blocked_page.pack_start(blocked_scroll, True, True, 0)
        
        # Modelo de datos y vista
        self.blocked_store = Gtk.ListStore(str, str)  # paquete, archivo
        
        # Cargar paquetes bloqueados
        blocked_packages = self.apt_manager.get_blocked_packages()
        for pkg in blocked_packages:
            self.blocked_store.append([pkg["name"], pkg["file"]])
        
        blocked_tree = Gtk.TreeView(model=self.blocked_store)
        
        # Columnas
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Paquete"), renderer, text=0)
        blocked_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Archivo"), renderer, text=1)
        blocked_tree.append_column(column)
        
        blocked_scroll.add(blocked_tree)
        
        # Botones de acción
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        blocked_page.pack_start(button_box, False, False, 0)
        
        add_button = Gtk.Button(label=_("Añadir"))
        add_button.connect("clicked", self.on_add_blocked_clicked)
        button_box.pack_start(add_button, False, False, 0)
        
        remove_button = Gtk.Button(label=_("Eliminar"))
        remove_button.connect("clicked", self.on_remove_blocked_clicked, blocked_tree)
        button_box.pack_start(remove_button, False, False, 0)
        
        edit_button = Gtk.Button(label=_("Editar Archivo"))
        edit_button.connect("clicked", self.on_edit_blocked_clicked)
        button_box.pack_start(edit_button, False, False, 0)
        
        # Pestaña de paquetes con prioridad
        priority_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.notebook.append_page(priority_page, Gtk.Label(label=_("Paquetes con Prioridad")))
        
        # Lista de paquetes con prioridad
        priority_label = Gtk.Label(label=_("Paquetes con prioridad especial:"))
        priority_label.set_halign(Gtk.Align.START)
        priority_page.pack_start(priority_label, False, False, 0)
        
        # ScrolledWindow para la lista
        priority_scroll = Gtk.ScrolledWindow()
        priority_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        priority_scroll.set_shadow_type(Gtk.ShadowType.IN)
        priority_page.pack_start(priority_scroll, True, True, 0)
        
        # Modelo de datos y vista
        self.priority_store = Gtk.ListStore(str, str, int, str)  # paquete, origen, prioridad, archivo
        
        # Cargar paquetes con prioridad
        priority_packages = self.apt_manager.get_priority_packages()
        for pkg in priority_packages:
            self.priority_store.append([
                pkg["name"], pkg["origin"], pkg["priority"], pkg["file"]
            ])
        
        priority_tree = Gtk.TreeView(model=self.priority_store)
        
        # Columnas
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Paquete"), renderer, text=0)
        priority_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Origen"), renderer, text=1)
        priority_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Prioridad"), renderer, text=2)
        priority_tree.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Archivo"), renderer, text=3)
        priority_tree.append_column(column)
        
        priority_scroll.add(priority_tree)
        
        # Botones de acción
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        priority_page.pack_start(button_box, False, False, 0)
        
        add_button = Gtk.Button(label=_("Añadir"))
        add_button.connect("clicked", self.on_add_priority_clicked)
        button_box.pack_start(add_button, False, False, 0)
        
        remove_button = Gtk.Button(label=_("Eliminar"))
        remove_button.connect("clicked", self.on_remove_priority_clicked, priority_tree)
        button_box.pack_start(remove_button, False, False, 0)
        
        edit_button = Gtk.Button(label=_("Editar Archivo"))
        edit_button.connect("clicked", self.on_edit_priority_clicked)
        button_box.pack_start(edit_button, False, False, 0)
    
    def on_add_blocked_clicked(self, button):
        """Manejar clic en botón de añadir paquete bloqueado"""
        # Diálogo para añadir paquete bloqueado
        dialog = Gtk.Dialog(
            title=_("Añadir Paquete Bloqueado"),
            transient_for=self,
            flags=0,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(350, 100)
        
        content_area = dialog.get_content_area()
        content_area.set_border_width(10)
        
        # Formulario
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        content_area.add(grid)
        
        # Etiqueta y entrada para el nombre del paquete
        package_label = Gtk.Label(label=_("Nombre del paquete:"))
        package_label.set_halign(Gtk.Align.START)
        grid.attach(package_label, 0, 0, 1, 1)
        
        package_entry = Gtk.Entry()
        grid.attach(package_entry, 1, 0, 1, 1)
        
        # Etiqueta y combobox para el archivo
        file_label = Gtk.Label(label=_("Archivo:"))
        file_label.set_halign(Gtk.Align.START)
        grid.attach(file_label, 0, 1, 1, 1)
        
        file_store = Gtk.ListStore(str)
        
        # Añadir archivos existentes
        pref_files = self.apt_manager.get_pref_files()
        for file in pref_files:
            filename = os.path.basename(file)
            if filename.endswith(".pref"):
                file_store.append([filename])
        
        file_combo = Gtk.ComboBox.new_with_model(file_store)
        renderer_text = Gtk.CellRendererText()
        file_combo.pack_start(renderer_text, True)
        file_combo.add_attribute(renderer_text, "text", 0)
        
        # Establecer valor predeterminado
        file_combo.set_active(0)
        
        grid.attach(file_combo, 1, 1, 1, 1)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            package_name = package_entry.get_text()
            
            # Obtener archivo seleccionado
            iter = file_combo.get_active_iter()
            if iter is not None:
                file_name = file_store[iter][0]
            else:
                file_name = "dexter-blocked.pref"
            
            # Verificar que se ingresó un nombre de paquete
            if package_name:
                # Añadir paquete bloqueado
                success = self.apt_manager.add_blocked_package(package_name, file_name)
                
                if success:
                    # Actualizar lista
                    self.blocked_store.append([package_name, file_name])
        
        dialog.destroy()
    
    def on_remove_blocked_clicked(self, button, treeview):
        """Manejar clic en botón de eliminar paquete bloqueado"""
        selection = treeview.get_selection()
        model, iter = selection.get_selected()
        
        if iter is not None:
            package_name = model[iter][0]
            file_name = model[iter][1]
            
            # Mostrar diálogo de confirmación
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=_("¿Eliminar paquete bloqueado?")
            )
            
            dialog.format_secondary_text(
                _("¿Desea eliminar '{0}' de la lista de paquetes bloqueados?").format(package_name))
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                # Eliminar paquete
                success = self.apt_manager.remove_package_from_pref(package_name, file_name)
                
                if success:
                    # Eliminar de la lista
                    model.remove(iter)
    
    def on_edit_blocked_clicked(self, button):
        """Manejar clic en botón de editar archivo de bloqueados"""
        # Diálogo para editar archivo
        dialog = Gtk.Dialog(
            title=_("Editar Archivo de Bloqueo"),
            transient_for=self,
            flags=0,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(600, 400)
        
        content_area = dialog.get_content_area()
        content_area.set_border_width(10)
        
        # Selector de archivo
        file_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        content_area.pack_start(file_box, False, False, 0)
        
        file_label = Gtk.Label(label=_("Archivo:"))
        file_box.pack_start(file_label, False, False, 0)
        
        file_store = Gtk.ListStore(str, str)  # nombre, ruta
        
        # Añadir archivos existentes
        pref_files = self.apt_manager.get_pref_files()
        for file in pref_files:
            filename = os.path.basename(file)
            if filename.endswith(".pref"):
                file_store.append([filename, file])
        
        file_combo = Gtk.ComboBox.new_with_model(file_store)
        renderer_text = Gtk.CellRendererText()
        file_combo.pack_start(renderer_text, True)
        file_combo.add_attribute(renderer_text, "text", 0)
        
        # Establecer valor predeterminado
        file_combo.set_active(0)
        
        file_box.pack_start(file_combo, True, True, 0)
        
        # Área de texto para editar el archivo
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        content_area.pack_start(scrolled, True, True, 10)
        
        self.edit_textview = Gtk.TextView()
        scrolled.add(self.edit_textview)
        
        # Función para actualizar el contenido del textview
        def on_file_changed(combo):
            iter = combo.get_active_iter()
            if iter is not None:
                file_path = file_store[iter][1]
                
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    buffer = self.edit_textview.get_buffer()
                    buffer.set_text(content)
                except Exception as e:
                    print(f"Error al leer archivo: {e}")
        
        # Conectar señal y cargar archivo inicial
        file_combo.connect("changed", on_file_changed)
        on_file_changed(file_combo)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Guardar cambios
            iter = file_combo.get_active_iter()
            if iter is not None:
                file_path = file_store[iter][1]
                
                buffer = self.edit_textview.get_buffer()
                start, end = buffer.get_bounds()
                content = buffer.get_text(start, end, False)
                
                try:
                    with open(file_path, 'w') as f:
                        f.write(content)
                except Exception as e:
                    print(f"Error al guardar archivo: {e}")
        
        dialog.destroy()
        
        # Actualizar la lista
        self.recreate_ui()
    
    def on_add_priority_clicked(self, button):
        """Manejar clic en botón de añadir paquete prioritario"""
        # Diálogo para añadir paquete con prioridad
        dialog = Gtk.Dialog(
            title=_("Añadir Paquete con Prioridad"),
            transient_for=self,
            flags=0,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(400, 200)
        
        content_area = dialog.get_content_area()
        content_area.set_border_width(10)
        
        # Formulario
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        content_area.add(grid)
        
        # Etiqueta y entrada para el nombre del paquete
        package_label = Gtk.Label(label=_("Nombre del paquete:"))
        package_label.set_halign(Gtk.Align.START)
        grid.attach(package_label, 0, 0, 1, 1)
        
        package_entry = Gtk.Entry()
        grid.attach(package_entry, 1, 0, 1, 1)
        
        # Etiqueta y entrada para el origen
        origin_label = Gtk.Label(label=_("Origen (Pin):"))
        origin_label.set_halign(Gtk.Align.START)
        grid.attach(origin_label, 0, 1, 1, 1)
        
        origin_entry = Gtk.Entry()
        origin_entry.set_text("release a=stable")
        grid.attach(origin_entry, 1, 1, 1, 1)
        
        # Etiqueta y entrada para la prioridad
        priority_label = Gtk.Label(label=_("Prioridad:"))
        priority_label.set_halign(Gtk.Align.START)
        grid.attach(priority_label, 0, 2, 1, 1)
        
        adjustment = Gtk.Adjustment(value=900, lower=-1, upper=1000, step_increment=1)
        priority_spin = Gtk.SpinButton()
        priority_spin.set_adjustment(adjustment)
        grid.attach(priority_spin, 1, 2, 1, 1)
        
        # Etiqueta y combobox para el archivo
        file_label = Gtk.Label(label=_("Archivo:"))
        file_label.set_halign(Gtk.Align.START)
        grid.attach(file_label, 0, 3, 1, 1)
        
        file_store = Gtk.ListStore(str)
        
        # Añadir archivos existentes
        pref_files = self.apt_manager.get_pref_files()
        for file in pref_files:
            filename = os.path.basename(file)
            if filename.endswith(".pref"):
                file_store.append([filename])
        
        file_combo = Gtk.ComboBox.new_with_model(file_store)
        renderer_text = Gtk.CellRendererText()
        file_combo.pack_start(renderer_text, True)
        file_combo.add_attribute(renderer_text, "text", 0)
        
        # Establecer valor predeterminado
        for i, row in enumerate(file_store):
            if "prioritys" in row[0]:
                file_combo.set_active(i)
                break
        
        if file_combo.get_active() == -1 and len(file_store) > 0:
            file_combo.set_active(0)
        
        grid.attach(file_combo, 1, 3, 1, 1)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            package_name = package_entry.get_text()
            origin = origin_entry.get_text()
            priority = priority_spin.get_value_as_int()
            
            # Obtener archivo seleccionado
            iter = file_combo.get_active_iter()
            if iter is not None:
                file_name = file_store[iter][0]
            else:
                file_name = "dexter-prioritys.pref"
            
            # Verificar que se ingresaron los datos necesarios
            if package_name and origin:
                # Añadir paquete con prioridad
                success = self.apt_manager.add_priority_package(
                    package_name, origin, priority, file_name)
                
                if success:
                    # Actualizar lista
                    self.priority_store.append([package_name, origin, priority, file_name])
        
        dialog.destroy()
    
    def on_remove_priority_clicked(self, button, treeview):
        """Manejar clic en botón de eliminar paquete prioritario"""
        selection = treeview.get_selection()
        model, iter = selection.get_selected()
        
        if iter is not None:
            package_name = model[iter][0]
            file_name = model[iter][3]
            
            # Mostrar diálogo de confirmación
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=_("¿Eliminar paquete con prioridad?")
            )
            
            dialog.format_secondary_text(
                _("¿Desea eliminar '{0}' de la lista de paquetes con prioridad?").format(package_name))
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                # Eliminar paquete
                success = self.apt_manager.remove_package_from_pref(package_name, file_name)
                
                if success:
                    # Eliminar de la lista
                    model.remove(iter)
    
    def on_edit_priority_clicked(self, button):
        """Manejar clic en botón de editar archivo de prioridades"""
        # Diálogo para editar archivo
        dialog = Gtk.Dialog(
            title=_("Editar Archivo de Prioridades"),
            transient_for=self,
            flags=0,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK
            )
        )
        dialog.set_default_size(600, 400)
        
        content_area = dialog.get_content_area()
        content_area.set_border_width(10)
        
        # Selector de archivo
        file_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        content_area.pack_start(file_box, False, False, 0)
        
        file_label = Gtk.Label(label=_("Archivo:"))
        file_box.pack_start(file_label, False, False, 0)
        
        file_store = Gtk.ListStore(str, str)  # nombre, ruta
        
        # Añadir archivos existentes
        pref_files = self.apt_manager.get_pref_files()
        for file in pref_files:
            filename = os.path.basename(file)
            if filename.endswith(".pref"):
                file_store.append([filename, file])
        
        file_combo = Gtk.ComboBox.new_with_model(file_store)
        renderer_text = Gtk.CellRendererText()
        file_combo.pack_start(renderer_text, True)
        file_combo.add_attribute(renderer_text, "text", 0)
        
        # Establecer valor predeterminado
        for i, row in enumerate(file_store):
            if "prioritys" in row[0]:
                file_combo.set_active(i)
                break
        
        if file_combo.get_active() == -1 and len(file_store) > 0:
            file_combo.set_active(0)
        
        file_box.pack_start(file_combo, True, True, 0)
        
        # Área de texto para editar el archivo
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        content_area.pack_start(scrolled, True, True, 10)
        
        self.edit_textview = Gtk.TextView()
        scrolled.add(self.edit_textview)
        
        # Función para actualizar el contenido del textview
        def on_file_changed(combo):
            iter = combo.get_active_iter()
            if iter is not None:
                file_path = file_store[iter][1]
                
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    buffer = self.edit_textview.get_buffer()
                    buffer.set_text(content)
                except Exception as e:
                    print(f"Error al leer archivo: {e}")
        
        # Conectar señal y cargar archivo inicial
        file_combo.connect("changed", on_file_changed)
        on_file_changed(file_combo)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Guardar cambios
            iter = file_combo.get_active_iter()
            if iter is not None:
                file_path = file_store[iter][1]
                
                buffer = self.edit_textview.get_buffer()
                start, end = buffer.get_bounds()
                content = buffer.get_text(start, end, False)
                
                try:
                    with open(file_path, 'w') as f:
                        f.write(content)
                except Exception as e:
                    print(f"Error al guardar archivo: {e}")
        
        dialog.destroy()
        
        # Actualizar la lista
        self.recreate_ui()