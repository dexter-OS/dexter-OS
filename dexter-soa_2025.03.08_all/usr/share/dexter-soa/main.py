#!/usr/bin/env python3
import sys
import os
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot, QSharedMemory, QSystemSemaphore
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QProgressBar, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

import system_clean
import system_update

# Clase para controlar instancia única
class SingleApplicationInstance:
    def __init__(self, key):
        self.key = key
        self.semaphore = QSystemSemaphore(key + "_semaphore", 1)
        self.semaphore.acquire()
        
        # Intenta eliminar memoria compartida si se cerró incorrectamente
        self.shared_memory = QSharedMemory(key + "_shared_memory")
        if self.shared_memory.attach():
            self.shared_memory.detach()
            
        self.is_running = self.shared_memory.attach()
        if not self.is_running:
            self.shared_memory.create(1)
        self.semaphore.release()

    def is_another_instance_running(self):
        return self.is_running

class UpdateWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    progress_val = pyqtSignal(int)

    @pyqtSlot()
    def run(self):
        try:
            self.progress.emit("Total Update executed\n")
            for message in system_update.actualizar_sistema():
                if message.startswith("Progress:"):
                    progress_value = int(message.replace("Progress: ", "").replace("%", ""))
                    self.progress_val.emit(progress_value)
                else:
                    self.progress.emit(message)
            self.progress.emit("\nMaintenance and Total Update completed.\n")
            self.progress_val.emit(0)
        except Exception as e:
            self.progress.emit(f"Unexpected error: {str(e)}")
        finally:
            self.finished.emit()

class CleanWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    progress_val = pyqtSignal(int)

    @pyqtSlot()
    def run(self):
        try:
            self.progress.emit("Starting Deep Cleaning\n")
            for message in system_clean.limpiar_sistema():
                if message.startswith("Progress:"):
                    progress_value = int(message.replace("Progress: ", "").replace("%", ""))
                    self.progress_val.emit(progress_value)
                else:
                    self.progress.emit(message)
            self.progress.emit("\nDeep Cleaning Completed\n")
            self.progress_val.emit(0)
        except Exception as e:
            self.progress.emit(f"Unexpected error: {str(e)}")
        finally:
            self.finished.emit()

# Creando una clase personalizada de QLabel para hacer clic en el texto
class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    
    def __init__(self, text=""):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dexter-SOA")
        self.setWindowIcon(QIcon.fromTheme("dexter-soa"))
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.initUI()
        # Agregar bandera para controlar proceso en ejecución
        self.process_running = False
        # Variable para mantener referencia a la ventana de ayuda
        self.help_window = None

    def initUI(self):
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        main_layout = QVBoxLayout()
        self.main_widget.setLayout(main_layout)

        self.title_label = QLabel("<font color='lightgreen'>Dexter-SOA</font>")
        self.title_label.setObjectName("TitleLabel")
        self.subtitle_label = QLabel("Cleaning and update tool for Debian systems")
        self.subtitle_label.setObjectName("SubtitleLabel")
        main_layout.addWidget(self.title_label, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.subtitle_label, alignment=Qt.AlignCenter)

        top_layout = QHBoxLayout()
        self.btn_actualizar = QPushButton("Update System")
        self.btn_limpiar = QPushButton("Deep Cleaning")
        top_layout.addWidget(self.btn_actualizar)
        top_layout.addWidget(self.btn_limpiar)
        main_layout.addLayout(top_layout)

        # Reemplazar el QLabel estándar con nuestro ClickableLabel personalizado
        self.label_bleachbit = ClickableLabel("FOR A DEEP CLEANING, IT IS RECOMMENDED TO HAVE <font color='yellow' style='font-size:16px;font-weight:bold;'><u>BLEACHBIT</u></font> INSTALLED AND CONFIGURED")
        self.label_bleachbit.setObjectName("LabelBleachbit")
        self.label_bleachbit.setAlignment(Qt.AlignCenter)
        # Conectar la señal de clic al método que abrirá el archivo de ayuda
        self.label_bleachbit.clicked.connect(self.open_bleachbit_help)
        main_layout.addWidget(self.label_bleachbit)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        main_layout.addWidget(self.terminal)

        self.btn_salir = QPushButton("Exit")
        main_layout.addWidget(self.btn_salir)
        self.btn_salir.clicked.connect(self.close)

        self.btn_actualizar.clicked.connect(self.handle_update)
        self.btn_limpiar.clicked.connect(self.handle_clean)

        self.setFixedSize(750, 600)

    def open_bleachbit_help(self):
        """Método para mostrar la ventana de ayuda de BleachBit"""
        try:
            # Importar el módulo de ayuda de BleachBit
            import bleachbit_help
            
            # Mostrar la ventana de ayuda
            self.help_window = bleachbit_help.show_bleachbit_help()
            
            # Registrar en el terminal
            self.terminal.append("BleachBit help window opened")
            
        except Exception as e:
            # En caso de error, mostrar un mensaje
            self.terminal.append(f"Error opening help window: {str(e)}")
            import traceback
            self.terminal.append(traceback.format_exc())

    def closeEvent(self, event):
        """Método para manejar el cierre de la ventana principal"""
        # Cerrar la ventana de ayuda de BleachBit si está abierta
        if hasattr(self, 'help_window') and self.help_window:
            try:
                self.help_window.close()
            except Exception as e:
                print(f"Error closing help window: {e}")
        
        # Continuar con el cierre normal de la ventana
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()

    def handle_update(self):
        # Verificar si ya hay un proceso en ejecución
        if self.process_running:
            return
            
        # Limpiar el terminal antes de iniciar el proceso
        self.terminal.clear()
        
        # Marcar que hay un proceso en ejecución
        self.process_running = True
        
        # Deshabilitar ambos botones durante el proceso
        self.btn_actualizar.setEnabled(False)
        self.btn_limpiar.setEnabled(False)
        
        self.update_thread = QThread()
        self.update_worker = UpdateWorker()
        self.update_worker.moveToThread(self.update_thread)

        self.update_thread.started.connect(self.update_worker.run)
        self.update_worker.finished.connect(self.update_thread.quit)
        self.update_worker.finished.connect(self.update_worker.deleteLater)
        self.update_thread.finished.connect(self.update_thread.deleteLater)
        self.update_thread.finished.connect(self.process_completed)

        self.update_worker.progress.connect(self.terminal.append)
        self.update_worker.progress_val.connect(self.progress_bar.setValue)

        self.update_thread.start()

    def handle_clean(self):
        # Verificar si ya hay un proceso en ejecución
        if self.process_running:
            return
        
        # Limpiar el terminal antes de iniciar el proceso
        self.terminal.clear()
            
        # Marcar que hay un proceso en ejecución
        self.process_running = True
        
        # Deshabilitar ambos botones durante el proceso
        self.btn_actualizar.setEnabled(False)
        self.btn_limpiar.setEnabled(False)
        
        self.clean_thread = QThread()
        self.clean_worker = CleanWorker()
        self.clean_worker.moveToThread(self.clean_thread)

        self.clean_thread.started.connect(self.clean_worker.run)
        self.clean_worker.finished.connect(self.clean_thread.quit)
        self.clean_worker.finished.connect(self.clean_worker.deleteLater)
        self.clean_thread.finished.connect(self.clean_thread.deleteLater)
        self.clean_thread.finished.connect(self.process_completed)

        self.clean_worker.progress.connect(self.terminal.append)
        self.clean_worker.progress_val.connect(self.progress_bar.setValue)

        self.clean_thread.start()
        
    def process_completed(self):
        # Resetear la bandera de proceso en ejecución
        self.process_running = False
        
        # Reactivar los botones
        self.btn_actualizar.setEnabled(True)
        self.btn_limpiar.setEnabled(True)

def main():
    app = QApplication(sys.argv)
    
    # Comprobar si la aplicación ya está en ejecución
    app_instance = SingleApplicationInstance("dexter_soa_application")
    if app_instance.is_another_instance_running():
        QMessageBox.warning(None, "Application Running", 
                           "Dexter-SOA is already running.\nCannot open another instance.")
        return
    
    # Obtener la ruta absoluta del archivo QSS
    qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.qss")
    
    try:
        with open(qss_path, "r") as f:
            style = f.read()
        app.setStyleSheet(style)
    except FileNotFoundError:
        print("Style file style.qss not found.")

    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
