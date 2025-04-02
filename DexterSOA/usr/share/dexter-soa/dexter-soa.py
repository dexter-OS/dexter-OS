#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DexterSOA - Una aplicación gráfica para gestión de actualizaciones,
administración de paquetes APT, limpieza del sistema y notificaciones programadas.
"""

import os
import sys
import gi
import locale
import gettext
import subprocess

# Verificar que estamos en Linux
if sys.platform != 'linux':
    print("Este programa solo funciona en sistemas Linux.")
    sys.exit(1)

# Inicializar sistema de internacionalización
try:
    # Uso de las funciones recomendadas en lugar de locale.getdefaultlocale()
    locale.setlocale(locale.LC_ALL, '')
    encoding = locale.getencoding()
    locale_code = locale.getlocale()[0]
    
    if locale_code is None:
        locale_code = 'es_ES'
    
    language = gettext.translation('dexter-soa', 
                                  localedir=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locale'),
                                  languages=[locale_code], 
                                  fallback=True)
    _ = language.gettext
except Exception as e:
    print(f"Advertencia al configurar internacionalización: {e}")
    _ = gettext.gettext

# Importar GTK después de configurar i18n
try:
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print(f"Error al cargar GTK: {e}")
    print("Asegúrese de tener instalado el paquete python3-gi (PyGObject).")
    sys.exit(1)

# Importaciones propias
try:
    from utils.utils import init_config_dir
    from ui.main_window import MainWindow
except Exception as e:
    print(f"Error al cargar módulos de la aplicación: {e}")
    sys.exit(1)

class DexterSOA:
    """Clase principal de la aplicación DexterSOA"""
    
    def __init__(self):
        """Inicializar la aplicación"""
        # Verificar si estamos ejecutando con privilegios
        self._check_privileges()
        
        # Inicializar directorio de configuración
        init_config_dir()
        
        # Crear ventana principal
        self.window = MainWindow()
        self.window.set_title("DexterSOA")  # Establecer título explícitamente
        self.window.connect("destroy", Gtk.main_quit)
        self.window.show_all()
    
    def _check_privileges(self):
        """Verificar si el programa se está ejecutando con privilegios elevados"""
        try:
            # Verificar si podemos escribir en /etc
            if not os.access('/etc', os.W_OK):
                print(_("Este programa necesita privilegios de administrador."))
                print(_("Se recomienda ejecutarlo con pkexec o sudo."))
                
                # Si estamos en un entorno gráfico, intentar reiniciar con pkexec
                if 'DISPLAY' in os.environ:
                    self._restart_with_pkexec()
                
                sys.exit(1)
        except Exception as e:
            print(f"Error al verificar privilegios: {e}")
    
    def _restart_with_pkexec(self):
        """Reiniciar la aplicación con privilegios elevados usando pkexec"""
        try:
            # Verificar si pkexec está disponible
            pkexec_path = subprocess.check_output(['which', 'pkexec']).decode().strip()
            
            if pkexec_path:
                print(_("Reiniciando con pkexec..."))
                
                # Construir el comando para reiniciar con pkexec
                cmd = [pkexec_path, sys.executable, os.path.abspath(__file__)]
                
                # Ejecutar el comando
                subprocess.Popen(cmd)
                
                # Salir de esta instancia sin privilegios
                sys.exit(0)
        except Exception as e:
            print(f"Error al reiniciar con pkexec: {e}")
    
    def run(self):
        """Ejecutar la aplicación"""
        Gtk.main()

def main():
    """Función principal de la aplicación"""
    app = DexterSOA()
    app.run()

if __name__ == "__main__":
    main()