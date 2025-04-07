#!/usr/bin/env python3
"""
Módulo de configuración para Dexter-Organizer
Maneja configuraciones y respaldos del sistema
"""

import os
import json
import shutil
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import tempfile
from pathlib import Path

class DexterConfig:
    """Módulo para manejar configuraciones y respaldos de la aplicación"""
    
    def __init__(self, app):
        self.app = app
        self.config_dir = os.path.join(os.path.expanduser("~"), ".config", "dexter-organizer")
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.load_config()
    
    def load_config(self):
        """Cargar configuración desde archivo"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                self.config = {"theme": "light", "categories": [], "documents": {}}
                messagebox.showerror("Error", f"Error al cargar configuración: {str(e)}")
        else:
            self.config = {"theme": "light", "categories": [], "documents": {}}
    
    def save_config(self):
        """Guardar configuración actual"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar configuración: {str(e)}")
    
    def backup(self):
        """Crear respaldo de toda la aplicación"""
        try:
            backup_dir = filedialog.askdirectory(title="Seleccionar carpeta para guardar el respaldo")
            if not backup_dir:
                return
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            backup_file = os.path.join(backup_dir, f"dexter-organizer-backup-{timestamp}.zip")
            
            # Crear un archivo zip con la configuración
            shutil.make_archive(
                backup_file.replace('.zip', ''),
                'zip',
                self.config_dir
            )
            
            # Opcionalmente incluir copias de documentos
            include_docs = messagebox.askyesno(
                "Respaldo completo", 
                "¿Desea incluir copias de todos los documentos en el respaldo?\n\n" +
                "Esto puede aumentar significativamente el tamaño del archivo."
            )
            
            if include_docs:
                # Crear directorio temporal para incluir copias
                with tempfile.TemporaryDirectory() as tmpdirname:
                    # Copiar archivos de configuración
                    config_dir = os.path.join(tmpdirname, "config")
                    os.makedirs(config_dir, exist_ok=True)
                    
                    for root, dirs, files in os.walk(self.config_dir):
                        for file in files:
                            src_path = os.path.join(root, file)
                            dst_path = os.path.join(config_dir, file)
                            shutil.copy2(src_path, dst_path)
                    
                    # Copiar documentos
                    docs_dir = os.path.join(tmpdirname, "documents")
                    os.makedirs(docs_dir, exist_ok=True)
                    
                    doc_index = {}
                    
                    for category, docs in self.config.config["documents"].items():
                        category_dir = os.path.join(docs_dir, category)
                        os.makedirs(category_dir, exist_ok=True)
                        
                        doc_index[category] = {}
                        
                        for doc_id, doc_info in docs.items():
                            if os.path.exists(doc_info["path"]):
                                file_name = doc_info["name"]
                                dest_path = os.path.join(category_dir, file_name)
                                
                                # Si ya existe, añadir un sufijo
                                if os.path.exists(dest_path):
                                    base, ext = os.path.splitext(file_name)
                                    dest_path = os.path.join(category_dir, f"{base}_{doc_id}{ext}")
                                
                                try:
                                    shutil.copy2(doc_info["path"], dest_path)
                                    
                                    # Actualizar índice
                                    doc_index[category][doc_id] = {
                                        "original_path": doc_info["path"],
                                        "backup_path": os.path.join(category, os.path.basename(dest_path))
                                    }
                                except Exception as e:
                                    print(f"Error copiando {doc_info['path']}: {str(e)}")
                    
                    # Guardar índice
                    index_path = os.path.join(tmpdirname, "doc_index.json")
                    with open(index_path, 'w', encoding='utf-8') as f:
                        json.dump(doc_index, f, indent=4)
                    
                    # Crear archivo zip completo
                    full_backup_file = backup_file.replace('.zip', '_full.zip')
                    shutil.make_archive(
                        full_backup_file.replace('.zip', ''),
                        'zip',
                        tmpdirname
                    )
                    
                    backup_file = full_backup_file
            
            messagebox.showinfo("Respaldo", f"Respaldo creado exitosamente en:\n{backup_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear respaldo: {str(e)}")
    
    def restore_backup(self):
        """Restaurar desde un respaldo"""
        try:
            backup_file = filedialog.askopenfilename(
                title="Seleccionar archivo de respaldo",
                filetypes=[("Archivos ZIP", "*.zip")]
            )
            if not backup_file:
                return
            
            # Determinar si es respaldo completo (con documentos)
            is_full_backup = "_full.zip" in backup_file
            
            # Extraer respaldo
            with tempfile.TemporaryDirectory() as tmpdirname:
                shutil.unpack_archive(backup_file, tmpdirname, 'zip')
                
                if is_full_backup:
                    # Restaurar configuración
                    config_dir = os.path.join(tmpdirname, "config")
                    if os.path.exists(config_dir):
                        for file in os.listdir(config_dir):
                            src_path = os.path.join(config_dir, file)
                            dst_path = os.path.join(self.config_dir, file)
                            shutil.copy2(src_path, dst_path)
                    
                    # Preguntar sobre restauración de documentos
                    restore_docs = messagebox.askyesno(
                        "Restaurar documentos",
                        "Este respaldo contiene copias de documentos. ¿Desea restaurarlos?\n\n" +
                        "Esto copiará los documentos a sus ubicaciones originales cuando sea posible."
                    )
                    
                    if restore_docs:
                        # Leer índice de documentos
                        index_path = os.path.join(tmpdirname, "doc_index.json")
                        if os.path.exists(index_path):
                            with open(index_path, 'r', encoding='utf-8') as f:
                                doc_index = json.load(f)
                            
                            docs_dir = os.path.join(tmpdirname, "documents")
                            
                            for category, docs in doc_index.items():
                                for doc_id, paths in docs.items():
                                    original_path = paths["original_path"]
                                    backup_path = os.path.join(docs_dir, paths["backup_path"])
                                    
                                    # Verificar si la ruta original existe
                                    original_dir = os.path.dirname(original_path)
                                    if not os.path.exists(original_dir):
                                        # Preguntar nueva ubicación
                                        new_dir = filedialog.askdirectory(
                                            title=f"Seleccionar nueva ubicación para {os.path.basename(original_path)}",
                                            initialdir=os.path.expanduser("~")
                                        )
                                        
                                        if new_dir:
                                            original_path = os.path.join(new_dir, os.path.basename(original_path))
                                    
                                    # Copiar archivo
                                    try:
                                        os.makedirs(os.path.dirname(original_path), exist_ok=True)
                                        shutil.copy2(backup_path, original_path)
                                    except Exception as e:
                                        print(f"Error restaurando {backup_path} a {original_path}: {str(e)}")
                    
                else:
                    # Restauración simple (solo configuración)
                    config_file = os.path.join(tmpdirname, "config.json")
                    if os.path.exists(config_file):
                        shutil.copy2(config_file, self.config_file)
                
                self.load_config()
                messagebox.showinfo("Restauración", "Respaldo restaurado exitosamente")
        except Exception as e:
            messagebox.showerror("Error", f"Error al restaurar respaldo: {str(e)}")
