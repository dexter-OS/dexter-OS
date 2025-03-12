#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# DexterOS Installer - Configuración global
# Version: 1.0
# Author: Victor Oubiña <oubinav78@gmail.com>
#

import os
import json
import tempfile

class Config:
    """Gestiona la configuración global del instalador"""
    
    def __init__(self):
        """Inicializa la configuración con valores predeterminados"""
        # Crear un archivo temporal para almacenar la configuración
        fd, self.config_file = tempfile.mkstemp(prefix='dexter-installer-')
        os.close(fd)
        
        # Valores predeterminados
        self.data = {
            # Configuración de idioma
            "language": {
                "locale": "es_ES.UTF-8",
                "language": "es",
                "country": "ES"
            },
            
            # Configuración de zona horaria
            "timezone": {
                "region": "Europe",
                "zone": "Madrid"
            },
            
            # Configuración de teclado
            "keyboard": {
                "layout": "es",
                "variant": ""
            },
            
            # Configuración de particiones
            "partition": {
                "mode": "auto",  # auto, alongside, manual
                "disk": "",
                "efi": False,
                "swap": True,
                "swap_size": 5120,  # MB
                "encrypt": False,
                "passphrase": "",
                "partitions": []
            },
            
            # Configuración de usuario
            "user": {
                "fullname": "",
                "username": "",
                "hostname": "dexteros",
                "password": "",
                "root_password": "",
                "autologin": False,
                "same_password": True
            },
            
            # Otras configuraciones
            "system": {
                "grub_device": "",
                "remove_installer": True,
                "update_system": True
            }
        }
        
        # Guardar la configuración inicial
        self.save()
    
    def save(self):
        """Guarda la configuración en el archivo temporal"""
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=4)
    
    def load(self):
        """Carga la configuración desde el archivo temporal"""
        try:
            with open(self.config_file, 'r') as f:
                self.data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Si hay error, mantener los valores predeterminados
            pass
    
    def get(self, section, key=None):
        """Obtiene un valor de configuración"""
        if key is None:
            return self.data.get(section, {})
        return self.data.get(section, {}).get(key)
    
    def set(self, section, key, value):
        """Establece un valor de configuración"""
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value
        self.save()
    
    def update_section(self, section, data):
        """Actualiza una sección completa de la configuración"""
        self.data[section] = data
        self.save()
    
    def get_all(self):
        """Retorna toda la configuración"""
        return self.data
    
    def cleanup(self):
        """Limpia los archivos temporales"""
        try:
            os.remove(self.config_file)
        except:
            pass
