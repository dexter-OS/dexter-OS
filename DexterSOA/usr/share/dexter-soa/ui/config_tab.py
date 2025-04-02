#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pestaña para la configuración del sistema.
Permite configurar opciones de limpieza, actualizaciones y notificaciones.
"""

import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from utils.utils import _, load_config, save_config

class ConfigTab(Gtk.Box):
    """Pestaña de configuración del sistema"""
    
    def __init__(self, parent_window):
        """Inicializar la pestaña de configuración"""
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.parent_window = parent_window
        
        self.set_border_width(10)
        
        # Cargar configuración
        self.config = load_config()
        
        # Crear área de contenido principal
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        self.pack_start(content_box, True, True, 0)
        
        # Panel izquierdo (Opciones de limpieza)
        left_panel = self.create_cleanup_options()
        content_box.pack_start(left_panel, True, True, 0)
        
        # Panel derecho (Opciones del sistema)
        right_panel = self.create_system_options()
        content_box.pack_start(right_panel, True, True, 0)
        
        # Botones de acción
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_border_width(10)
        
        # Botón para guardar configuración
        save_button = Gtk.Button(label=_("Guardar Configuración"))
        save_button.connect("clicked", self.on_save_clicked)
        button_box.pack_end(save_button, False, False, 0)
        
        # Botón para restablecer configuración
        reset_button = Gtk.Button(label=_("Restablecer"))
        reset_button.connect("clicked", self.on_reset_clicked)
        button_box.pack_end(reset_button, False, False, 0)
        
        self.pack_end(button_box, False, False, 0)
    
    def create_cleanup_options(self):
        """Crear panel de opciones de limpieza"""
        frame = Gtk.Frame(label=_("Opciones de Limpieza"))
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)
        frame.add(vbox)
        
        # Checkbox: Ocultar limpiadores irrelevantes
        self.hide_irrelevant_check = Gtk.CheckButton(label=_("Ocultar limpiadores irrelevantes"))
        self.hide_irrelevant_check.set_tooltip_text(
            _("Ocultar limpiadores para aplicaciones no instaladas"))
        self.hide_irrelevant_check.set_active(
            self.config.get("cleanup", {}).get("hide_irrelevant_cleaners", True))
        vbox.pack_start(self.hide_irrelevant_check, False, False, 0)
        
        # Checkbox: Sobrescribir contenido
        self.overwrite_check = Gtk.CheckButton(label=_("Sobrescribir contenido de los archivos para evitar su recuperación"))
        self.overwrite_check.set_active(
            self.config.get("cleanup", {}).get("overwrite_files", False))
        vbox.pack_start(self.overwrite_check, False, False, 0)
        
        # Checkbox: Usar unidades IEC
        self.iec_units_check = Gtk.CheckButton(label=_("Usar unidades IEC (1 KiB = 1024 bytes) en vez de unidades SI (1 kB = 1000 bytes)"))
        self.iec_units_check.set_active(
            self.config.get("cleanup", {}).get("use_iec_units", True))
        vbox.pack_start(self.iec_units_check, False, False, 0)
        
        # Checkbox: Mostrar mensajes de depuración
        self.debug_check = Gtk.CheckButton(label=_("Mostrar mensajes de depuración"))
        self.debug_check.set_active(
            self.config.get("cleanup", {}).get("show_debug_messages", False))
        vbox.pack_start(self.debug_check, False, False, 0)
        
        # Separador
        vbox.pack_start(Gtk.Separator(), False, False, 10)
        
        # Número de kernels a mantener
        kernel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        kernel_label = Gtk.Label(label=_("Kernels a mantener:"), xalign=0)
        kernel_box.pack_start(kernel_label, False, False, 0)
        
        kernel_adjustment = Gtk.Adjustment(
            value=self.config.get("cleanup", {}).get("keep_kernels", 2),
            lower=1,
            upper=10,
            step_increment=1)
        self.kernel_spin = Gtk.SpinButton()
        self.kernel_spin.set_adjustment(kernel_adjustment)
        self.kernel_spin.set_value(self.config.get("cleanup", {}).get("keep_kernels", 2))
        kernel_box.pack_start(self.kernel_spin, False, False, 0)
        
        vbox.pack_start(kernel_box, False, False, 0)
        
        return frame
    
    def create_system_options(self):
        """Crear panel de opciones del sistema"""
        frame = Gtk.Frame(label=_("Opciones del Sistema"))
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(10)
        frame.add(vbox)
        
        # Intervalo de aviso para limpieza
        cleanup_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cleanup_label = Gtk.Label(label=_("Recordar limpieza cada:"), xalign=0)
        cleanup_box.pack_start(cleanup_label, False, False, 0)
        
        cleanup_adjustment = Gtk.Adjustment(
            value=self.config.get("system", {}).get("cleanup_reminder_days", 14),
            lower=1,
            upper=90,
            step_increment=1)
        self.cleanup_spin = Gtk.SpinButton()
        self.cleanup_spin.set_adjustment(cleanup_adjustment)
        self.cleanup_spin.set_value(self.config.get("system", {}).get("cleanup_reminder_days", 14))
        cleanup_box.pack_start(self.cleanup_spin, False, False, 0)
        
        cleanup_days_label = Gtk.Label(label=_("días"))
        cleanup_box.pack_start(cleanup_days_label, False, False, 0)
        
        vbox.pack_start(cleanup_box, False, False, 0)
        
        # Intervalo de comprobación de actualizaciones
        update_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        update_label = Gtk.Label(label=_("Comprobar actualizaciones cada:"), xalign=0)
        update_box.pack_start(update_label, False, False, 0)
        
        update_adjustment = Gtk.Adjustment(
            value=self.config.get("system", {}).get("update_check_interval_hours", 24),
            lower=1,
            upper=168,
            step_increment=1)
        self.update_spin = Gtk.SpinButton()
        self.update_spin.set_adjustment(update_adjustment)
        self.update_spin.set_value(self.config.get("system", {}).get("update_check_interval_hours", 24))
        update_box.pack_start(self.update_spin, False, False, 0)
        
        update_hours_label = Gtk.Label(label=_("horas"))
        update_box.pack_start(update_hours_label, False, False, 0)
        
        vbox.pack_start(update_box, False, False, 0)
        
        # Checkbox: Mostrar notificaciones de actualizaciones
        self.notify_updates_check = Gtk.CheckButton(label=_("Mostrar notificaciones de actualizaciones"))
        self.notify_updates_check.set_active(
            self.config.get("system", {}).get("update_notification", True))
        vbox.pack_start(self.notify_updates_check, False, False, 0)
        
        # Checkbox: Mostrar notificaciones de seguridad
        self.notify_security_check = Gtk.CheckButton(label=_("Notificar actualizaciones de seguridad"))
        self.notify_security_check.set_active(
            self.config.get("system", {}).get("notify_security_updates", True))
        vbox.pack_start(self.notify_security_check, False, False, 0)
        
        # Separador
        vbox.pack_start(Gtk.Separator(), False, False, 10)
        
        # Sección de copia de seguridad
        backup_label = Gtk.Label(label=_("Copias de Seguridad"), xalign=0)
        backup_label.set_markup("<b>" + _("Copias de Seguridad") + "</b>")
        vbox.pack_start(backup_label, False, False, 0)
        
        # Botones de backup
        backup_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        backup_button = Gtk.Button(label=_("Realizar Backup"))
        backup_button.connect("clicked", self.on_backup_clicked)
        backup_box.pack_start(backup_button, True, True, 0)
        
        restore_button = Gtk.Button(label=_("Restaurar Backup"))
        restore_button.connect("clicked", self.on_restore_clicked)
        backup_box.pack_start(restore_button, True, True, 0)
        
        vbox.pack_start(backup_box, False, False, 5)
        
        # Sección de idioma
        language_label = Gtk.Label(label=_("Idioma"), xalign=0)
        language_label.set_markup("<b>" + _("Idioma") + "</b>")
        vbox.pack_start(language_label, False, False, 10)
        
        # ComboBox para idiomas
        language_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        language_list_label = Gtk.Label(label=_("Seleccionar idioma:"), xalign=0)
        language_box.pack_start(language_list_label, False, False, 0)
        
        language_store = Gtk.ListStore(str, str)  # nombre, código
        language_store.append([_("Español (España)"), "es_ES"])
        language_store.append([_("Español (Latinoamérica)"), "es_419"])
        language_store.append([_("English (US)"), "en_US"])
        language_store.append([_("Français"), "fr_FR"])
        language_store.append([_("Deutsch"), "de_DE"])
        
        self.language_combo = Gtk.ComboBox.new_with_model(language_store)
        renderer_text = Gtk.CellRendererText()
        self.language_combo.pack_start(renderer_text, True)
        self.language_combo.add_attribute(renderer_text, "text", 0)
        
        # Establecer idioma activo
        current_language = self.config.get("language", "es_ES")
        active_index = 0
        
        for i, row in enumerate(language_store):
            if row[1] == current_language:
                active_index = i
                break
        
        self.language_combo.set_active(active_index)
        
        language_box.pack_start(self.language_combo, True, True, 0)
        vbox.pack_start(language_box, False, False, 0)
        
        return frame
    
    def on_save_clicked(self, button):
        """Manejar clic en botón de guardar configuración"""
        # Actualizar configuración de limpieza
        if "cleanup" not in self.config:
            self.config["cleanup"] = {}
        
        self.config["cleanup"]["hide_irrelevant_cleaners"] = self.hide_irrelevant_check.get_active()
        self.config["cleanup"]["overwrite_files"] = self.overwrite_check.get_active()
        self.config["cleanup"]["use_iec_units"] = self.iec_units_check.get_active()
        self.config["cleanup"]["show_debug_messages"] = self.debug_check.get_active()
        self.config["cleanup"]["keep_kernels"] = self.kernel_spin.get_value_as_int()
        
        # Actualizar configuración del sistema
        if "system" not in self.config:
            self.config["system"] = {}
        
        self.config["system"]["cleanup_reminder_days"] = self.cleanup_spin.get_value_as_int()
        self.config["system"]["update_check_interval_hours"] = self.update_spin.get_value_as_int()
        self.config["system"]["update_notification"] = self.notify_updates_check.get_active()
        self.config["system"]["notify_security_updates"] = self.notify_security_check.get_active()
        
        # Actualizar idioma
        active_iter = self.language_combo.get_active_iter()
        if active_iter is not None:
            model = self.language_combo.get_model()
            language_code = model[active_iter][1]
            self.config["language"] = language_code
        
        # Guardar configuración
        if save_config(self.config):
            self.show_message_dialog(
                _("Configuración guardada"),
                _("La configuración se ha guardado correctamente."),
                Gtk.MessageType.INFO
            )
        else:
            self.show_message_dialog(
                _("Error"),
                _("No se pudo guardar la configuración."),
                Gtk.MessageType.ERROR
            )
    
    def on_reset_clicked(self, button):
        """Manejar clic en botón de restablecer configuración"""
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_("¿Restablecer configuración?")
        )
        
        dialog.format_secondary_text(
            _("¿Está seguro de que desea restablecer la configuración a los valores predeterminados?"))
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Cargar configuración predeterminada
            from utils.utils import DEFAULT_CONFIG
            
            self.config = DEFAULT_CONFIG.copy()
            
            # Actualizar interfaz
            self.update_ui_from_config()
            
            # Guardar configuración
            if save_config(self.config):
                self.show_message_dialog(
                    _("Configuración restablecida"),
                    _("La configuración se ha restablecido a los valores predeterminados."),
                    Gtk.MessageType.INFO
                )
            else:
                self.show_message_dialog(
                    _("Error"),
                    _("No se pudo restablecer la configuración."),
                    Gtk.MessageType.ERROR
                )
    
    def update_ui_from_config(self):
        """Actualizar la interfaz según la configuración cargada"""
        # Opciones de limpieza
        self.hide_irrelevant_check.set_active(
            self.config.get("cleanup", {}).get("hide_irrelevant_cleaners", True))
        self.overwrite_check.set_active(
            self.config.get("cleanup", {}).get("overwrite_files", False))
        self.iec_units_check.set_active(
            self.config.get("cleanup", {}).get("use_iec_units", True))
        self.debug_check.set_active(
            self.config.get("cleanup", {}).get("show_debug_messages", False))
        self.kernel_spin.set_value(
            self.config.get("cleanup", {}).get("keep_kernels", 2))
        
        # Opciones del sistema
        self.cleanup_spin.set_value(
            self.config.get("system", {}).get("cleanup_reminder_days", 14))
        self.update_spin.set_value(
            self.config.get("system", {}).get("update_check_interval_hours", 24))
        self.notify_updates_check.set_active(
            self.config.get("system", {}).get("update_notification", True))
        self.notify_security_check.set_active(
            self.config.get("system", {}).get("notify_security_updates", True))
        
        # Idioma
        current_language = self.config.get("language", "es_ES")
        model = self.language_combo.get_model()
        active_index = 0
        
        for i, row in enumerate(model):
            if row[1] == current_language:
                active_index = i
                break
        
        self.language_combo.set_active(active_index)
    
    def on_backup_clicked(self, button):
        """Manejar clic en botón de realizar backup"""
        dialog = Gtk.FileChooserDialog(
            title=_("Guardar copia de seguridad"),
            parent=self.parent_window,
            action=Gtk.FileChooserAction.SAVE,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK
            )
        )
        
        dialog.set_current_name("dexter-soa-backup.json")
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            dialog.destroy()
            
            # Exportar configuración
            from utils.utils import export_config
            
            if export_config(self.config, filepath):
                self.show_message_dialog(
                    _("Copia de seguridad realizada"),
                    _("La copia de seguridad se ha guardado correctamente en:\n{0}").format(filepath),
                    Gtk.MessageType.INFO
                )
            else:
                self.show_message_dialog(
                    _("Error"),
                    _("No se pudo crear la copia de seguridad."),
                    Gtk.MessageType.ERROR
                )
        else:
            dialog.destroy()
    
    def on_restore_clicked(self, button):
        """Manejar clic en botón de restaurar backup"""
        dialog = Gtk.FileChooserDialog(
            title=_("Abrir archivo de copia de seguridad"),
            parent=self.parent_window,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
        )
        
        # Filtro para archivos JSON
        filter_json = Gtk.FileFilter()
        filter_json.set_name(_("Archivos JSON"))
        filter_json.add_pattern("*.json")
        dialog.add_filter(filter_json)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            dialog.destroy()
            
            # Importar configuración
            from utils.utils import import_config
            
            new_config = import_config(filepath)
            if new_config:
                self.config = new_config
                self.update_ui_from_config()
                
                # Guardar la configuración importada
                if save_config(self.config):
                    self.show_message_dialog(
                        _("Copia de seguridad restaurada"),
                        _("La configuración se ha restaurado correctamente."),
                        Gtk.MessageType.INFO
                    )
                else:
                    self.show_message_dialog(
                        _("Error"),
                        _("La copia de seguridad se importó pero no se pudo guardar."),
                        Gtk.MessageType.WARNING
                    )
            else:
                self.show_message_dialog(
                    _("Error"),
                    _("No se pudo restaurar la copia de seguridad."),
                    Gtk.MessageType.ERROR
                )
        else:
            dialog.destroy()
    
    def show_message_dialog(self, title, message, message_type):
        """Mostrar un diálogo de mensaje"""
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            flags=0,
            message_type=message_type,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()