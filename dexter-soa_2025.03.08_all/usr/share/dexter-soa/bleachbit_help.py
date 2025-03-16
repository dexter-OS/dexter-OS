#!/usr/bin/env python3
import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCharFormat, QColor, QFont, QTextCursor, QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLabel, QTextBrowser, QFrame)


class BleachBitHelpWindow(QMainWindow):
    """Ventana independiente para mostrar la ayuda de BleachBit"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BleachBit Help - Dexter-SOA")
        self.setWindowIcon(QIcon.fromTheme("dexter-soa"))
        self.setMinimumSize(900, 600)
        
        # Configurar ventana sin bordes
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        self.initUI()
        
        # Variables para mover la ventana sin bordes
        self.draggable = True
        self.dragPosition = None
    
    def initUI(self):
        """Inicializa la interfaz de usuario de la ventana de ayuda"""
        # Widget central con fondo transparente
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Contenedor principal con bordes redondeados
        main_container = QFrame()
        main_container.setObjectName("MainContainer")
        main_container.setFrameShape(QFrame.StyledPanel)
        
        # Layout del contenedor principal
        container_layout = QVBoxLayout(main_container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)
        
        # Título en la parte superior
        title_label = QLabel("BleachBit Configuration Guide for Dexter-SOA")
        title_label.setObjectName("TitleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title_label)
        
        # Área de texto para mostrar el contenido
        self.content_browser = QTextBrowser()
        self.content_browser.setObjectName("ContentBrowser")
        container_layout.addWidget(self.content_browser)
        
        # Botón Salir
        exit_button = QPushButton("Exit")
        exit_button.setObjectName("ExitButton")
        exit_button.clicked.connect(self.close)
        container_layout.addWidget(exit_button)
        
        # Añadir el contenedor principal al layout
        main_layout.addWidget(main_container)
        
        # Cargar el contenido de la ayuda
        self.load_help_content()

    def mousePressEvent(self, event):
        """Maneja el evento de click del mouse para permitir mover la ventana sin bordes"""
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos()
            event.accept()

    def mouseMoveEvent(self, event):
        """Maneja el evento de movimiento del mouse para mover la ventana sin bordes"""
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()
    
    def load_help_content(self):
        """Carga el contenido de la ayuda con formato de texto enriquecido"""
        # Limpiar contenido previo
        self.content_browser.clear()
        
        # Obtener el cursor para insertar texto
        cursor = self.content_browser.textCursor()
        
        # Definir formatos de texto
        def create_format(color, size, weight=QFont.Normal):
            fmt = QTextCharFormat()
            fmt.setFontWeight(weight)
            fmt.setFontPointSize(size)
            fmt.setForeground(QColor(*color))
            return fmt
        
        # Formatos predefinidos
        main_title_format = create_format((0, 255, 0), 16, QFont.Bold)  # Verde brillante
        subtitle_format = create_format((255, 0, 255), 14, QFont.Bold)  # Magenta
        normal_format = create_format((255, 255, 255), 12)  # Blanco
        list_title_format = create_format((0, 255, 255), 12, QFont.Bold)  # Cian
        list_desc_format = create_format((255, 255, 255), 12)  # Blanco
        code_format = create_format((100, 200, 100), 12)  # Verde claro
        warning_format = create_format((255, 100, 100), 12)  # Rojo suave
        
        def insert_section(cursor, title, content, title_format, content_format):
            """Insertar una sección con título y contenido"""
            cursor.insertText(title + "\n", title_format)
            cursor.insertText(content + "\n\n", content_format)
        
        def insert_numbered_list(cursor, items, title_format, desc_format):
            """Insertar una lista numerada"""
            for i, (title, description) in enumerate(items, 1):
                cursor.insertText(f"{i}. ", title_format)
                cursor.insertText(f"{title}: ", title_format)
                cursor.insertText(f"{description}\n", desc_format)
            cursor.insertText("\n", normal_format)
        
        # Advertencia inicial
        cursor.insertText("Initial Warning:\n", warning_format)
        cursor.insertText("BleachBit is a powerful tool that requires caution. Always create backups before performing deep cleanings.\n\n", warning_format)
        
        # Introducción
        insert_section(
            cursor, 
            "Introduction", 
            "This guide will help you correctly configure BleachBit to complement Dexter-SOA's cleaning functionality. BleachBit is an open-source tool designed to free up disk space and maintain privacy by eliminating unnecessary files.", 
            subtitle_format, 
            normal_format
        )
        
        # Modos de ejecución
        cursor.insertText("Execution Modes\n", subtitle_format)
        cursor.insertText("It is important to understand that BleachBit can be executed in two distinct modes:\n", normal_format)
        
        modes = [
            ("User Mode", "To clean personal files and configurations of the current user."),
            ("Root Mode (Administrator)", "To perform a deeper cleaning that includes system files.")
        ]
        insert_numbered_list(cursor, modes, list_title_format, list_desc_format)
        
        # Instalación
        insert_section(
            cursor, 
            "BleachBit Installation", 
            "You can install BleachBit using the following methods:", 
            subtitle_format, 
            normal_format
        )
        
        # Métodos de instalación
        insert_section(
            cursor, 
            "Method 1: Installation from Repositories", 
            "Use the following commands in the terminal:", 
            list_title_format, 
            normal_format
        )
        cursor.insertText("sudo apt update\n", code_format)
        cursor.insertText("sudo apt install bleachbit\n\n", code_format)
        
        insert_section(
            cursor, 
            "Method 2: Direct Download", 
            "Visit the official BleachBit website (https://www.bleachbit.org) and download the version compatible with your operating system.", 
            list_title_format, 
            normal_format
        )
        
        # Configuración Modo Usuario
        insert_section(
            cursor, 
            "BleachBit Configuration (User Mode)", 
            "Activate the following options for optimal configuration:", 
            subtitle_format, 
            normal_format
        )
        
        user_config_options = [
            "Hide irrelevant cleaners",
            "Overwrite file contents to prevent recovery",
            "Confirm before deleting",
            "Use IEC units (1 KiB = 1024 bytes)",
            "Enable dark mode",
            "Remember window dimensions"
        ]
        
        for option in user_config_options:
            cursor.insertText("✓ ", list_title_format)
            cursor.insertText(f"{option}\n", list_desc_format)
        cursor.insertText("\n", normal_format)
        
        # Configuración Modo Root
        insert_section(
            cursor, 
            "BleachBit Configuration (Root Mode)", 
            "To run BleachBit with administrator privileges:", 
            subtitle_format, 
            normal_format
        )
        
        cursor.insertText("Execution Command:\n", list_title_format)
        cursor.insertText("sudo bleachbit\n\n", code_format)
        
        # Precauciones
        cursor.insertText("Precautions in Root Mode:\n", warning_format)
        root_precautions = [
            "Always use the \"Preview\" function",
            "Avoid cleaning system memory unnecessarily",
            "Do not interrupt the cleaning process",
            "Create a backup before extensive cleanings"
        ]
        
        for precaution in root_precautions:
            cursor.insertText("⚠ ", warning_format)
            cursor.insertText(f"{precaution}\n", warning_format)
        cursor.insertText("\n", normal_format)
        
        # Uso conjunto con Dexter-SOA
        insert_section(
            cursor, 
            "Joint Use with Dexter-SOA", 
            "Follow this sequence for optimal results:", 
            subtitle_format, 
            normal_format
        )
        
        dexter_sequence = [
            "Run Dexter-SOA's \"Deep Cleaning\"",
            "Run BleachBit in user mode",
            "If necessary, run BleachBit in administrator mode",
            "Finish with Dexter-SOA's \"Update System\""
        ]
        
        for i, step in enumerate(dexter_sequence, 1):
            cursor.insertText(f"{i}. ", list_title_format)
            cursor.insertText(f"{step}\n", list_desc_format)
        cursor.insertText("\n", normal_format)
        
        # Solución de problemas
        insert_section(
            cursor, 
            "Troubleshooting", 
            "If you experience issues after using BleachBit:", 
            subtitle_format, 
            normal_format
        )
        
        troubleshooting_steps = [
            "Verify that you have not deleted important configuration files",
            "Consider reinstalling problematic programs",
            "Review system logs in /var/log/"
        ]
        
        for step in troubleshooting_steps:
            cursor.insertText("• ", list_title_format)
            cursor.insertText(f"{step}\n", list_desc_format)
        
        # Establecer el cursor al inicio
        cursor.movePosition(QTextCursor.Start)
        self.content_browser.setTextCursor(cursor)
        self.content_browser.verticalScrollBar().setValue(0)


# Función para mostrar la ventana de ayuda de BleachBit
def show_bleachbit_help():
    """Muestra la ventana de ayuda de BleachBit"""
    help_window = BleachBitHelpWindow()
    
    # Intentar cargar adicionalmente el estilo.qss si existe
    style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.qss")
    if os.path.exists(style_path):
        try:
            with open(style_path, 'r') as f:
                style = f.read()
            help_window.setStyleSheet(style)
        except Exception as e:
            print(f"Error al cargar el archivo de estilos: {str(e)}")
    
    help_window.show()
    
    # Devolvemos la ventana para que la aplicación principal pueda mantener una referencia
    return help_window


if __name__ == "__main__":
    # Este bloque permite probar el módulo de forma independiente
    app = QApplication(sys.argv)
    window = show_bleachbit_help()
    sys.exit(app.exec_())
