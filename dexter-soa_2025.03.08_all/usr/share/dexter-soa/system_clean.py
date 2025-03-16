import subprocess
import shutil
from i18n import _  # Importar la función de traducción

def limpiar_sistema():
    """
    Generador que ejecuta los comandos de limpieza en tiempo real.
    """
    comandos = [
        "sudo apt-get purge -y",
        "sudo apt-get clean -y",
        "sudo apt-get autoclean -y",
        "sudo apt-get autoremove -y",
        "sudo rm -rf ~/.local/share/Trash/*",
        "sudo rm -rf /tmp/*",
        "sudo rm -rf /var/tmp/*",
        "bash -c 'history -c'"
    ]

    if shutil.which("bleachbit"):
        comandos.extend([
            "bleachbit --preset --preview",
            "bleachbit --preset --clean",
            "sudo bleachbit --preset --preview",
            "sudo bleachbit --preset --clean"
        ])
    
    total_comandos = len(comandos)
    
    for i, comando in enumerate(comandos):
        yield _("Executing: {}").format(comando) + "\n"
        
        proceso = subprocess.Popen(comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for linea in proceso.stdout:
            yield linea.strip() + "\n"
        
        proceso.wait()
        
        if proceso.returncode != 0:
            yield _("Process error: Code {}").format(proceso.returncode) + "\n"
        
        progreso = int(((i + 1) / total_comandos) * 100)
        yield _("Progress: {}%").format(progreso) + "\n"
        
