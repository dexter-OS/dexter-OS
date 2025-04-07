# dexter_config.py

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

class ConfigView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20, margin_top=40)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_margin_start(20)
        self.set_margin_end(20)

        self.backup_button = Gtk.Button(label="Realizar Backup")
        self.backup_button.connect("clicked", self.on_backup_clicked)

        self.restore_button = Gtk.Button(label="Restaurar Backup")
        self.restore_button.connect("clicked", self.on_restore_clicked)

        self.append(self.backup_button)
        self.append(self.restore_button)

    def on_backup_clicked(self, button):
        print(">> Realizando backup... (aquí va la lógica de backup)")

    def on_restore_clicked(self, button):
        print(">> Restaurando backup... (aquí va la lógica de restauración)")

