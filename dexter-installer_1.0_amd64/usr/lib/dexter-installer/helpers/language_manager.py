#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# DexterOS Installer - Módulo para gestión de idiomas
# Version: 1.0
# Author: Victor Oubiña <oubinav78@gmail.com>
#

import os
import json
import locale
import subprocess

class LanguageManager:
    """Clase para gestionar idiomas y localizaciones"""
    
    def __init__(self, languages_file="/usr/share/dexter-installer/locales/languages.json"):
        """Inicializa el gestor de idiomas cargando el archivo de definiciones"""
        self.languages_file = languages_file
        self.languages = []
        self.load_languages()
        self.detect_system_language()
    
    def load_languages(self):
        """Carga la lista de idiomas desde el archivo JSON"""
        try:
            if os.path.exists(self.languages_file):
                with open(self.languages_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.languages = data.get("languages", [])
                    print(f"Cargados {len(self.languages)} idiomas desde {self.languages_file}")
            else:
                print(f"Archivo de idiomas no encontrado: {self.languages_file}")
                # Cargar algunos idiomas básicos por defecto
                self.languages = [
                    {
                        "code": "es",
                        "name": "Español",
                        "variants": [
                            {"code": "es_ES", "name": "España", "timezone": "Europe/Madrid"}
                        ]
                    },
                    {
                        "code": "en",
                        "name": "English",
                        "variants": [
                            {"code": "en_US", "name": "United States", "timezone": "America/New_York"}
                        ]
                    }
                ]
        except Exception as e:
            print(f"Error al cargar idiomas: {e}")
            # Configurar valores predeterminados mínimos en caso de error
            self.languages = [
                {
                    "code": "es",
                    "name": "Español",
                    "variants": [
                        {"code": "es_ES", "name": "España", "timezone": "Europe/Madrid"}
                    ]
                },
                {
                    "code": "en",
                    "name": "English",
                    "variants": [
                        {"code": "en_US", "name": "United States", "timezone": "America/New_York"}
                    ]
                }
            ]
    
    def detect_system_language(self):
        """Detecta el idioma y localización del sistema"""
        try:
            # Intentar obtener la configuración regional del sistema
            self.system_locale = locale.getlocale()[0] or locale.getdefaultlocale()[0] or 'en_US.UTF-8'
            # Eliminar la parte de codificación si está presente
            if '.' in self.system_locale:
                self.system_locale = self.system_locale.split('.')[0]
            
            print(f"Detectado locale del sistema: {self.system_locale}")
            
            # Buscar si tenemos este locale en nuestras definiciones
            self.detected_language = None
            self.detected_variant = None
            
            # Buscar coincidencia exacta de locale
            for lang in self.languages:
                for variant in lang.get("variants", []):
                    if variant["code"] == self.system_locale:
                        self.detected_language = lang
                        self.detected_variant = variant
                        return
            
            # Si no encontramos coincidencia exacta, buscar por idioma principal
            if not self.detected_language:
                lang_code = self.system_locale.split('_')[0]
                for lang in self.languages:
                    if lang["code"] == lang_code:
                        self.detected_language = lang
                        # Tomar la primera variante como predeterminada
                        if lang.get("variants"):
                            self.detected_variant = lang["variants"][0]
                        return
            
            # Si aún no tenemos nada, usar inglés por defecto
            if not self.detected_language:
                for lang in self.languages:
                    if lang["code"] == "en":
                        self.detected_language = lang
                        # Tomar inglés de EE.UU. como predeterminado si existe
                        for variant in lang.get("variants", []):
                            if variant["code"] == "en_US":
                                self.detected_variant = variant
                                return
                        # Si no hay en_US, tomar la primera variante
                        if lang.get("variants"):
                            self.detected_variant = lang["variants"][0]
                        return
        
        except Exception as e:
            print(f"Error al detectar el idioma del sistema: {e}")
            # Establecer inglés como fallback
            for lang in self.languages:
                if lang["code"] == "en":
                    self.detected_language = lang
                    if lang.get("variants"):
                        self.detected_variant = lang["variants"][0]
                    return
    
    def get_all_languages(self):
        """Retorna la lista completa de idiomas"""
        return self.languages
    
    def get_language_variants(self, language_code):
        """Retorna todas las variantes de un idioma por su código"""
        for lang in self.languages:
            if lang["code"] == language_code:
                return lang.get("variants", [])
        return []
    
    def get_detected_language(self):
        """Retorna el idioma detectado del sistema"""
        return self.detected_language
    
    def get_detected_variant(self):
        """Retorna la variante detectada del sistema"""
        return self.detected_variant
    
    def get_language_by_code(self, code):
        """Busca un idioma por su código"""
        for lang in self.languages:
            if lang["code"] == code:
                return lang
        return None
    
    def get_variant_by_code(self, language_code, variant_code):
        """Busca una variante específica por su código"""
        for lang in self.languages:
            if lang["code"] == language_code:
                for variant in lang.get("variants", []):
                    if variant["code"] == variant_code:
                        return variant
        return None

# Ejemplo de uso:
if __name__ == "__main__":
    lang_manager = LanguageManager()
    
    # Obtener el idioma detectado
    detected = lang_manager.get_detected_language()
    if detected:
        print(f"Idioma detectado: {detected['name']} ({detected['code']})")
        
    # Obtener la variante detectada
    variant = lang_manager.get_detected_variant()
    if variant:
        print(f"Variante detectada: {variant['name']} ({variant['code']}) - Zona horaria: {variant['timezone']}")
    
    # Mostrar todas las variantes del idioma detectado
    if detected:
        print(f"\nVariantes disponibles para {detected['name']}:")
        for v in detected.get("variants", []):
            print(f"  - {v['name']} ({v['code']})")
