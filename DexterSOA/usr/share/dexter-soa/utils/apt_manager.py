#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para la gestión de paquetes APT, preferencias y configuraciones.
Gestiona los archivos pref para bloquear o priorizar paquetes.
"""

import os
import subprocess
import re
import logging
from utils.utils import execute_command, ensure_dirs_exist

class AptManager:
    """Gestor de paquetes y configuraciones APT"""
    
    def __init__(self):
        """Inicializar el gestor de APT"""
        self.logger = logging.getLogger("DexterSOA.AptManager")
        
        # Directorios para archivos de configuración de APT
        self.apt_conf_dir = "/etc/apt/preferences.d"
        self.apt_sources_dir = "/etc/apt/sources.list.d"
        
        # Verificar rutas
        self._verify_paths()
    
    def _verify_paths(self):
        """Verificar que las rutas necesarias existan"""
        # Solo verificamos que existan las rutas de solo lectura
        if not os.path.exists(self.apt_conf_dir):
            self.logger.warning(f"El directorio {self.apt_conf_dir} no existe")
        
        if not os.path.exists(self.apt_sources_dir):
            self.logger.warning(f"El directorio {self.apt_sources_dir} no existe")
    
    def get_updates(self):
        """
        Obtener la lista de actualizaciones disponibles
        
        Returns:
            list: Lista de paquetes por actualizar
        """
        self.logger.info("Obteniendo actualizaciones disponibles")
        
        # Actualizar índices
        self.logger.debug("Actualizando índices de paquetes")
        returncode, output = execute_command(['apt-get', 'update'], shell=False)
        if returncode != 0:
            self.logger.error(f"Error al actualizar índices: {output}")
            return []
        
        # Obtener lista de paquetes actualizables
        self.logger.debug("Obteniendo lista de paquetes actualizables")
        returncode, output = execute_command(['apt-get', 'upgrade', '--dry-run'], shell=False)
        if returncode != 0:
            self.logger.error(f"Error al obtener paquetes actualizables: {output}")
            return []
        
        # Procesar la salida para extraer los paquetes
        packages = []
        package_pattern = re.compile(r'Inst\s+(\S+)\s+\[([^\]]+)\]\s+\(([^)]+)\s+')
        for line in output.split('\n'):
            if line.startswith('Inst'):
                match = package_pattern.search(line)
                if match:
                    package = {
                        'name': match.group(1),
                        'current_version': match.group(2),
                        'new_version': match.group(3).strip()
                    }
                    packages.append(package)
        
        self.logger.info(f"Se encontraron {len(packages)} paquetes por actualizar")
        return packages
    
    def perform_update(self, callback=None):
        """
        Realiza la actualización del sistema
        
        Args:
            callback: Función de callback para actualizar la interfaz
        
        Returns:
            (bool, str): Tupla con éxito/fracaso y mensaje
        """
        self.logger.info("Iniciando actualización del sistema")
        
        # Actualizar índices
        if callback:
            callback("Actualizando índices de paquetes...")
        
        returncode, output = execute_command(['apt-get', 'update'], callback=callback, shell=False)
        if returncode != 0:
            self.logger.error(f"Error al actualizar índices: {output}")
            return False, "Error al actualizar índices de paquetes"
        
        # Actualizar paquetes
        if callback:
            callback("\nActualizando paquetes...")
        
        returncode, output = execute_command(['apt-get', 'upgrade', '-y'], callback=callback, shell=False)
        if returncode != 0:
            self.logger.error(f"Error al actualizar paquetes: {output}")
            return False, "Error al actualizar paquetes"
        
        self.logger.info("Actualización del sistema completada")
        return True, "Actualización del sistema completada con éxito"
    
    def get_pref_files(self):
        """
        Obtener lista de archivos de preferencias de APT
        
        Returns:
            list: Lista de archivos encontrados
        """
        pref_files = []
        
        if os.path.exists(self.apt_conf_dir):
            for file in os.listdir(self.apt_conf_dir):
                if file.endswith('.pref'):
                    pref_files.append(file)
        
        return pref_files
    
    def save_pref_file(self, filename, content):
        """
        Guardar un archivo de preferencias de APT
        
        Args:
            filename: Nombre del archivo (debe terminar en .pref)
            content: Contenido del archivo
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        if not filename.endswith('.pref'):
            filename += '.pref'
        
        file_path = os.path.join(self.apt_conf_dir, filename)
        
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Error al guardar archivo de preferencias: {e}")
            return False
    
    def delete_pref_file(self, filename):
        """
        Eliminar un archivo de preferencias de APT
        
        Args:
            filename: Nombre del archivo a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        file_path = os.path.join(self.apt_conf_dir, filename)
        
        if not os.path.exists(file_path):
            return False
        
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            self.logger.error(f"Error al eliminar archivo de preferencias: {e}")
            return False
    
    def get_blocked_packages(self):
        """
        Obtener lista de paquetes bloqueados
        
        Returns:
            list: Lista de paquetes bloqueados
        """
        blocked_packages = []
        
        # Buscar en archivos .pref
        for pref_file in self.get_pref_files():
            file_path = os.path.join(self.apt_conf_dir, pref_file)
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Buscar paquetes bloqueados (prioridad negativa)
                package_blocks = re.finditer(r'Package:\s*([^\n]+)\s*\nPin:\s*([^\n]+)\s*\nPin-Priority:\s*(-\d+)', content)
                
                for match in package_blocks:
                    package_name = match.group(1).strip()
                    pin = match.group(2).strip()
                    priority = int(match.group(3).strip())
                    
                    if priority < 0:
                        blocked_packages.append({
                            'name': package_name,
                            'pin': pin,
                            'priority': priority,
                            'file': pref_file
                        })
            except Exception as e:
                self.logger.error(f"Error al leer archivo de preferencias {pref_file}: {e}")
        
        return blocked_packages
    
    def get_priority_packages(self):
        """
        Obtener lista de paquetes con prioridad
        
        Returns:
            list: Lista de paquetes con prioridad
        """
        priority_packages = []
        
        # Buscar en archivos .pref
        for pref_file in self.get_pref_files():
            file_path = os.path.join(self.apt_conf_dir, pref_file)
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Buscar paquetes con prioridad positiva
                package_priorities = re.finditer(r'Package:\s*([^\n]+)\s*\nPin:\s*([^\n]+)\s*\nPin-Priority:\s*(\d+)', content)
                
                for match in package_priorities:
                    package_name = match.group(1).strip()
                    pin = match.group(2).strip()
                    priority = int(match.group(3).strip())
                    
                    if priority > 0:
                        priority_packages.append({
                            'name': package_name,
                            'pin': pin,
                            'priority': priority,
                            'file': pref_file
                        })
            except Exception as e:
                self.logger.error(f"Error al leer archivo de preferencias {pref_file}: {e}")
        
        return priority_packages
    
    def add_blocked_package(self, package_name, file_name="dexter-blocked.pref"):
        """
        Añadir un paquete a la lista de bloqueados
        
        Args:
            package_name: Nombre del paquete a bloquear
            file_name: Archivo donde añadirlo
            
        Returns:
            bool: True si se añadió correctamente, False en caso contrario
        """
        file_path = os.path.join(self.apt_conf_dir, file_name)
        
        # Crear contenido para bloqueo
        package_block = f"""# Paquete bloqueado por DexterSOA
Package: {package_name}
Pin: version *
Pin-Priority: -1

"""
        
        try:
            # Verificar si el archivo existe, si no, crearlo
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write("# Archivo de preferencias de APT generado por DexterSOA\n\n")
            
            # Añadir el bloqueo al archivo
            with open(file_path, 'a') as f:
                f.write(package_block)
            
            return True
        except Exception as e:
            self.logger.error(f"Error al añadir paquete bloqueado: {e}")
            return False
    
    def add_priority_package(self, package_name, origin, priority, file_name="dexter-priority.pref"):
        """
        Añadir un paquete a la lista de prioridades
        
        Args:
            package_name: Nombre del paquete
            origin: Origen para el Pin
            priority: Valor de prioridad
            file_name: Archivo donde añadirlo
            
        Returns:
            bool: True si se añadió correctamente, False en caso contrario
        """
        file_path = os.path.join(self.apt_conf_dir, file_name)
        
        # Crear contenido para prioridad
        package_priority = f"""# Paquete con prioridad establecida por DexterSOA
Package: {package_name}
Pin: {origin}
Pin-Priority: {priority}

"""
        
        try:
            # Verificar si el archivo existe, si no, crearlo
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write("# Archivo de preferencias de APT generado por DexterSOA\n\n")
            
            # Añadir la prioridad al archivo
            with open(file_path, 'a') as f:
                f.write(package_priority)
            
            return True
        except Exception as e:
            self.logger.error(f"Error al añadir paquete con prioridad: {e}")
            return False
    
    def remove_package_from_pref(self, package_name, file_name):
        """
        Eliminar un paquete de un archivo de preferencias
        
        Args:
            package_name: Nombre del paquete a eliminar
            file_name: Archivo de donde eliminarlo
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        file_path = os.path.join(self.apt_conf_dir, file_name)
        
        if not os.path.exists(file_path):
            return False
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Buscar y eliminar el bloque correspondiente al paquete
            # Patrón para buscar el bloque completo de un paquete
            pattern = r'(?m)^# Paquete[^\n]*\nPackage:\s*' + re.escape(package_name) + r'\s*\nPin:[^\n]*\nPin-Priority:[^\n]*\n\n?'
            
            # Si no incluye el comentario
            if not re.search(pattern, content):
                pattern = r'(?m)^Package:\s*' + re.escape(package_name) + r'\s*\nPin:[^\n]*\nPin-Priority:[^\n]*\n\n?'
            
            # Aplicar la eliminación
            new_content = re.sub(pattern, '', content)
            
            # Guardar el archivo actualizado
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            return True
        except Exception as e:
            self.logger.error(f"Error al eliminar paquete de archivo de preferencias: {e}")
            return False
    
    def install_package(self, package_name, callback=None):
        """
        Instalar un paquete
        
        Args:
            package_name: Nombre del paquete a instalar
            callback: Función de callback para actualizar la interfaz
            
        Returns:
            (bool, str): Tupla con éxito/fracaso y mensaje
        """
        self.logger.info(f"Instalando paquete: {package_name}")
        
        if callback:
            callback(f"Instalando paquete: {package_name}...")
        
        returncode, output = execute_command(['apt-get', 'install', '-y', package_name], callback=callback, shell=False)
        
        if returncode != 0:
            self.logger.error(f"Error al instalar paquete {package_name}: {output}")
            return False, f"Error al instalar paquete {package_name}"
        
        self.logger.info(f"Paquete {package_name} instalado correctamente")
        return True, f"Paquete {package_name} instalado correctamente"
    
    def remove_package(self, package_name, purge=False, callback=None):
        """
        Desinstalar un paquete
        
        Args:
            package_name: Nombre del paquete a desinstalar
            purge: Si es True, se eliminan también los archivos de configuración
            callback: Función de callback para actualizar la interfaz
            
        Returns:
            (bool, str): Tupla con éxito/fracaso y mensaje
        """
        self.logger.info(f"Desinstalando paquete: {package_name} (purge={purge})")
        
        command = ['apt-get', 'purge', '-y', package_name] if purge else ['apt-get', 'remove', '-y', package_name]
        
        if callback:
            callback(f"{'Eliminando completamente' if purge else 'Desinstalando'} paquete: {package_name}...")
        
        returncode, output = execute_command(command, callback=callback, shell=False)
        
        if returncode != 0:
            self.logger.error(f"Error al desinstalar paquete {package_name}: {output}")
            return False, f"Error al desinstalar paquete {package_name}"
        
        self.logger.info(f"Paquete {package_name} desinstalado correctamente")
        return True, f"Paquete {package_name} desinstalado correctamente"