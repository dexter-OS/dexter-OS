#!/usr/bin/env python3
import gi
import os
import json
import zipfile
import datetime
import shutil
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

class BackupManager:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.data_path = os.path.expanduser("~/.local/share/dexter-organizer")
        self.config_file = os.path.join(self.data_path, "config.json")
        
        # Cargar configuración
        self.load_config()
        
        # Contenedor principal
        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.container.set_margin_top(20)
        self.container.set_margin_bottom(20)
        self.container.set_margin_start(20)
        self.container.set_margin_end(20)
        
        # Título
        title = Gtk.Label(label="<b>Respaldo y Restauración</b>")
        title.set_use_markup(True)
        title.set_halign(Gtk.Align.START)
        self.container.append(title)
        
        # Información
        info = Gtk.Label(label="Crea respaldos de tus documentos y categorías para evitar pérdidas de información.")
        info.set_halign(Gtk.Align.START)
        info.set_wrap(True)
        self.container.append(info)
        
        # Ruta de respaldo
        path_frame = Gtk.Frame()
        path_frame.set_label("Ruta de Respaldo")
        
        path_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        path_box.set_margin_top(10)
        path_box.set_margin_bottom(10)
        path_box.set_margin_start(10)
        path_box.set_margin_end(10)
        
        self.path_label = Gtk.Label(label=self.config["backup_path"])
        self.path_label.set_halign(Gtk.Align.START)
        path_box.append(self.path_label)
        
        path_note = Gtk.Label(label="<i>Nota: Puedes cambiar la ruta de respaldo en la configuración.</i>")
        path_note.set_use_markup(True)
        path_note.set_halign(Gtk.Align.START)
        path_box.append(path_note)
        
        path_frame.set_child(path_box)
        self.container.append(path_frame)
        
        # Acciones de respaldo
        action_frame = Gtk.Frame()
        action_frame.set_label("Acciones")
        
        action_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        action_box.set_margin_top(10)
        action_box.set_margin_bottom(10)
        action_box.set_margin_start(10)
        action_box.set_margin_end(10)
        
        # Crear respaldo
        backup_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        backup_label = Gtk.Label(label="Crear un nuevo respaldo de todos tus datos:")
        backup_label.set_hexpand(True)
        backup_label.set_halign(Gtk.Align.START)
        
        backup_button = Gtk.Button(label="Crear Respaldo")
        backup_button.connect("clicked", self.on_create_backup)
        
        backup_box.append(backup_label)
        backup_box.append(backup_button)
        
        action_box.append(backup_box)
        
        # Restaurar respaldo
        restore_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        restore_label = Gtk.Label(label="Restaurar desde un archivo de respaldo:")
        restore_label.set_hexpand(True)
        restore_label.set_halign(Gtk.Align.START)
        
        restore_button = Gtk.Button(label="Restaurar Respaldo")
        restore_button.connect("clicked", self.on_restore_backup)
        
        restore_box.append(restore_label)
        restore_box.append(restore_button)
        
        action_box.append(restore_box)
        
        action_frame.set_child(action_box)
        self.container.append(action_frame)
        
        # Historial de respaldos
        history_frame = Gtk.Frame()
        history_frame.set_label("Historial de Respaldos")
        
        history_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        history_box.set_margin_top(10)
        history_box.set_margin_bottom(10)
        history_box.set_margin_start(10)
        history_box.set_margin_end(10)
        
        self.history_list = Gtk.ListBox()
        self.history_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_min_content_height(150)
        scrolled_window.set_child(self.history_list)
        
        history_box.append(scrolled_window)
        
        # Botones de acción para el historial
        history_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        history_actions.set_halign(Gtk.Align.END)
        
        refresh_button = Gtk.Button(label="Actualizar")
        refresh_button.connect("clicked", self.on_refresh_history)
        
        delete_button = Gtk.Button(label="Eliminar Seleccionado")
        delete_button.connect("clicked", self.on_delete_backup)
        
        history_actions.append(refresh_button)
        history_actions.append(delete_button)
        
        history_box.append(history_actions)
        
        history_frame.set_child(history_box)
        self.container.append(history_frame)
        
        # Cargar historial de respaldos
        self.load_backup_history()
        
    def get_container(self):
        return self.container
        
    def load_config(self):
        # Cargar configuración desde el archivo JSON
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {
                "backup_path": os.path.expanduser("~/Documentos/DexterBackups"),
                "data_path": self.data_path,
                "font_family": "Sans",
                "font_size": 10,
                "theme": "dark"
            }
            
            # Crear directorio de respaldo si no existe
            os.makedirs(self.config["backup_path"], exist_ok=True)
            
            # Guardar configuración
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
                
    def load_backup_history(self):
        # Limpiar la lista
        for child in self.history_list:
            self.history_list.remove(child)
            
        # Verificar si el directorio de respaldo existe
        if not os.path.exists(self.config["backup_path"]):
            os.makedirs(self.config["backup_path"], exist_ok=True)
            
            no_backups = Gtk.Label(label="No hay respaldos disponibles.")
            no_backups.set_margin_top(10)
            no_backups.set_margin_bottom(10)
            
            row = Gtk.ListBoxRow()
            row.set_selectable(False)
            row.set_child(no_backups)
            
            self.history_list.append(row)
            return
            
        # Obtener lista de archivos de respaldo
        backup_files = []
        for filename in os.listdir(self.config["backup_path"]):
            if filename.startswith("dexter_backup_") and filename.endswith(".zip"):
                filepath = os.path.join(self.config["backup_path"], filename)
                backup_files.append((filename, os.path.getmtime(filepath)))
                
        # Ordenar por fecha de modificación (más reciente primero)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        if not backup_files:
            no_backups = Gtk.Label(label="No hay respaldos disponibles.")
            no_backups.set_margin_top(10)
            no_backups.set_margin_bottom(10)
            
            row = Gtk.ListBoxRow()
            row.set_selectable(False)
            row.set_child(no_backups)
            
            self.history_list.append(row)
            return
            
        # Añadir respaldos a la lista
        for filename, mtime in backup_files:
            # Convertir timestamp a fecha legible
            date_str = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S")
            
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.set_margin_top(5)
            box.set_margin_bottom(5)
            box.set_margin_start(5)
            box.set_margin_end(5)
            
            icon = Gtk.Image.new_from_icon_name("package-x-generic")
            box.append(icon)
            
            label = Gtk.Label(label=f"{filename} - {date_str}")
            label.set_halign(Gtk.Align.START)
            box.append(label)
            
            row = Gtk.ListBoxRow()
            row.set_child(box)
            row.set_data("filename", filename)
            
            self.history_list.append(row)
            
    def on_refresh_history(self, button):
        self.load_backup_history()
        
    def on_create_backup(self, button=None):
        return self.create_backup(self.config["backup_path"])
        
    def create_backup(self, backup_path):
        # Verificar si el directorio de respaldo existe
        if not os.path.exists(backup_path):
            try:
                os.makedirs(backup_path, exist_ok=True)
            except OSError as e:
                dialog = Gtk.MessageDialog(
                    transient_for=self.parent,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Error al crear directorio de respaldo"
                )
                dialog.format_secondary_text(str(e))
                dialog.run()
                dialog.destroy()
                return False
                
        # Crear nombre de archivo con fecha y hora
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"dexter_backup_{now}.zip"
        backup_filepath = os.path.join(backup_path, backup_filename)
        
        try:
            # Crear archivo ZIP
            with zipfile.ZipFile(backup_filepath, 'w') as zipf:
                # Añadir archivos de datos
                for filename in os.listdir(self.data_path):
                    if filename.endswith(".json"):
                        file_path = os.path.join(self.data_path, filename)
                        zipf.write(file_path, os.path.basename(file_path))
                        
            # Actualizar historial
            self.load_backup_history()
            
            return True
        except Exception as e:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error al crear respaldo"
            )
            dialog.format_secondary_text(str(e))
            dialog.run()
            dialog.destroy()
            return False
            
    def on_restore_backup(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Seleccionar Archivo de Respaldo",
            transient_for=self.parent,
            action=Gtk.FileChooserAction.OPEN
        )
        
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Restaurar", Gtk.ResponseType.OK)
        
        filter_zip = Gtk.FileFilter()
        filter_zip.set_name("Archivos ZIP")
        filter_zip.add_pattern("*.zip")
        dialog.add_filter(filter_zip)
        
        dialog.set_current_folder(Gio.File.new_for_path(self.config["backup_path"]))
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            backup_file = dialog.get_file().get_path()
            dialog.destroy()
            
            # Confirmar restauración
            confirm_dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Confirmar Restauración"
            )
            confirm_dialog.format_secondary_text("¿Estás seguro de que deseas restaurar desde este respaldo? Se sobrescribirán todos los datos actuales.")
            
            confirm_response = confirm_dialog.run()
            confirm_dialog.destroy()
            
            if confirm_response == Gtk.ResponseType.YES:
                self.restore_backup(backup_file)
        else:
            dialog.destroy()
            
    def restore_backup(self, backup_file):
        try:
            # Verificar si el archivo es un ZIP válido
            if not zipfile.is_zipfile(backup_file):
                dialog = Gtk.MessageDialog(
                    transient_for=self.parent,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Archivo de respaldo inválido"
                )
                dialog.format_secondary_text("El archivo seleccionado no es un archivo ZIP válido.")
                dialog.run()
                dialog.destroy()
                return False
                
            # Crear directorio temporal
            temp_dir = os.path.join(self.data_path, "temp_restore")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            # Extraer archivos al directorio temporal
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_dir)
                
            # Verificar si los archivos necesarios están presentes
            required_files = ["categories.json", "documents.json", "config.json"]
            for file in required_files:
                if not os.path.exists(os.path.join(temp_dir, file)):
                    shutil.rmtree(temp_dir)
                    
                    dialog = Gtk.MessageDialog(
                        transient_for=self.parent,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="Respaldo incompleto"
                    )
                    dialog.format_secondary_text(f"El archivo de respaldo no contiene todos los archivos necesarios. Falta: {file}")
                    dialog.run()
                    dialog.destroy()
                    return False
                    
            # Hacer copia de seguridad de los archivos actuales
            backup_dir = os.path.join(self.data_path, "backup_before_restore")
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            os.makedirs(backup_dir)
            
            for filename in os.listdir(self.data_path):
                if filename.endswith(".json"):
                    shutil.copy2(os.path.join(self.data_path, filename), backup_dir)
                    
            # Copiar archivos restaurados
            for filename in os.listdir(temp_dir):
                if filename.endswith(".json"):
                    shutil.copy2(os.path.join(temp_dir, filename), self.data_path)
                    
            # Limpiar
            shutil.rmtree(temp_dir)
            
            # Mostrar mensaje de éxito
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Restauración Completada"
            )
            dialog.format_secondary_text("Se han restaurado los datos correctamente. La aplicación se reiniciará para aplicar los cambios.")
            dialog.run()
            dialog.destroy()
            
            # Reiniciar la aplicación
            self.parent.get_application().quit()
            
            return True
        except Exception as e:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error al restaurar respaldo"
            )
            dialog.format_secondary_text(str(e))
            dialog.run()
            dialog.destroy()
            return False
            
    def on_delete_backup(self, button):
        selected_row = self.history_list.get_selected_row()
        if selected_row is None:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Ningún respaldo seleccionado"
            )
            dialog.format_secondary_text("Por favor, selecciona un respaldo para eliminar.")
            dialog.run()
            dialog.destroy()
            return
            
        filename = selected_row.get_data("filename")
        if not filename:
            return
            
        # Confirmar eliminación
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Confirmar Eliminación"
        )
        dialog.format_secondary_text(f"¿Estás seguro de que deseas eliminar el respaldo '{filename}'?")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            filepath = os.path.join(self.config["backup_path"], filename)
            try:
                os.remove(filepath)
                self.load_backup_history()
            except OSError as e:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self.parent,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Error al eliminar respaldo"
                )
                error_dialog.format_secondary_text(str(e))
                error_dialog.run()
                error_dialog.destroy()
