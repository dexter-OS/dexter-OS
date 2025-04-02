#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para la gestión de limpieza del sistema.
Proporciona funciones para eliminar archivos temporales, cachés,
y realizar otras tareas de mantenimiento.
"""

import os
import subprocess
import re
import glob
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from collections import defaultdict
from utils.utils import execute_command, format_size, ensure_dirs_exist

class CleanupManager:
    """Gestor de limpieza del sistema"""
    
    def __init__(self, cleaners_dir=None):
        """
        Inicializar el gestor de limpieza
        
        Args:
            cleaners_dir: Directorio donde se encuentran los archivos XML de limpiadores
        """
        self.logger = logging.getLogger("DexterSOA.CleanupManager")
        
        # Directorio de limpiadores (archivos XML)
        self.cleaners_dir = cleaners_dir or "/usr/share/dexter-soa/cleaners"
        
        # Usar directorio relativo para entorno de desarrollo
        if not os.path.exists(self.cleaners_dir):
            dev_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cleaners")
            if os.path.exists(dev_dir):
                self.cleaners_dir = dev_dir
        
        # Cargar limpiadores disponibles
        self.available_cleaners = self.load_cleaners()
    
    def get_cleaner_files(self):
        """
        Obtiene la lista de archivos de limpiadores disponibles
        
        Returns:
            list: Lista de diccionarios con información de los archivos de limpiadores
        """
        cleaner_files = []
        
        if not os.path.exists(self.cleaners_dir):
            self.logger.warning(f"El directorio de limpiadores {self.cleaners_dir} no existe")
            return cleaner_files
        
        # Buscar archivos XML en el directorio de limpiadores
        for xml_file in glob.glob(os.path.join(self.cleaners_dir, "*.xml")):
            cleaner_files.append({
                "path": xml_file,
                "name": os.path.basename(xml_file)
            })
        
        return cleaner_files
    
    def parse_cleaner_file(self, file_path):
        """
        Parsea un archivo XML de limpiador y extrae su información
        
        Args:
            file_path: Ruta al archivo XML
            
        Returns:
            dict: Información del limpiador, o None si hay error
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            cleaner_id = root.get('id')
            if not cleaner_id:
                self.logger.warning(f"Archivo XML sin ID de limpiador: {file_path}")
                return None
            
            # Obtener información básica del limpiador
            label_elem = root.find('label')
            desc_elem = root.find('description')
            
            # Obtener categoría (si existe)
            category_elem = root.find('category')
            category = category_elem.text if category_elem is not None else "general"
            
            cleaner_info = {
                'id': cleaner_id,
                'label': label_elem.text if label_elem is not None else cleaner_id,
                'description': desc_elem.text if desc_elem is not None else "",
                'file': file_path,
                'category': category,
                'options': []
            }
            
            # Cargar opciones del limpiador
            for option in root.findall('option'):
                option_id = option.get('id')
                if not option_id:
                    continue
                
                option_label = option.find('label')
                option_desc = option.find('description')
                
                option_info = {
                    'id': option_id,
                    'label': option_label.text if option_label is not None else option_id,
                    'description': option_desc.text if option_desc is not None else "",
                    'actions': []
                }
                
                # Añadir esta opción a la lista de opciones del limpiador
                cleaner_info['options'].append(option_info)
            
            return cleaner_info
            
        except Exception as e:
            self.logger.error(f"Error al parsear archivo de limpiador {file_path}: {e}")
            return None
    
    def load_cleaners(self):
        """
        Cargar limpiadores disponibles desde archivos XML
        
        Returns:
            dict: Diccionario con información de limpiadores
        """
        cleaners = {}
        
        if not os.path.exists(self.cleaners_dir):
            self.logger.warning(f"El directorio de limpiadores {self.cleaners_dir} no existe")
            return cleaners
        
        # Buscar archivos XML en el directorio de limpiadores
        for xml_file in glob.glob(os.path.join(self.cleaners_dir, "*.xml")):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                cleaner_id = root.get('id')
                if not cleaner_id:
                    self.logger.warning(f"Archivo XML sin ID de limpiador: {xml_file}")
                    continue
                
                # Obtener información básica del limpiador
                label_elem = root.find('label')
                desc_elem = root.find('description')
                
                cleaner_info = {
                    'id': cleaner_id,
                    'label': label_elem.text if label_elem is not None else cleaner_id,
                    'description': desc_elem.text if desc_elem is not None else "",
                    'file': xml_file,
                    'options': []
                }
                
                # Cargar opciones del limpiador
                for option in root.findall('option'):
                    option_id = option.get('id')
                    if not option_id:
                        continue
                    
                    option_label = option.find('label')
                    option_desc = option.find('description')
                    
                    option_info = {
                        'id': option_id,
                        'label': option_label.text if option_label is not None else option_id,
                        'description': option_desc.text if option_desc is not None else "",
                        'actions': []
                    }
                    
                    # Cargar acciones de la opción
                    for action in option.findall('action'):
                        command = action.get('command')
                        path = action.get('path')
                        
                        if not command or not path:
                            continue
                        
                        option_info['actions'].append({
                            'command': command,
                            'path': path
                        })
                    
                    cleaner_info['options'].append(option_info)
                
                cleaners[cleaner_id] = cleaner_info
                
            except Exception as e:
                self.logger.error(f"Error al cargar limpiador desde {xml_file}: {e}")
        
        self.logger.info(f"Se cargaron {len(cleaners)} limpiadores")
        return cleaners
    
    def filter_irrelevant_cleaners(self, cleaners):
        """
        Filtra limpiadores que no son relevantes para el sistema actual.
        Por ejemplo, elimina limpiadores de Firefox si no está instalado.
        
        Args:
            cleaners: Lista de limpiadores a filtrar
            
        Returns:
            list: Lista filtrada de limpiadores relevantes
        """
        if not cleaners:
            return []
        
        # Detectar programas instalados
        installed_programs = self._detect_installed_programs()
        
        # Filtrar limpiadores
        filtered_cleaners = []
        for cleaner in cleaners:
            # Verificar si este limpiador es específico para algún programa
            program_specific = False
            
            # ID del limpiador puede indicar el programa (ej: firefox, chrome, etc)
            cleaner_id = cleaner.get('id', '').lower()
            
            # Programas conocidos a verificar
            programs_to_check = {
                'firefox': ['firefox', 'firefox-esr'],
                'chromium': ['chromium', 'chromium-browser'],
                'chrome': ['google-chrome', 'google-chrome-stable'],
                'opera': ['opera'],
                'libreoffice': ['libreoffice'],
                'thunderbird': ['thunderbird'],
                'vlc': ['vlc'],
                'gimp': ['gimp']
            }
            
            # Verificar si el limpiador es específico para un programa
            for prog_id, prog_names in programs_to_check.items():
                if prog_id in cleaner_id:
                    program_specific = True
                    # Verificar si el programa está instalado
                    if not any(prog in installed_programs for prog in prog_names):
                        # El programa no está instalado, ignorar este limpiador
                        self.logger.debug(f"Ignorando limpiador {cleaner_id} porque {prog_id} no está instalado")
                        break
                    else:
                        # El programa está instalado, incluir este limpiador
                        filtered_cleaners.append(cleaner)
                        break
            
            # Si no es específico para ningún programa, incluirlo siempre
            if not program_specific:
                filtered_cleaners.append(cleaner)
        
        return filtered_cleaners
    
    def _detect_installed_programs(self):
        """
        Detecta programas instalados en el sistema
        
        Returns:
            list: Lista de nombres de programas instalados
        """
        installed = set()
        
        # Verificar programas en el PATH
        path_dirs = os.environ.get('PATH', '').split(':')
        common_programs = [
            'firefox', 'firefox-esr', 'chromium', 'chromium-browser', 
            'google-chrome', 'opera', 'libreoffice', 'thunderbird',
            'vlc', 'gimp'
        ]
        
        for prog in common_programs:
            for path_dir in path_dirs:
                if os.path.exists(os.path.join(path_dir, prog)):
                    installed.add(prog)
                    break
        
        # Verificar con which para programas que pueden tener diferentes nombres
        for prog in common_programs:
            try:
                returncode, output = execute_command(['which', prog], shell=False)
                if returncode == 0 and output.strip():
                    installed.add(prog)
            except:
                pass
        
        return list(installed)
    
    def get_available_cleaners(self):
        """
        Obtener lista de limpiadores disponibles
        
        Returns:
            dict: Diccionario con información de limpiadores
        """
        return self.available_cleaners
    
    def analyze_disk_usage(self):
        """
        Analizar uso de disco en el sistema
        
        Returns:
            dict: Información de uso de disco
        """
        usage_info = {
            'total': 0,
            'used': 0,
            'free': 0,
            'percent': 0,
            'details': {}
        }
        
        try:
            # Obtener información de uso de disco para la partición raíz
            returncode, output = execute_command(['df', '-h', '/'], shell=False)
            
            if returncode == 0:
                lines = output.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 5:
                        usage_info['total'] = parts[1]
                        usage_info['used'] = parts[2]
                        usage_info['free'] = parts[3]
                        usage_info['percent'] = parts[4]
            
            # Analizar directorios específicos
            dirs_to_check = ['/var/cache', '/var/log', '/tmp', '/var/tmp']
            
            for dir_path in dirs_to_check:
                if os.path.exists(dir_path):
                    returncode, output = execute_command(['du', '-sh', dir_path], shell=False)
                    
                    if returncode == 0:
                        parts = output.split()
                        if len(parts) >= 1:
                            usage_info['details'][dir_path] = {
                                'size': parts[0]
                            }
            
            return usage_info
            
        except Exception as e:
            self.logger.error(f"Error al analizar uso de disco: {e}")
            return usage_info
    
    def perform_cleanup(self, selected_cleaners, callback=None):
        """
        Realizar limpieza del sistema
        
        Args:
            selected_cleaners: Lista de limpiadores/opciones seleccionados (formato: cleaner_id.option_id)
            callback: Función de callback para actualizar la interfaz
            
        Returns:
            dict: Resultados de la limpieza
        """
        results = {
            'success': True,
            'items_cleaned': 0,
            'space_freed': 0,
            'errors': [],
            'details': {}
        }
        
        if callback:
            callback("Iniciando proceso de limpieza...")
        
        self.logger.info(f"Iniciando limpieza con {len(selected_cleaners)} elementos seleccionados")
        
        for item_id in selected_cleaners:
            try:
                # Separar ID de limpiador y opción
                parts = item_id.split('.')
                
                if len(parts) != 2:
                    if callback:
                        callback(f"Error: ID de elemento inválido: {item_id}")
                    continue
                
                cleaner_id, option_id = parts
                
                # Verificar que el limpiador exista
                if cleaner_id not in self.available_cleaners:
                    if callback:
                        callback(f"Error: Limpiador no encontrado: {cleaner_id}")
                    continue
                
                cleaner = self.available_cleaners[cleaner_id]
                
                # Buscar la opción seleccionada
                selected_option = None
                for option in cleaner['options']:
                    if option['id'] == option_id:
                        selected_option = option
                        break
                
                if not selected_option:
                    if callback:
                        callback(f"Error: Opción no encontrada: {option_id} en limpiador {cleaner_id}")
                    continue
                
                # Registrar en resultados
                item_result = {
                    'name': f"{cleaner['label']} - {selected_option['label']}",
                    'success': True,
                    'items_cleaned': 0,
                    'space_freed': 0,
                    'errors': []
                }
                
                if callback:
                    callback(f"Limpiando {item_result['name']}...")
                
                # Ejecutar acciones de limpieza
                for action in selected_option['actions']:
                    command = action['command']
                    path = self._expand_path(action['path'])
                    
                    if command == 'delete':
                        # Obtener tamaño de archivos antes de eliminar
                        files = self._expand_glob(path)
                        size_before = self._get_files_size(files)
                        
                        # Eliminar archivos
                        if callback:
                            callback(f"  Eliminando archivos en {path}...")
                        
                        results_delete = self._delete_files(files, callback)
                        
                        item_result['items_cleaned'] += results_delete['count']
                        item_result['space_freed'] += results_delete['size']
                        
                        if results_delete['errors']:
                            item_result['errors'].extend(results_delete['errors'])
                    
                    elif command == 'truncate':
                        # Truncar archivos (establecer tamaño cero)
                        if callback:
                            callback(f"  Truncando archivos en {path}...")
                        
                        files = self._expand_glob(path)
                        size_before = self._get_files_size(files)
                        
                        results_truncate = self._truncate_files(files, callback)
                        
                        item_result['items_cleaned'] += results_truncate['count']
                        item_result['space_freed'] += size_before
                        
                        if results_truncate['errors']:
                            item_result['errors'].extend(results_truncate['errors'])
                    
                    elif command == 'script':
                        # Ejecutar script personalizado
                        if callback:
                            callback(f"  Ejecutando script {path}...")
                        
                        if os.path.exists(path) and os.access(path, os.X_OK):
                            returncode, output = execute_command([path], callback=callback, shell=False)
                            
                            if returncode != 0:
                                error_msg = f"Error al ejecutar script {path}: código {returncode}"
                                item_result['errors'].append(error_msg)
                                self.logger.error(error_msg)
                        else:
                            error_msg = f"Script no encontrado o no ejecutable: {path}"
                            item_result['errors'].append(error_msg)
                            self.logger.error(error_msg)
                
                # Actualizar resultado del item
                item_result['success'] = len(item_result['errors']) == 0
                
                # Añadir a resultados globales
                results['items_cleaned'] += item_result['items_cleaned']
                results['space_freed'] += item_result['space_freed']
                results['details'][item_id] = item_result
                
                if item_result['errors']:
                    results['errors'].extend(item_result['errors'])
                
                # Mostrar resumen
                if callback:
                    if item_result['success']:
                        callback(f"✓ {item_result['name']}: {item_result['items_cleaned']} elementos ({format_size(item_result['space_freed'])})")
                    else:
                        callback(f"✗ {item_result['name']}: {len(item_result['errors'])} errores")
                
            except Exception as e:
                error_msg = f"Error al procesar limpiador {item_id}: {e}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
                
                if callback:
                    callback(f"Error: {error_msg}")
        
        # Actualizar resultado global
        results['success'] = len(results['errors']) == 0
        
        # Mostrar resumen final
        if callback:
            callback("\nResumen de limpieza:")
            callback(f"Total elementos limpiados: {results['items_cleaned']}")
            callback(f"Espacio total liberado: {format_size(results['space_freed'])}")
            
            if results['errors']:
                callback(f"Se encontraron {len(results['errors'])} errores durante la limpieza")
        
        self.logger.info(f"Limpieza completada. {results['items_cleaned']} elementos, {format_size(results['space_freed'])} liberados")
        return results
    
    def _expand_path(self, path):
        """
        Expandir rutas con variables de entorno y ~
        
        Args:
            path: Ruta a expandir
            
        Returns:
            str: Ruta expandida
        """
        # Expandir ~ y variables de entorno
        expanded = os.path.expanduser(path)
        expanded = os.path.expandvars(expanded)
        return expanded
    
    def _expand_glob(self, path):
        """
        Expandir patrones glob en una ruta
        
        Args:
            path: Patrón de ruta
            
        Returns:
            list: Lista de rutas que coinciden con el patrón
        """
        expanded_path = self._expand_path(path)
        return glob.glob(expanded_path)
    
    def _get_files_size(self, files):
        """
        Obtener tamaño total de una lista de archivos
        
        Args:
            files: Lista de rutas de archivos
            
        Returns:
            int: Tamaño total en bytes
        """
        total_size = 0
        
        for file_path in files:
            try:
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
            except Exception as e:
                self.logger.error(f"Error al obtener tamaño de {file_path}: {e}")
        
        return total_size
    
    def _delete_files(self, files, callback=None):
        """
        Eliminar archivos de forma segura
        
        Args:
            files: Lista de rutas de archivos a eliminar
            callback: Función de callback para actualizar la interfaz
            
        Returns:
            dict: Resultados de la eliminación
        """
        results = {
            'count': 0,
            'size': 0,
            'errors': []
        }
        
        for file_path in files:
            try:
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    
                    # Eliminar archivo
                    os.remove(file_path)
                    
                    results['count'] += 1
                    results['size'] += size
                    
                    if callback and results['count'] % 10 == 0:
                        callback(f"    Eliminados {results['count']} archivos...")
            except Exception as e:
                error_msg = f"Error al eliminar archivo {file_path}: {e}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
        
        return results
    
    def _truncate_files(self, files, callback=None):
        """
        Truncar archivos (establecer tamaño cero)
        
        Args:
            files: Lista de rutas de archivos a truncar
            callback: Función de callback para actualizar la interfaz
            
        Returns:
            dict: Resultados de la operación
        """
        results = {
            'count': 0,
            'errors': []
        }
        
        for file_path in files:
            try:
                if os.path.isfile(file_path):
                    # Truncar archivo
                    with open(file_path, 'w') as f:
                        pass
                    
                    results['count'] += 1
                    
                    if callback and results['count'] % 10 == 0:
                        callback(f"    Truncados {results['count']} archivos...")
            except Exception as e:
                error_msg = f"Error al truncar archivo {file_path}: {e}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
        
        return results
    
    def remove_old_kernels(self, kernels_to_keep=2, callback=None):
        """
        Eliminar kernels antiguos
        
        Args:
            kernels_to_keep: Número de kernels a mantener (además del actual)
            callback: Función de callback para actualizar la interfaz
            
        Returns:
            (bool, str, list): Éxito/fracaso, mensaje y lista de kernels eliminados
        """
        if callback:
            callback("Buscando kernels instalados...")
        
        self.logger.info(f"Buscando kernels antiguos (manteniendo {kernels_to_keep})")
        
        try:
            # Obtener kernel actual
            returncode, current_kernel = execute_command(['uname', '-r'], shell=False)
            current_kernel = current_kernel.strip()
            
            if callback:
                callback(f"Kernel actual: {current_kernel}")
            
            # Listar todos los kernels instalados
            returncode, output = execute_command(['dpkg', '--list', 'linux-image*'], shell=False)
            
            kernel_packages = []
            kernel_regex = re.compile(r'linux-image-(\d+\.\d+\.\d+-\S+)')
            
            for line in output.split('\n'):
                if line.startswith('ii'):
                    parts = line.split()
                    if len(parts) >= 2:
                        package_name = parts[1]
                        match = kernel_regex.search(package_name)
                        
                        if match:
                            kernel_version = match.group(1)
                            kernel_packages.append({
                                'package': package_name,
                                'version': kernel_version,
                                'is_current': kernel_version == current_kernel
                            })
            
            # Ordenar por versión (más nuevo primero)
            kernel_packages.sort(key=lambda k: self._version_key(k['version']), reverse=True)
            
            if callback:
                callback("\nKernels instalados:")
                for kernel in kernel_packages:
                    callback(f"  {kernel['package']} {'(actual)' if kernel['is_current'] else ''}")
            
            # Determinar qué kernels eliminar
            kernels_to_remove = []
            kernels_to_check = [k for k in kernel_packages if not k['is_current']]
            
            # Mantener un número específico de kernels (además del actual)
            if len(kernels_to_check) > kernels_to_keep:
                kernels_to_remove = kernels_to_check[kernels_to_keep:]
            
            if not kernels_to_remove:
                if callback:
                    callback("\nNo hay kernels antiguos para eliminar.")
                
                return True, "No hay kernels antiguos para eliminar.", []
            
            # Mostrar kernels a eliminar
            if callback:
                callback(f"\nKernels a eliminar ({len(kernels_to_remove)}):")
                for kernel in kernels_to_remove:
                    callback(f"  {kernel['package']}")
            
            # Confirmar eliminación
            if callback:
                callback("\nEliminando kernels antiguos...")
            
            # Eliminar kernels antiguos
            removed_packages = []
            
            for kernel in kernels_to_remove:
                package = kernel['package']
                
                if callback:
                    callback(f"Eliminando {package}...")
                
                returncode, output = execute_command(['apt-get', 'purge', '-y', package], callback=callback, shell=False)
                
                if returncode == 0:
                    removed_packages.append(package)
                else:
                    error_msg = f"Error al eliminar kernel {package}: código {returncode}"
                    self.logger.error(error_msg)
                    
                    if callback:
                        callback(f"Error: {error_msg}")
            
            # Ejecutar autoremove para eliminar paquetes no necesarios
            if callback:
                callback("\nEjecutando autoremove para eliminar paquetes relacionados no necesarios...")
            
            returncode, output = execute_command(['apt-get', 'autoremove', '-y'], callback=callback, shell=False)
            
            # Resultado final
            if len(removed_packages) == len(kernels_to_remove):
                success_msg = f"Se eliminaron exitosamente {len(removed_packages)} kernels antiguos."
                if callback:
                    callback(f"\n✓ {success_msg}")
                
                self.logger.info(success_msg)
                return True, success_msg, removed_packages
            else:
                error_msg = f"Se eliminaron {len(removed_packages)} de {len(kernels_to_remove)} kernels antiguos."
                if callback:
                    callback(f"\n⚠ {error_msg}")
                
                self.logger.warning(error_msg)
                return len(removed_packages) > 0, error_msg, removed_packages
                
        except Exception as e:
            error_msg = f"Error al eliminar kernels antiguos: {e}"
            self.logger.error(error_msg)
            
            if callback:
                callback(f"Error: {error_msg}")
            
            return False, error_msg, []
    
    def _version_key(self, version):
        """
        Crear una clave para ordenar versiones de kernel
        
        Args:
            version: Cadena de versión (ej. "5.10.0-8-amd64")
            
        Returns:
            tuple: Clave para ordenar
        """
        # Dividir en componentes
        parts = version.split('-')
        version_nums = parts[0].split('.')
        
        # Convertir componentes numéricos
        key = []
        for part in version_nums:
            try:
                key.append(int(part))
            except ValueError:
                key.append(part)
        
        # Añadir componentes adicionales
        if len(parts) > 1:
            try:
                key.append(int(parts[1].split('-')[0]))
            except (ValueError, IndexError):
                key.append(parts[1])
        
        # Añadir arquitectura como el último componente
        if len(parts) > 2:
            key.append(parts[2])
        
        return tuple(key)
    
    def shred_files(self, files, passes=3, callback=None):
        """
        Destruir archivos de forma segura
        
        Args:
            files: Lista de rutas de archivos a destruir
            passes: Número de pasadas de sobrescritura
            callback: Función de callback para actualizar la interfaz
            
        Returns:
            (bool, str, int): Éxito/fracaso, mensaje y número de archivos destruidos
        """
        if callback:
            callback(f"Iniciando destrucción segura de {len(files)} archivos...")
        
        self.logger.info(f"Destruyendo {len(files)} archivos con {passes} pasadas")
        
        try:
            files_destroyed = 0
            errors = []
            
            for file_path in files:
                try:
                    if not os.path.exists(file_path):
                        if callback:
                            callback(f"Advertencia: El archivo no existe: {file_path}")
                        continue
                    
                    if os.path.isdir(file_path):
                        if callback:
                            callback(f"Advertencia: Es un directorio (use shred_directory): {file_path}")
                        continue
                    
                    if callback:
                        callback(f"Destruyendo: {file_path}")
                    
                    # Usar shred para destruir de forma segura
                    returncode, output = execute_command(['shred', '-vzn', str(passes), file_path], callback=callback, shell=False)
                    
                    if returncode == 0:
                        # Eliminar el archivo después de destruirlo
                        os.remove(file_path)
                        files_destroyed += 1
                    else:
                        error_msg = f"Error al destruir {file_path}: código {returncode}"
                        errors.append(error_msg)
                        self.logger.error(error_msg)
                        
                        if callback:
                            callback(f"Error: {error_msg}")
                
                except Exception as e:
                    error_msg = f"Error al procesar archivo {file_path}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
                    
                    if callback:
                        callback(f"Error: {error_msg}")
            
            # Resultado final
            if files_destroyed == len(files):
                success_msg = f"Se destruyeron exitosamente {files_destroyed} archivos."
                if callback:
                    callback(f"\n✓ {success_msg}")
                
                self.logger.info(success_msg)
                return True, success_msg, files_destroyed
            elif files_destroyed > 0:
                partial_msg = f"Se destruyeron {files_destroyed} de {len(files)} archivos."
                if callback:
                    callback(f"\n⚠ {partial_msg}")
                
                self.logger.warning(partial_msg)
                return True, partial_msg, files_destroyed
            else:
                error_msg = "No se pudo destruir ningún archivo."
                if callback:
                    callback(f"\n✗ {error_msg}")
                
                self.logger.error(error_msg)
                return False, error_msg, 0
                
        except Exception as e:
            error_msg = f"Error al destruir archivos: {e}"
            self.logger.error(error_msg)
            
            if callback:
                callback(f"Error: {error_msg}")
            
            return False, error_msg, 0
    
    def shred_directory(self, directory, passes=3, callback=None):
        """
        Destruir una carpeta y su contenido de forma segura
        
        Args:
            directory: Ruta del directorio a destruir
            passes: Número de pasadas de sobrescritura
            callback: Función de callback para actualizar la interfaz
            
        Returns:
            (bool, str, int): Éxito/fracaso, mensaje y número de archivos destruidos
        """
        if not os.path.exists(directory):
            error_msg = f"El directorio no existe: {directory}"
            if callback:
                callback(f"Error: {error_msg}")
            
            self.logger.error(error_msg)
            return False, error_msg, 0
        
        if not os.path.isdir(directory):
            error_msg = f"La ruta no es un directorio: {directory}"
            if callback:
                callback(f"Error: {error_msg}")
            
            self.logger.error(error_msg)
            return False, error_msg, 0
        
        if callback:
            callback(f"Destruyendo directorio: {directory}")
            callback("Recopilando archivos...")
        
        try:
            # Recopilar todos los archivos dentro del directorio
            files = []
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
            
            if callback:
                callback(f"Se encontraron {len(files)} archivos para destruir")
            
            # Destruir los archivos
            success, message, files_destroyed = self.shred_files(files, passes, callback)
            
            # Eliminar directorios vacíos
            if callback:
                callback("Eliminando directorios vacíos...")
            
            for root, dirs, files in os.walk(directory, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        os.rmdir(dir_path)
                    except OSError:
                        # No está vacío, ignorar
                        pass
            
            # Eliminar el directorio principal si está vacío
            try:
                os.rmdir(directory)
                if callback:
                    callback(f"Directorio eliminado: {directory}")
            except OSError as e:
                if callback:
                    callback(f"No se pudo eliminar el directorio principal (puede no estar vacío): {e}")
            
            return success, message, files_destroyed
            
        except Exception as e:
            error_msg = f"Error al destruir directorio {directory}: {e}"
            self.logger.error(error_msg)
            
            if callback:
                callback(f"Error: {error_msg}")
            
            return False, error_msg, 0
    
    def clean_free_space(self, mount_point, passes=1, callback=None):
        """
        Limpiar espacio libre en un sistema de archivos
        
        Args:
            mount_point: Punto de montaje del sistema de archivos
            passes: Número de pasadas de sobrescritura
            callback: Función de callback para actualizar la interfaz
            
        Returns:
            (bool, str): Éxito/fracaso y mensaje
        """
        if not os.path.exists(mount_point):
            error_msg = f"El punto de montaje no existe: {mount_point}"
            if callback:
                callback(f"Error: {error_msg}")
            
            self.logger.error(error_msg)
            return False, error_msg
        
        if callback:
            callback(f"Limpiando espacio libre en: {mount_point}")
            callback("Este proceso puede tardar mucho tiempo dependiendo del tamaño del sistema de archivos...")
        
        try:
            # Crear un directorio temporal
            temp_dir = os.path.join(mount_point, ".tmp_wipe_freespace")
            os.makedirs(temp_dir, exist_ok=True)
            
            if callback:
                callback(f"Creado directorio temporal: {temp_dir}")
            
            # Crear un archivo grande para llenar el espacio libre
            temp_file = os.path.join(temp_dir, "wipe_file")
            
            if callback:
                callback("Creando archivo para llenar espacio libre...")
            
            # Usar dd para llenar el espacio libre
            returncode, output = execute_command([
                'dd', 'if=/dev/zero', f'of={temp_file}', 'bs=1M', 
                'conv=fdatasync'
            ], callback=callback, shell=False)
            
            # No importa si falla por falta de espacio, eso es lo que queremos
            if callback:
                callback("Sobrescribiendo archivo...")
            
            # Usar shred para sobrescribir el archivo
            returncode, output = execute_command([
                'shred', '-vzn', str(passes), temp_file
            ], callback=callback, shell=False)
            
            # Limpiar
            if callback:
                callback("Limpiando archivos temporales...")
            
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            
            success_msg = f"Se limpió el espacio libre en {mount_point} satisfactoriamente."
            if callback:
                callback(f"\n✓ {success_msg}")
            
            self.logger.info(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Error al limpiar espacio libre en {mount_point}: {e}"
            self.logger.error(error_msg)
            
            if callback:
                callback(f"Error: {error_msg}")
            
            # Intentar limpiar archivos temporales en caso de error
            try:
                if 'temp_file' in locals() and os.path.exists(temp_file):
                    os.remove(temp_file)
                
                if 'temp_dir' in locals() and os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass
            
            return False, error_msg