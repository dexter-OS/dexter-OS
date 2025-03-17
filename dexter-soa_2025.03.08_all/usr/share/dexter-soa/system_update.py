import subprocess
import time
from i18n import _  # Importar la función de traducción

def actualizar_sistema():
    """
    Generador que ejecuta los comandos de actualización en tiempo real.
    """
    comandos = [
        "sudo apt-get update",
        "sudo apt-get install -f -y",
        "sudo apt-get install --fix-broken -y",
        "sudo dpkg --configure -a",
        "sudo apt-get full-upgrade -y",
        "sudo apt-get remove -y",
        "sudo apt-get autoremove -y",
        "sudo apt-get purge -y",
        "sudo apt-get autopurge -y",
        "sudo apt-get clean",
        "sudo apt-get autoclean",
        "sudo update-grub2"
    ]

    total_comandos = len(comandos)
    
    for i, comando in enumerate(comandos):
        yield _("Executing: {}").format(comando) + "\n"
        
        proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for linea in proceso.stdout:
            yield linea  # Muestra la salida en tiempo real
            
        proceso.wait()
        
        if proceso.returncode != 0:
            yield _("Process error: Code {}").format(proceso.returncode) + "\n"
        
        progreso = int(((i + 1) / total_comandos) * 100)
        yield _("Progress: {}%").format(progreso) + "\n"
        
