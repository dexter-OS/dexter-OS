#!/usr/bin/env python3
import os
import gettext
import locale

def setup_translations():
    # Ruta estándar a los archivos de traducción
    locale_dir = '/usr/share/locale'
    
    # Obtener idioma del sistema
    try:
        current_locale, encoding = locale.getdefaultlocale()
        if current_locale is None:
            current_locale = 'en_US'
        
        # Obtener código de idioma (ej: 'es' de 'es_ES')
        language = current_locale.split('_')[0]
        
        # Configurar gettext
        translation = gettext.translation('dexter-soa', locale_dir, 
                                          languages=[language, current_locale], 
                                          fallback=True)
        translation.install()
        return translation.gettext
    except Exception as e:
        print(f"Error al configurar traducciones: {e}")
        return lambda x: x

# Función global de traducción
_ = setup_translations()
