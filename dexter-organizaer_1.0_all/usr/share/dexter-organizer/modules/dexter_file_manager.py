#!/usr/bin/env python3

"""
Dexter Organizer - Módulo de gestión de archivos
Author: Victor Oubiña Faubel - oubinav78@gmail.com
Website: https://sourceforge.net/projects/dexter-gnome/
"""

import os
import json
import time
import shutil
import tempfile
import zipfile
from gi.repository import GLib

class DexterFileManager:
    def __init__(self, app):
        """
        Inicializa el gestor de archivos.
        
        Args:
            app: Instancia principal de la aplicación DexterOrganizer
        """
        self.app = app
        
        # Rutas de datos
        self.data_path = os.path.join(GLib.get_user_data_dir(), "dexter-organizer")
        self.data_file = os.path.join(self.data_path, "data.json")
        self.documents_path = os.path.join(self.data_path, "documents")
        
        # Asegurar que los directorios existan
        self._ensure_directories()
        
        # Cargar datos al iniciar
        self.categories = self.load_data()
        
    def _ensure_directories(self):
        """Asegura que existan los directorios necesarios"""
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
        
        if not os.path.exists(self.documents_path):
            os.makedirs(self.documents_path)
    
    def load_data(self):
        """Carga los datos de categorías y documentos"""
        categories = {}
        
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    categories = data.get('categories', {})
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error al cargar datos: {e}")
                categories = {}
        else:
            self.save_data(categories)
        
        return categories
    
    def save_data(self, categories=None):
        """Guarda los datos de categorías y documentos"""
        if categories is None:
            categories = self.categories
        
        try:
            with open(self.data_file, 'w') as f:
                json.dump({'categories': categories}, f, indent=4)
            return True
        except IOError as e:
            print(f"Error al guardar datos: {e}")
            return False
    
    def create_document(self, category_name, doc_name, doc_type):
        """
        Crea un nuevo documento
        
        Args:
            category_name: Nombre de la categoría
            doc_name: Nombre del documento
            doc_type: Tipo del documento (txt, md, html)
            
        Returns:
            doc_id: ID del documento creado, o None si hay error
        """
        # Verificar si la categoría existe
        if category_name not in self.categories:
            self.categories[category_name] = {}
        
        # Crear ID del documento
        doc_id = f"{doc_name.lower().replace(' ', '_')}_{GLib.get_monotonic_time()}"
        
        # Añadir a las categorías
        self.categories[category_name][doc_id] = {
            'name': doc_name,
            'type': doc_type,
            'created': GLib.get_monotonic_time()
        }
        
        # Crear archivo físico
        doc_path = os.path.join(self.documents_path, doc_id)
        try:
            with open(doc_path, 'w') as f:
                f.write("")
            
            # Guardar cambios
            self.save_data()
            return doc_id
        except IOError as e:
            print(f"Error al crear documento: {e}")
            return None
    
    def delete_document(self, category_name, doc_id):
        """
        Elimina un documento
        
        Args:
            category_name: Nombre de la categoría
            doc_id: ID del documento
            
        Returns:
            bool: True si se eliminó correctamente
        """
        if category_name not in self.categories or doc_id not in self.categories[category_name]:
            return False
        
        # Eliminar físicamente el archivo
        doc_path = os.path.join(self.documents_path, doc_id)
        try:
            if os.path.exists(doc_path):
                os.remove(doc_path)
        except OSError as e:
            print(f"Error al eliminar archivo: {e}")
            return False
        
        # Eliminar de los datos
        del self.categories[category_name][doc_id]
        self.save_data()
        return True
    
    def delete_category(self, category_name):
        """
        Elimina una categoría y todos sus documentos
        
        Args:
            category_name: Nombre de la categoría
            
        Returns:
            bool: True si se eliminó correctamente
        """
        if category_name not in self.categories:
            return False
        
        # Eliminar físicamente todos los archivos de la categoría
        for doc_id in self.categories[category_name]:
            doc_path = os.path.join(self.documents_path, doc_id)
            try:
                if os.path.exists(doc_path):
                    os.remove(doc_path)
            except OSError as e:
                print(f"Error al eliminar archivo: {e}")
        
        # Eliminar la categoría
        del self.categories[category_name]
        self.save_data()
        return True
    
    def create_backup(self, path):
        """
        Crea un backup de los datos y documentos
        
        Args:
            path: Ruta donde guardar el backup
            
        Returns:
            backup_path: Ruta completa del archivo de backup, o None si hay error
        """
        timestamp = time.strftime("%d-%m-%Y")
        backup_filename = f"Backup-Dexter-Organizer-{timestamp}.zip"
        backup_path = os.path.join(path, backup_filename)
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Añadir archivo data.json
                zipf.write(self.data_file, os.path.basename(self.data_file))
                
                # Añadir documentos
                for category_name, docs in self.categories.items():
                    for doc_id in docs:
                        doc_path = os.path.join(self.documents_path, doc_id)
                        if os.path.exists(doc_path):
                            zipf.write(doc_path, os.path.join('documents', doc_id))
            
            return backup_path
        except Exception as e:
            print(f"Error al crear backup: {e}")
            return None
    
    def restore_backup(self, backup_path):
        """
        Restaura un backup de los datos y documentos
        
        Args:
            backup_path: Ruta del archivo de backup
            
        Returns:
            bool: True si se restauró correctamente
        """
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Extraer en un directorio temporal
                temp_dir = tempfile.mkdtemp()
                zipf.extractall(temp_dir)
                
                # Restaurar data.json
                data_file_temp = os.path.join(temp_dir, os.path.basename(self.data_file))
                if os.path.exists(data_file_temp):
                    with open(data_file_temp, 'r') as f:
                        data = json.load(f)
                        self.categories = data.get('categories', {})
                    
                    # Copiar a ubicación final
                    shutil.copy2(data_file_temp, self.data_file)
                
                # Restaurar documentos
                docs_dir_temp = os.path.join(temp_dir, 'documents')
                if os.path.exists(docs_dir_temp):
                    for doc_id in os.listdir(docs_dir_temp):
                        doc_path_temp = os.path.join(docs_dir_temp, doc_id)
                        doc_path_final = os.path.join(self.documents_path, doc_id)
                        shutil.copy2(doc_path_temp, doc_path_final)
                
                # Limpiar
                shutil.rmtree(temp_dir)
                return True
        except Exception as e:
            print(f"Error al restaurar backup: {e}")
            return False
