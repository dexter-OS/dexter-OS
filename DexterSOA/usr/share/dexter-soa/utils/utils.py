#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de utilidades generales para DexterSOA.
Proporciona funciones auxiliares utilizadas en diferentes partes de la aplicación.
"""

import os
import subprocess
import platform
import psutil
import logging
import json
import sys
from datetime import datetime

# Configuración global
APP_NAME = "DexterSOA"
CONFIG_DIR = os.path.expanduser("~/.config/dexter-soa")
CACHE_DIR = os.path.expanduser("~/.cache/dexter-soa")
LOG_FILE = os.path.join(CONFIG_DIR, "dexter-soa.log")

# Traducción simple
def _(text):
    """Función de internacionalización simple"""
    return text

def get_data_path():
    """
    Obtiene la ruta de los datos de la aplicación.
    En desarrollo: directorio actual
    En producción: /usr/share/dexter-soa
    
    Returns:
        str: Ruta de los datos de la aplicación
    """
    # En desarrollo usamos el directorio actual
    if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), "dexter-soa.py")):
        return os.path.dirname(os.path.dirname(__file__))
    
    # En producción usamos la ruta de instalación
    return "/usr/share/dexter-soa"

def get_icons_path(theme="light"):
    """
    Obtiene la ruta de los iconos según el tema.
    
    Args:
        theme: Nombre del tema (default: "light")
        
    Returns:
        str: Ruta de los iconos
    """
    return os.path.join(get_data_path(), "assets", "themes", "icons", theme)

def ensure_dirs_exist():
    """
    Asegura que los directorios necesarios existan
    """
    dirs = [CONFIG_DIR, CACHE_DIR]
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)

def init_config_dir():
    """
    Inicializa el directorio de configuración y crea archivos necesarios
    si no existen.
    
    Returns:
        bool: True si se ha inicializado correctamente, False en caso contrario
    """
    try:
        # Asegurar que los directorios existan
        ensure_dirs_exist()
        
        # Cargar configuración para crear el archivo si no existe
        load_config()
        
        # Verificar permisos de escritura en el directorio de configuración
        if not os.access(CONFIG_DIR, os.W_OK):
            logging.getLogger(APP_NAME).error(f"No hay permisos de escritura en {CONFIG_DIR}")
            return False
            
        return True
    except Exception as e:
        logging.getLogger(APP_NAME).error(f"Error al inicializar directorio de configuración: {e}")
        return False

def setup_logging():
    """
    Configura el sistema de logging
    
    Returns:
        logging.Logger: Logger configurado
    """
    ensure_dirs_exist()
    
    # Configurar logging
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.DEBUG)
    
    # Manejador para archivo
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    
    # Manejador para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Añadir manejadores
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_system_info():
    """
    Obtiene información básica del sistema
    
    Returns:
        dict: Información del sistema
    """
    info = {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "hostname": platform.node(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "disk_usage": {}
    }
    
    # Añadir información de discos
    for part in psutil.disk_partitions(all=False):
        if os.name == 'nt':
            if 'cdrom' in part.opts or part.fstype == '':
                continue
        usage = psutil.disk_usage(part.mountpoint)
        info["disk_usage"][part.mountpoint] = {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent
        }
    
    return info

def execute_command(command, callback=None, shell=False):
    """
    Ejecuta un comando externo y maneja la salida
    
    Args:
        command: Comando a ejecutar (lista o cadena)
        callback: Función a llamar con cada línea de salida (opcional)
        shell: Si es True, ejecuta el comando en una shell
        
    Returns:
        (int, str): Código de retorno y salida completa
    """
    if isinstance(command, str) and not shell:
        command = command.split()
    
    try:
        # Usar subprocess.run para mayor compatibilidad y seguridad
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=shell
        )
        
        output = result.stdout.strip().split('\n')
        
        # Si hay callback, llamarlo para cada línea
        if callback and output:
            for line in output:
                callback(line)
        
        return result.returncode, '\n'.join(output)
    except Exception as e:
        error_msg = f"Error al ejecutar comando: {e}"
        if callback:
            callback(error_msg)
        return 1, error_msg

def format_size(bytes, suffix="B"):
    """
    Formatea tamaños en bytes a formato legible
    
    Args:
        bytes: Tamaño en bytes
        suffix: Sufijo a usar
        
    Returns:
        str: Tamaño formateado (ej. "4.2 GB")
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f} {unit}{suffix}"
        bytes /= factor
    return f"{bytes:.2f} E{suffix}"

# Alias para mantener compatibilidad
def format_bytes(bytes, precision=2):
    """
    Alias de format_size para mantener compatibilidad con código existente
    
    Args:
        bytes: Tamaño en bytes
        precision: Número de decimales a mostrar
        
    Returns:
        str: Tamaño formateado (ej. "4.2 GB")
    """
    if bytes is None or bytes == 0:
        return "0 B"
    
    factor = 1024
    byte_value = float(bytes)
    for unit in ["", "K", "M", "G", "T", "P"]:
        if byte_value < factor:
            return f"{byte_value:.{precision}f} {unit}B"
        byte_value /= factor
    return f"{byte_value:.{precision}f} EB"

def save_config(config):
    """
    Guarda la configuración en un archivo JSON
    
    Args:
        config: Configuración a guardar
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    ensure_dirs_exist()
    config_file = os.path.join(CONFIG_DIR, "config.json")
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logging.getLogger(APP_NAME).error(f"Error al guardar configuración: {e}")
        return False

def load_config():
    """
    Carga la configuración desde un archivo JSON
    
    Returns:
        dict: Configuración cargada o configuración predeterminada
    """
    ensure_dirs_exist()
    config_file = os.path.join(CONFIG_DIR, "config.json")
    
    # Configuración predeterminada
    default_config = {
        "theme": "default",
        "auto_check_updates": True,
        "update_interval": 86400,  # 1 día en segundos
        "notifications": True,
        "auto_cleanup": False,
        "cleanup_level": "safe",
        "kernels_to_keep": 2,
        "preferred_terminal": "gnome-terminal",
        "last_update_check": None
    }
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            # Asegurar que todos los campos predeterminados existen
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            return config
        else:
            # Si no existe, guardar y devolver la configuración predeterminada
            save_config(default_config)
            return default_config
            
    except Exception as e:
        logging.getLogger(APP_NAME).error(f"Error al cargar configuración: {e}")
        return default_config

def is_root():
    """
    Verifica si el programa se está ejecutando como root
    
    Returns:
        bool: True si se está ejecutando como root, False en caso contrario
    """
    return os.geteuid() == 0 if hasattr(os, 'geteuid') else False

def get_distribution_info():
    """
    Obtiene información sobre la distribución de Linux
    
    Returns:
        dict: Información de la distribución
    """
    try:
        # Intentar leer /etc/os-release
        release_info = {}
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        release_info[key] = value.strip('"')
        
        # Intentar ejecutar lsb_release si está disponible
        lsb_info = {}
        try:
            returncode, output = execute_command(['lsb_release', '-a'])
            if returncode == 0:
                for line in output.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        lsb_info[key.strip()] = value.strip()
        except:
            pass
        
        # Combinar información
        info = {
            "name": release_info.get('NAME', lsb_info.get('Distributor ID', '')),
            "version": release_info.get('VERSION_ID', lsb_info.get('Release', '')),
            "codename": release_info.get('VERSION_CODENAME', lsb_info.get('Codename', '')),
            "description": release_info.get('PRETTY_NAME', lsb_info.get('Description', ''))
        }
        
        return info
    except Exception as e:
        logging.getLogger(APP_NAME).error(f"Error al obtener información de distribución: {e}")
        return {
            "name": "Desconocido",
            "version": "Desconocido",
            "codename": "Desconocido",
            "description": "Distribución desconocida"
        }

def backup_config(backup_path=None):
    """
    Realiza una copia de seguridad de la configuración
    
    Args:
        backup_path: Ruta donde guardar la copia de seguridad (opcional)
        
    Returns:
        (bool, str): Éxito/fracaso y ruta del archivo de copia de seguridad
    """
    ensure_dirs_exist()
    config_file = os.path.join(CONFIG_DIR, "config.json")
    
    if not os.path.exists(config_file):
        return False, "No existe archivo de configuración para hacer copia de seguridad"
    
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(CONFIG_DIR, f"config_backup_{timestamp}.json")
    
    try:
        with open(config_file, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        return True, backup_path
    except Exception as e:
        logging.getLogger(APP_NAME).error(f"Error al hacer copia de seguridad: {e}")
        return False, str(e)

def restore_config(backup_path):
    """
    Restaura la configuración desde una copia de seguridad
    
    Args:
        backup_path: Ruta del archivo de copia de seguridad
        
    Returns:
        (bool, str): Éxito/fracaso y mensaje
    """
    if not os.path.exists(backup_path):
        return False, "El archivo de copia de seguridad no existe"
    
    config_file = os.path.join(CONFIG_DIR, "config.json")
    
    try:
        # Hacer copia de seguridad de la configuración actual por si acaso
        if os.path.exists(config_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_backup = os.path.join(CONFIG_DIR, f"config_before_restore_{timestamp}.json")
            with open(config_file, 'r') as src, open(temp_backup, 'w') as dst:
                dst.write(src.read())
        
        # Restaurar desde la copia de seguridad
        with open(backup_path, 'r') as src, open(config_file, 'w') as dst:
            dst.write(src.read())
        
        return True, "Configuración restaurada correctamente"
    except Exception as e:
        logging.getLogger(APP_NAME).error(f"Error al restaurar configuración: {e}")
        return False, str(e)