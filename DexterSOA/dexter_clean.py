import sys
import threading
import os
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QPushButton, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt

class DexterClean(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DexterClean")
        self.setGeometry(100, 100, 800, 600)

        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        self.layout = QHBoxLayout(self.main_widget)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        # Contenedor izquierdo con el TreeView
        self.left_container = QWidget(self.main_widget)
        self.left_layout = QVBoxLayout(self.left_container)
        self.left_container.setMinimumWidth(350)
        self.layout.addWidget(self.left_container, 1)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemChanged.connect(self.handle_item_changed)
        self.left_layout.addWidget(self.tree)

        self.load_xml_files()

        # Contenedor derecho
        self.right_container = QWidget(self.main_widget)
        self.right_layout = QVBoxLayout(self.right_container)
        self.layout.addWidget(self.right_container, 3)

        # Terminal
        self.terminal = QTextEdit(self.right_container)
        self.terminal.setReadOnly(True)
        self.terminal.setText("Sistema listo para Limpiar")
        self.terminal.setMinimumHeight(400)
        self.right_layout.addWidget(self.terminal, 1)

        # Botón de limpieza
        self.clean_button = QPushButton("Limpiar Sistema")
        self.clean_button.clicked.connect(self.clean_system)
        self.right_layout.addWidget(self.clean_button)

    def load_xml_files(self):
        xml_dir = "cleaners"  # Carpeta donde están los XML
        if not os.path.exists(xml_dir):
            return
        
        for xml_file in os.listdir(xml_dir):
            if xml_file.endswith(".xml"):
                file_path = os.path.join(xml_dir, xml_file)
                self.parse_xml(file_path)

    def parse_xml(self, file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()
        label = root.find("label")
        if label is None:
            return
        
        parent = QTreeWidgetItem(self.tree, [label.text])
        parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
        parent.setCheckState(0, Qt.Unchecked)
        parent.setExpanded(True)

        for option in root.findall("option"):
            label = option.find("label")
            if label is not None:
                child = QTreeWidgetItem(parent, [label.text])
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Unchecked)

    def handle_item_changed(self, item, column):
        if item.parent() is None:  # Si es un elemento padre
            state = item.checkState(0)
            for i in range(item.childCount()):
                item.child(i).setCheckState(0, state)
        else:  # Si es un elemento hijo
            parent = item.parent()
            checked_children = sum(parent.child(i).checkState(0) == Qt.Checked for i in range(parent.childCount()))
            if checked_children == parent.childCount():
                parent.setCheckState(0, Qt.Checked)
            elif checked_children > 0:
                parent.setCheckState(0, Qt.PartiallyChecked)
            else:
                parent.setCheckState(0, Qt.Unchecked)

    def clean_system(self):
        self.terminal.clear()
        thread = threading.Thread(target=self.run_cleaning_process)
        thread.start()

    def run_cleaning_process(self):
        self.update_terminal("Proceso de limpieza en curso...")

    def update_terminal(self, message):
        self.terminal.append(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DexterClean()
    window.show()
    sys.exit(app.exec_())
