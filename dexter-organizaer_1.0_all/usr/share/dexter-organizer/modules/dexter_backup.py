#!/usr/bin/env python3

"""
Dexter Organizer - Módulo de copias de seguridad
Author: Victor Oubiña Faubel - oubinav78@gmail.com
Website: https://sourceforge.net/projects/dexter-gnome/
"""

import os
import time
import zipfile
import tempfile
import shutil
from gi.repository import Gtk, GLib

class DexterBackup:
    def __init__(self, app):
        """
        Inicializa el gestor de copias de seguridad.
        
        Args:
            app: Instancia principal de la aplicación DexterOrganizer
        """
        self.app = app
        self.window = app.window
        self.file_manager = app.file_manager
    
    def show_create_backup_dialog(self):
        """Muestra el diálogo para crear una copia de seguridad"""
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
            self._show_progress_dialog("Creando copia de seguridad", 
                                     "Creando copia de seguridad, por favor espere...",
                                     self._create_backup_task, folder_path)
        else:
            file_chooser.destroy()
    
    def show_restore_backup_dialog(self):
        """Muestra el diálogo para restaurar una copia de seguridad"""
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
            self._show_confirm_restore_dialog(backup_path)
        else:
            file_chooser.destroy()
    
    def _show_confirm_restore_dialog(self, backup_path):
        """Muestra el diálogo de confirmación para restaurar"""
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
            self._show_progress_dialog("Restaurando copia de seguridad", 
                                     "Restaurando copia de seguridad, por favor espere...",
                                     self._restore_backup_task, backup_path)
    
    def _show_progress_dialog(self, title, message, task_func, task_arg):
        """Muestra un diálogo de progreso para tareas largas"""
        progress_dialog = Gtk.Dialog(
            title=title,
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
        
        label = Gtk.Label(label=message)
        progress_bar = Gtk.ProgressBar()
        progress_bar.pulse()
        
        content_area.pack_start(label, False, False, 0)
        content_area.pack_start(progress_bar, False, False, 0)
        
        progress_dialog.show_all()
        
        # Mantener el progreso animado
        def pulse_progress():
            progress_bar.pulse()
            return True
        
        # Iniciar animación
        pulse_id = GLib.timeout_add(100, pulse_progress)
        
        # Iniciar tarea en segundo plano
        GLib.idle_add(lambda: self._run_task(task_func, task_arg, progress_dialog, pulse_id))
    
    def _run_task(self, task_func, task_arg, dialog, pulse_id):
        """Ejecuta una tarea en segundo plano"""
        result = task_func(task_arg)
        
        # Detener animación
        GLib.source_remove(pulse_id)
        
        # Cerrar diálogo
        dialog.destroy()
        
        # Mostrar resultado
        if result[0]:
            self.app.show_success_dialog(result[1])
        else:
            self.app.show_error_dialog(result[1])
        
        return False
    
    def _create_backup_task(self, folder_path):
        """Tarea para crear una copia de seguridad"""
        backup_path = self.file_manager.create_backup(folder_path)
        
        if backup_path:
            return (True, f"Copia de seguridad creada correctamente en:\n{backup_path}")
        else:
            return (False, "Error al crear la copia de seguridad.")
    
    def _restore_backup_task(self, backup_path):
        """Tarea para restaurar una copia de seguridad"""
        success = self.file_manager.restore_backup(backup_path)
        
        if success:
            # Recargar UI
            self.app.file_manager = self.file_manager  # Actualizar referencia
            self.app.categories = self.file_manager.categories
            self.app.load_categories()
            self.app.content_panel.set_visible_child_name("welcome")
            self.app.current_category = None
            self.app.current_document = None
            
            return (True, "Copia de seguridad restaurada correctamente.")
        else:
            return (False, "Error al restaurar la copia de seguridad.")
