#!/usr/bin/env python3
import gi
import os
import json
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Pango

class ConfigManager:
    def __init__(self, parent_window):
        self.parent = parent_window
        self.data_path = os.path.expanduser("~/.local/share/dexter-organizer")
        self.config_file = os.path.join(self.data_path, "config.json")
        
        # Valores predeterminados
        self.default_config = {
            "backup_path": os.path.expanduser("~/Documentos/DexterBackups"),
            "data_path": self.data_path,
            "font_family": "Sans",
            "font_size": 10,
            "theme": "dark"
        }
        
        # Cargar configuración
        self.load_config()
        
        # Contenedor principal
        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.container.set_margin_top(20)
        self.container.set_margin_bottom(20)
        self.container.set_margin_start(20)
        self.container.set_margin_end(20)
        
        # Título
        title = Gtk.Label(label="<b>Configuración</b>")
        title.set_use_markup(True)
        title.set_halign(Gtk.Align.START)
        self.container.append(title)
        
        # Notebook para pestañas
        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)
        
        # Pestaña de Respaldo
        backup_page = self.create_backup_page()
        notebook.append_page(backup_page, Gtk.Label(label="Respaldo"))
        
        # Pestaña de Categorías
        categories_page = self.create_categories_page()
        notebook.append_page(categories_page, Gtk.Label(label="Categorías"))
        
        # Pestaña de Preferencias
        preferences_page = self.create_preferences_page()
        notebook.append_page(preferences_page, Gtk.Label(label="Preferencias"))
        
        self.container.append(notebook)
        
        # Botones de acción
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_box.set_halign(Gtk.Align.END)
        action_box.set_margin_top(10)
        
        self.save_button = Gtk.Button(label="Guardar Configuración")
        self.save_button.connect("clicked", self.on_save_config)
        self.save_button.add_css_class("suggested-action")
        
        action_box.append(self.save_button)
        
        self.container.append(action_box)
        
    def get_container(self):
        return self.container
        
    def load_config(self):
        # Crear directorio de datos si no existe
        os.makedirs(self.data_path, exist_ok=True)
        
        # Cargar configuración desde el archivo JSON
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = self.default_config.copy()
            self.save_config()
            
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
            
    def create_backup_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_margin_top(20)
        page.set_margin_bottom(20)
        page.set_margin_start(20)
        page.set_margin_end(20)
        
        # Ruta de respaldo
        backup_frame = Gtk.Frame()
        backup_frame.set_label("Ruta de Respaldo")
        
        backup_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        backup_box.set_margin_top(10)
        backup_box.set_margin_bottom(10)
        backup_box.set_margin_start(10)
        backup_box.set_margin_end(10)
        
        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.backup_path_entry = Gtk.Entry()
        self.backup_path_entry.set_text(self.config["backup_path"])
        self.backup_path_entry.set_hexpand(True)
        
        browse_button = Gtk.Button(label="Examinar")
        browse_button.connect("clicked", self.on_browse_backup_path)
        
        path_box.append(self.backup_path_entry)
        path_box.append(browse_button)
        
        backup_box.append(path_box)
        
        # Botones de respaldo y restauración
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_box.set_halign(Gtk.Align.CENTER)
        action_box.set_margin_top(10)
        
        backup_button = Gtk.Button(label="Crear Respaldo Ahora")
        backup_button.connect("clicked", self.on_create_backup)
        
        restore_button = Gtk.Button(label="Restaurar desde Respaldo")
        restore_button.connect("clicked", self.on_restore_backup)
        
        action_box.append(backup_button)
        action_box.append(restore_button)
        
        backup_box.append(action_box)
        
        backup_frame.set_child(backup_box)
        page.append(backup_frame)
        
        return page
        
    def create_categories_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_margin_top(20)
        page.set_margin_bottom(20)
        page.set_margin_start(20)
        page.set_margin_end(20)
        
        # Importar el módulo de categorías
        from modules.dexter_category import CategoryManager
        
        # Crear una instancia del administrador de categorías
        category_manager = CategoryManager(self.parent)
        
        # Añadir el contenedor del administrador de categorías
        page.append(category_manager.get_container())
        
        return page
        
    def create_preferences_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_margin_top(20)
        page.set_margin_bottom(20)
        page.set_margin_start(20)
        page.set_margin_end(20)
        
        # Fuente
        font_frame = Gtk.Frame()
        font_frame.set_label("Fuente")
        
        font_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        font_box.set_margin_top(10)
        font_box.set_margin_bottom(10)
        font_box.set_margin_start(10)
        font_box.set_margin_end(10)
        
        # Familia de fuente
        family_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        family_label = Gtk.Label(label="Familia:")
        family_label.set_width_chars(10)
        
        self.font_family_combo = Gtk.FontButton()
        self.font_family_combo.set_font(self.config["font_family"])
        self.font_family_combo.set_hexpand(True)
        
        family_box.append(family_label)
        family_box.append(self.font_family_combo)
        
        font_box.append(family_box)
        
        # Tamaño de fuente
        size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        size_label = Gtk.Label(label="Tamaño:")
        size_label.set_width_chars(10)
        
        self.font_size_spin = Gtk.SpinButton.new_with_range(8, 24, 1)
        self.font_size_spin.set_value(self.config["font_size"])
        
        size_box.append(size_label)
        size_box.append(self.font_size_spin)
        
        font_box.append(size_box)
        
        font_frame.set_child(font_box)
        page.append(font_frame)
        
        # Ruta de datos
        data_frame = Gtk.Frame()
        data_frame.set_label("Ruta de Datos")
        
        data_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        data_box.set_margin_top(10)
        data_box.set_margin_bottom(10)
        data_box.set_margin_start(10)
        data_box.set_margin_end(10)
        
        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.data_path_entry = Gtk.Entry()
        self.data_path_entry.set_text(self.config["data_path"])
        self.data_path_entry.set_hexpand(True)
        
        browse_button = Gtk.Button(label="Examinar")
        browse_button.connect("clicked", self.on_browse_data_path)
        
        path_box.append(self.data_path_entry)
        path_box.append(browse_button)
        
        data_box.append(path_box)
        
        warning_label = Gtk.Label(label="<i>Nota: Cambiar la ruta de datos requerirá reiniciar la aplicación.</i>")
        warning_label.set_use_markup(True)
        warning_label.set_halign(Gtk.Align.START)
        
        data_box.append(warning_label)
        
        data_frame.set_child(data_box)
        page.append(data_frame)
        
        # Tema
        theme_frame = Gtk.Frame()
        theme_frame.set_label("Tema")
        
        theme_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        theme_box.set_margin_top(10)
        theme_box.set_margin_bottom(10)
        theme_box.set_margin_start(10)
        theme_box.set_margin_end(10)
        
        self.theme_dark_radio = Gtk.CheckButton(label="Oscuro")
        self.theme_light_radio = Gtk.CheckButton(label="Claro")
        self.theme_light_radio.set_group(self.theme_dark_radio)
        
        if self.config["theme"] == "dark":
            self.theme_dark_radio.set_active(True)
        else:
            self.theme_light_radio.set_active(True)
        
        theme_box.append(self.theme_dark_radio)
        theme_box.append(self.theme_light_radio)
        
        theme_frame.set_child(theme_box)
        page.append(theme_frame)
        
        return page
        
    def on_browse_backup_path(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Seleccionar Carpeta de Respaldo",
            transient_for=self.parent,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Seleccionar", Gtk.ResponseType.OK)
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.backup_path_entry.set_text(dialog.get_file().get_path())
            
        dialog.destroy()
        
    def on_browse_data_path(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Seleccionar Carpeta de Datos",
            transient_for=self.parent,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Seleccionar", Gtk.ResponseType.OK)
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.data_path_entry.set_text(dialog.get_file().get_path())
            
        dialog.destroy()
        
    def on_create_backup(self, button):
        # Llamar al módulo de respaldo
        from modules.dexter_backup import BackupManager
        
        backup_manager = BackupManager(self.parent)
        success = backup_manager.create_backup(self.backup_path_entry.get_text())
        
        if success:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Respaldo Creado"
            )
            dialog.format_secondary_text(f"Se ha creado un respaldo en {self.backup_path_entry.get_text()}")
            dialog.run()
            dialog.destroy()
        
    def on_restore_backup(self, button):
        # Llamar al módulo de respaldo
        from modules.dexter_backup import BackupManager
        
        backup_manager = BackupManager(self.parent)
        
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
                success = backup_manager.restore_backup(backup_file)
                
                if success:
                    info_dialog = Gtk.MessageDialog(
                        transient_for=self.parent,
                        message_type=Gtk.MessageType.INFO,
                        buttons=Gtk.ButtonsType.OK,
                        text="Restauración Completada"
                    )
                    info_dialog.format_secondary_text("Se han restaurado los datos. La aplicación se reiniciará.")
                    info_dialog.run()
                    info_dialog.destroy()
                    
                    # Reiniciar la aplicación
                    self.parent.get_application().quit()
        else:
            dialog.destroy()
        
    def on_save_config(self, button):
        # Actualizar la configuración con los valores actuales
        self.config["backup_path"] = self.backup_path_entry.get_text()
        self.config["data_path"] = self.data_path_entry.get_text()
        
        font_desc = self.font_family_combo.get_font_desc()
        self.config["font_family"] = font_desc.get_family()
        
        self.config["font_size"] = self.font_size_spin.get_value_as_int()
        
        if self.theme_dark_radio.get_active():
            self.config["theme"] = "dark"
        else:
            self.config["theme"] = "light"
            
        # Guardar la configuración
        self.save_config()
        
        # Mostrar mensaje de éxito
        dialog = Gtk.MessageDialog(
            transient_for=self.parent,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Configuración Guardada"
        )
        dialog.format_secondary_text("La configuración se ha guardado correctamente. Algunos cambios pueden requerir reiniciar la aplicación.")
        dialog.run()
        dialog.destroy()
        
    def get_config(self):
        return self.config
