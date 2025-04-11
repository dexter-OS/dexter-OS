#!/usr/bin/env python3
import gi
import os
import subprocess
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gio

class FileManager:
    def __init__(self, parent_window):
        self.parent = parent_window
        
        # Contenedor principal
        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.container.set_margin_top(20)
        self.container.set_margin_bottom(20)
        self.container.set_margin_start(20)
        self.container.set_margin_end(20)
        
        # Título
        title = Gtk.Label(label="<b>Gestor de Archivos</b>")
        title.set_use_markup(True)
        title.set_halign(Gtk.Align.START)
        self.container.append(title)
        
        # Descripción
        description = Gtk.Label(label="Abre carpetas en el gestor de archivos del sistema.")
        description.set_halign(Gtk.Align.START)
        description.set_margin_bottom(20)
        self.container.append(description)
        
        # Carpetas comunes
        common_frame = Gtk.Frame()
        common_frame.set_label("Carpetas Comunes")
        
        common_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        common_box.set_margin_top(10)
        common_box.set_margin_bottom(10)
        common_box.set_margin_start(10)
        common_box.set_margin_end(10)
        
        # Carpeta de datos
        data_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        data_label = Gtk.Label(label="Carpeta de Datos:")
        data_label.set_hexpand(True)
        data_label.set_halign(Gtk.Align.START)
        
        data_button = Gtk.Button(label="Abrir")
        data_button.connect("clicked", self.on_open_data_folder)
        
        data_box.append(data_label)
        data_box.append(data_button)
        
        common_box.append(data_box)
        
        # Carpeta de respaldos
        backup_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        backup_label = Gtk.Label(label="Carpeta de Respaldos:")
        backup_label.set_hexpand(True)
        backup_label.set_halign(Gtk.Align.START)
        
        backup_button = Gtk.Button(label="Abrir")
        backup_button.connect("clicked", self.on_open_backup_folder)
        
        backup_box.append(backup_label)
        backup_box.append(backup_button)
        
        common_box.append(backup_box)
        
        # Carpeta de documentos
        documents_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        documents_label = Gtk.Label(label="Carpeta de Documentos:")
        documents_label.set_hexpand(True)
        documents_label.set_halign(Gtk.Align.START)
        
        documents_button = Gtk.Button(label="Abrir")
        documents_button.connect("clicked", self.on_open_documents_folder)
        
        documents_box.append(documents_label)
        documents_box.append(documents_button)
        
        common_box.append(documents_box)
        
        common_frame.set_child(common_box)
        self.container.append(common_frame)
        
        # Abrir carpeta personalizada
        custom_frame = Gtk.Frame()
        custom_frame.set_label("Abrir Carpeta Personalizada")
        
        custom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        custom_box.set_margin_top(10)
        custom_box.set_margin_bottom(10)
        custom_box.set_margin_start(10)
        custom_box.set_margin_end(10)
        
        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.path_entry = Gtk.Entry()
        self.path_entry.set_placeholder_text("Ruta de la carpeta")
        self.path_entry.set_hexpand(True)
        
        browse_button = Gtk.Button(label="Examinar")
        browse_button.connect("clicked", self.on_browse_folder)
        
        open_button = Gtk.Button(label="Abrir")
        open_button.connect("clicked", self.on_open_custom_folder)
        
        path_box.append(self.path_entry)
        path_box.append(browse_button)
        path_box.append(open_button)
        
        custom_box.append(path_box)
        
        custom_frame.set_child(custom_box)
        self.container.append(custom_frame)
        
    def get_container(self):
        return self.container
        
    def detect_file_manager(self):
        """Detecta el gestor de archivos predeterminado del sistema."""
        file_managers = [
            "nautilus",  # GNOME
            "nemo",      # Cinnamon
            "thunar",    # XFCE
            "dolphin",   # KDE
            "pcmanfm",   # LXDE
            "caja",      # MATE
            "xdg-open"   # Fallback
        ]
        
        for fm in file_managers:
            try:
                # Comprobar si el comando existe
                subprocess.run(["which", fm], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                return fm
            except subprocess.CalledProcessError:
                continue
                
        return "xdg-open"  # Fallback
        
    def open_folder(self, path):
        """Abre una carpeta en el gestor de archivos del sistema."""
        if not os.path.exists(path):
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Carpeta no encontrada"
            )
            dialog.format_secondary_text(f"La carpeta {path} no existe.")
            dialog.run()
            dialog.destroy()
            return
            
        file_manager = self.detect_file_manager()
        
        try:
            subprocess.Popen([file_manager, path])
        except Exception as e:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error al abrir el gestor de archivos"
            )
            dialog.format_secondary_text(str(e))
            dialog.run()
            dialog.destroy()
            
    def on_open_data_folder(self, button):
        """Abre la carpeta de datos."""
        data_path = os.path.expanduser("~/.local/share/dexter-organizer")
        self.open_folder(data_path)
        
    def on_open_backup_folder(self, button):
        """Abre la carpeta de respaldos."""
        # Cargar configuración para obtener la ruta de respaldos
        config_file = os.path.expanduser("~/.local/share/dexter-organizer/config.json")
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                backup_path = config.get("backup_path", os.path.expanduser("~/Documentos/DexterBackups"))
        except (FileNotFoundError, json.JSONDecodeError):
            backup_path = os.path.expanduser("~/Documentos/DexterBackups")
            
        self.open_folder(backup_path)
        
    def on_open_documents_folder(self, button):
        """Abre la carpeta de documentos."""
        documents_path = os.path.expanduser("~/Documentos")
        self.open_folder(documents_path)
        
    def on_browse_folder(self, button):
        """Muestra un diálogo para seleccionar una carpeta."""
        dialog = Gtk.FileChooserDialog(
            title="Seleccionar Carpeta",
            transient_for=self.parent,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Seleccionar", Gtk.ResponseType.OK)
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.path_entry.set_text(dialog.get_file().get_path())
            
        dialog.destroy()
        
    def on_open_custom_folder(self, button):
        """Abre la carpeta especificada en el campo de texto."""
        path = self.path_entry.get_text().strip()
        if path:
            self.open_folder(path)
        else:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Ruta vacía"
            )
            dialog.format_secondary_text("Por favor, especifica una ruta de carpeta.")
            dialog.run()
            dialog.destroy()
