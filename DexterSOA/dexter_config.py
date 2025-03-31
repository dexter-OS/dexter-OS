#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import sys
import subprocess
from PyQt5.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QCheckBox, QLabel, QPushButton, QTreeView, QHeaderView,
                           QFileDialog, QMessageBox, QScrollArea, QFrame, QListWidget,
                           QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem

# Directorio y archivo para guardar la configuración
CONFIG_DIR = os.path.expanduser("~/.config/dexter-soa")
CONFIG_FILE = os.path.join(CONFIG_DIR, "preferences.json")

# Constantes para los tipos de páginas de ubicaciones
LOCATIONS_WHITELIST = 1
LOCATIONS_CUSTOM = 2

class InitialConfigDialog(QDialog):
    """Diálogo de configuración inicial que se muestra solo la primera vez que se ejecuta la aplicación"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración por defecto
        self.config = {
            'hide_cleaners': True,
            'overwrite_files': True,
            'exit_after_clean': False,
            'confirm_delete': True,
            'use_iec': True,
            'remember_geometry': True,
            'show_debug': True,
            'whitelist_paths': [],
            'custom_paths': [],
            'shred_drives': [],
            'preserved_languages': ['es', 'en']
        }
        
        # Configuración básica de la ventana
        self.setWindowTitle("Configuración Inicial")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(600, 400)
        
        # Crear el widget principal con el estilo que aplicaremos
        self.main_widget = QWidget()
        self.main_widget.setObjectName("main_widget")
        
        # Layout para el diálogo general
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(self.main_widget)
        
        # Layout para el widget principal
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Título y descripción
        title_label = QLabel("Configuración Inicial de Dexter-SOA")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        
        desc_label = QLabel("Por favor, configure las opciones básicas para personalizar su experiencia.")
        desc_label.setObjectName("descriptionLabel")
        desc_label.setAlignment(Qt.AlignCenter)
        
        # Crear notebook (tab widget)
        self.notebook = QTabWidget()
        self.notebook.addTab(self.create_general_page(), "Generales")
        self.notebook.addTab(self.create_locations_page(LOCATIONS_CUSTOM), "Limpieza personalizada")
        self.notebook.addTab(self.create_drives_page(), "Unidades")
        self.notebook.addTab(self.create_languages_page(), "Idiomas")
        self.notebook.addTab(self.create_locations_page(LOCATIONS_WHITELIST), "Lista blanca")
        
        # Botones de acción
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setObjectName("actionButton")  # Mismo estilo que el botón de guardar
        self.btn_cancel.clicked.connect(self.handle_cancel)
        
        self.btn_save = QPushButton("Guardar y Continuar")
        self.btn_save.setObjectName("actionButton")
        self.btn_save.clicked.connect(self.accept)
        
        # Layout para botones
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_save)
        
        # Añadir componentes al layout principal
        main_layout.addWidget(title_label)
        main_layout.addWidget(desc_label)
        main_layout.addWidget(self.notebook)
        main_layout.addLayout(button_layout)
        
        # Para mover la ventana
        self.dragPos = None
        
    def create_general_page(self):
        """Crear página de opciones generales"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Opciones - Sin las que se han eliminado
        self.cb_hide_cleaners = QCheckBox("Ocultar los limpiadores irrelevantes")
        self.cb_hide_cleaners.setChecked(self.config.get('hide_cleaners', True))
        
        self.cb_overwrite_files = QCheckBox("Sobreescribir el contenido de los archivos para evitar su recuperación")
        self.cb_overwrite_files.setChecked(self.config.get('overwrite_files', True))
        
        self.cb_exit_after_clean = QCheckBox("Salir después de la limpieza")
        self.cb_exit_after_clean.setChecked(self.config.get('exit_after_clean', False))
        
        self.cb_confirm_delete = QCheckBox("Confirmar antes de eliminar")
        self.cb_confirm_delete.setChecked(self.config.get('confirm_delete', True))
        
        self.cb_use_iec = QCheckBox("Usar unidades IEC (1 KiB = 1024 bytes) en vez de unidades SI (1 kB = 1000 bytes)")
        self.cb_use_iec.setChecked(self.config.get('use_iec', True))
        
        self.cb_remember_geometry = QCheckBox("Recordar las dimensiones de la ventana")
        self.cb_remember_geometry.setChecked(self.config.get('remember_geometry', True))
        
        self.cb_show_debug = QCheckBox("Mostrar los mensajes de depuración")
        self.cb_show_debug.setChecked(self.config.get('show_debug', False))
        
        # Añadir widgets al layout
        layout.addWidget(self.cb_hide_cleaners)
        layout.addWidget(self.cb_overwrite_files)
        layout.addWidget(self.cb_exit_after_clean)
        layout.addWidget(self.cb_confirm_delete)
        layout.addWidget(self.cb_use_iec)
        layout.addWidget(self.cb_remember_geometry)
        layout.addWidget(self.cb_show_debug)
        
        layout.addStretch()
        page.setLayout(layout)
        return page
    
    def create_locations_page(self, page_type):
        """Crear página de ubicaciones (lista blanca o personalizada)"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Etiqueta informativa
        if page_type == LOCATIONS_WHITELIST:
            info_label = QLabel("No se eliminarán ni se modificarán estas rutas.")
        else:  # LOCATIONS_CUSTOM
            info_label = QLabel("Estas ubicaciones se pueden seleccionar para su eliminación.")

        # Mejorar la visibilidad del texto
        info_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(info_label)
        
        # Modelo para la vista de árbol
        self.locations_model = QStandardItemModel()
        self.locations_model.setHorizontalHeaderLabels(["Tipo", "Ruta"])
        
        # Vista de árbol
        self.locations_view = QTreeView()
        self.locations_view.setModel(self.locations_model)
        self.locations_view.setRootIsDecorated(False)
        self.locations_view.setAlternatingRowColors(True)
        self.locations_view.header().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Añadir vista de árbol al layout
        layout.addWidget(self.locations_view)
        
        # Botones
        button_layout = QHBoxLayout()
        
        # Estilo común para los botones
        button_style = """
            QPushButton {
                border-radius: 8px; 
                padding: 8px 15px; 
                background-color: #2a3d4d; 
                color: white;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3c6382;
            }
        """
        add_file_button = QPushButton("Añadir un archivo")
        add_file_button.setStyleSheet(button_style)

        add_folder_button = QPushButton("Añadir una carpeta")
        add_folder_button.setStyleSheet(button_style)

        remove_button = QPushButton("Eliminar")
        remove_button.setStyleSheet(button_style)
        
        # Conectar señales
        if page_type == LOCATIONS_WHITELIST:
            add_file_button.clicked.connect(lambda: self.add_location('file', LOCATIONS_WHITELIST))
            add_folder_button.clicked.connect(lambda: self.add_location('folder', LOCATIONS_WHITELIST))
            remove_button.clicked.connect(lambda: self.remove_location(LOCATIONS_WHITELIST))
        else:
            add_file_button.clicked.connect(lambda: self.add_location('file', LOCATIONS_CUSTOM))
            add_folder_button.clicked.connect(lambda: self.add_location('folder', LOCATIONS_CUSTOM))
            remove_button.clicked.connect(lambda: self.remove_location(LOCATIONS_CUSTOM))
        
        # Añadir botones al layout
        button_layout.addWidget(add_file_button)
        button_layout.addWidget(add_folder_button)
        button_layout.addWidget(remove_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        page.setLayout(layout)
        return page
    
    def create_drives_page(self):
        """Crear página de unidades"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Etiqueta informativa
        info_label = QLabel("Elija una carpeta con permisos de escritura para cada unidad para la que quiera sobreescribir el espacio libre.")
        info_label.setStyleSheet("color: white; font-size: 14px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Lista de unidades
        self.drives_list = QListWidget()
        self.drives_list.setAlternatingRowColors(True)
        
        layout.addWidget(self.drives_list)
        
        # Botones
        button_layout = QHBoxLayout()
        
        # Estilo común para los botones
        button_style = """
            QPushButton {
                border-radius: 8px; 
                padding: 8px 15px; 
                background-color: #2a3d4d; 
                color: white;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3c6382;
            }
        """

        add_button = QPushButton("Añadir")
        add_button.setStyleSheet(button_style)
        add_button.clicked.connect(self.add_drive)
        
        remove_button = QPushButton("Eliminar")
        remove_button.setStyleSheet(button_style)
        remove_button.clicked.connect(self.remove_drive)
        
        # Añadir botones al layout
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        page.setLayout(layout)
        return page
    
    def create_languages_page(self):
        """Crear página de idiomas"""
        page = QWidget()
        layout = QVBoxLayout()
        
        # Etiqueta informativa
        info_label = QLabel("Se eliminarán todos los idiomas excepto los marcados.")
        info_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(info_label)
        
        # Crear un modelo
        self.languages_model = QStandardItemModel()
        self.languages_model.setHorizontalHeaderLabels(["Conservar", "Código", "Nombre"])
        
        # Algunos idiomas de ejemplo (esto debería venir de tu sistema)
        languages = [
            ["es", "Español"],
            ["en", "English"],
            ["fr", "Français"],
            ["de", "Deutsch"],
            ["it", "Italiano"],
            ["pt", "Português"],
            ["ru", "Русский"],
            ["zh", "中文"],
            ["ja", "日本語"],
            ["ko", "한국어"]
        ]
        
        # Obtener los idiomas preservados
        preserved_languages = self.config.get('preserved_languages', ['es', 'en'])
        
        # Añadir idiomas al modelo
        for lang_code, lang_name in languages:
            preserve_item = QStandardItem()
            preserve_item.setCheckable(True)
            preserve_item.setCheckState(Qt.Checked if lang_code in preserved_languages else Qt.Unchecked)
            
            code_item = QStandardItem(lang_code)
            name_item = QStandardItem(lang_name)
            
            self.languages_model.appendRow([preserve_item, code_item, name_item])
        
        # Vista de árbol
        self.languages_view = QTreeView()
        self.languages_view.setModel(self.languages_model)
        self.languages_view.setRootIsDecorated(False)
        self.languages_view.setAlternatingRowColors(True)
        self.languages_view.header().setSectionResizeMode(2, QHeaderView.Stretch)
        
        # Añadir vista al layout
        layout.addWidget(self.languages_view)
        
        page.setLayout(layout)
        return page
    
    def add_location(self, location_type, page_type):
        """Añadir una ubicación (archivo o carpeta) usando el selector nativo"""
        path = ""
        
        try:
            if location_type == 'file':
                # Usar zenity para mostrar un diálogo de selección de archivo
                process = subprocess.Popen(
                    ["zenity", "--file-selection", "--title=Seleccionar archivo"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate()
                if process.returncode == 0:
                    path = stdout.decode('utf-8').strip()
            else:
                # Usar zenity para mostrar un diálogo de selección de carpeta
                process = subprocess.Popen(
                    ["zenity", "--file-selection", "--directory", "--title=Seleccionar carpeta"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate()
                if process.returncode == 0:
                    path = stdout.decode('utf-8').strip()
        except Exception as e:
            # Si falla zenity, usar el diálogo de Qt como respaldo
            if location_type == 'file':
                path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo")
            else:
                path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        
        if path:
            # Verificar si la ruta ya existe
            paths = self.config.get('whitelist_paths' if page_type == LOCATIONS_WHITELIST else 'custom_paths', [])
            for p in paths:
                if p[1] == path:
                    QMessageBox.warning(self, "Advertencia", "Esta ruta ya existe en la lista.")
                    return
            
            # Añadir a la lista
            type_str = "Archivo" if location_type == 'file' else "Carpeta"
            type_item = QStandardItem(type_str)
            path_item = QStandardItem(path)
            self.locations_model.appendRow([type_item, path_item])
            
            # Actualizar config
            paths.append([location_type, path])
            if page_type == LOCATIONS_WHITELIST:
                self.config['whitelist_paths'] = paths
            else:
                self.config['custom_paths'] = paths
    
    def remove_location(self, page_type):
        """Eliminar una ubicación"""
        indexes = self.locations_view.selectedIndexes()
        if indexes:
            # Obtener el índice de la fila
            row = indexes[0].row()
            
            # Obtener la ruta
            path = self.locations_model.item(row, 1).text()
            
            # Eliminar del modelo
            self.locations_model.removeRow(row)
            
            # Actualizar config
            paths = self.config.get('whitelist_paths' if page_type == LOCATIONS_WHITELIST else 'custom_paths', [])
            paths = [p for p in paths if p[1] != path]
            
            if page_type == LOCATIONS_WHITELIST:
                self.config['whitelist_paths'] = paths
            else:
                self.config['custom_paths'] = paths
    
    def add_drive(self):
        """Añadir una unidad"""
        try:
            # Usar zenity para mostrar un diálogo de selección de carpeta
            process = subprocess.Popen(
                ["zenity", "--file-selection", "--directory", "--title=Seleccionar carpeta para unidad"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                path = stdout.decode('utf-8').strip()
            else:
                # Si el usuario cancela zenity
                return
        except Exception as e:
            # Si falla zenity, usar el diálogo de Qt como respaldo
            path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para unidad")
        
        if path:
            # Verificar si la ruta ya existe
            drives = self.config.get('shred_drives', [])
            if path in drives:
                QMessageBox.warning(self, "Advertencia", "Esta ruta ya existe en la lista.")
                return
            
            # Añadir a la lista
            self.drives_list.addItem(path)
            
            # Actualizar config
            drives.append(path)
            self.config['shred_drives'] = drives
    
    def remove_drive(self):
        """Eliminar una unidad"""
        selected_items = self.drives_list.selectedItems()
        if selected_items:
            # Obtener la ruta
            path = selected_items[0].text()
            
            # Eliminar de la lista
            self.drives_list.takeItem(self.drives_list.row(selected_items[0]))
            
            # Actualizar config
            drives = self.config.get('shred_drives', [])
            drives.remove(path)
            self.config['shred_drives'] = drives
    
    def get_config(self):
        """Obtener la configuración actual"""
        # Valores por defecto para las opciones eliminadas
        self.config['check_updates'] = False
        self.config['check_beta'] = False
        self.config['dark_mode'] = True
        
        # Actualizar config con los valores de los widgets
        self.config['hide_cleaners'] = self.cb_hide_cleaners.isChecked()
        self.config['overwrite_files'] = self.cb_overwrite_files.isChecked()
        self.config['exit_after_clean'] = self.cb_exit_after_clean.isChecked()
        self.config['confirm_delete'] = self.cb_confirm_delete.isChecked()
        self.config['use_iec'] = self.cb_use_iec.isChecked()
        self.config['remember_geometry'] = self.cb_remember_geometry.isChecked()
        self.config['show_debug'] = self.cb_show_debug.isChecked()
        
        # Actualizar los idiomas preservados
        preserved_languages = []
        for row in range(self.languages_model.rowCount()):
            if self.languages_model.item(row, 0).checkState() == Qt.Checked:
                preserved_languages.append(self.languages_model.item(row, 1).text())
        
        self.config['preserved_languages'] = preserved_languages
        
        return self.config
    
    def save_config(self):
        """Guardar la configuración en un archivo"""
        # Crear directorio si no existe
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.get_config(), f, indent=4)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar la configuración: {e}")
            return False
    
    def accept(self):
        """Guardar configuración y cerrar diálogo"""
        if self.save_config():
            super().accept()
    
    def handle_cancel(self):
        """Manejar la cancelación: cerrar este diálogo pero permitir que la aplicación continúe"""
        self.reject()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'dragPos') and self.dragPos and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()


def show_if_first_run(parent=None):
    """
    Mostrar el diálogo de configuración inicial si es la primera ejecución.
    Retorna True si la configuración se guardó correctamente.
    """
    if not os.path.exists(CONFIG_FILE):
        dialog = InitialConfigDialog(parent)
        result = dialog.exec_()
        return result == QDialog.Accepted
    return True


# Para pruebas independientes
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Cargar estilo
    style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    
    # Mostrar diálogo como si fuera primera ejecución
    if show_if_first_run():
        print("Configuración guardada correctamente")
    else:
        print("Configuración cancelada o error")
    
    sys.exit(0)
