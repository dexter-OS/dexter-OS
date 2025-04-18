#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

class DexterStart(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)        
        self.init_ui()
        
    def init_ui(self):
        self.set_border_width(20)
        self.set_hexpand(True)
        self.set_vexpand(True)

        # Contenedor interno centrado
        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        center_box.set_halign(Gtk.Align.CENTER)
        center_box.set_valign(Gtk.Align.CENTER)
        center_box.set_hexpand(True)
        center_box.set_vexpand(True)

        # Título principal
        title_label = Gtk.Label(label="Gestión Avanzada de Documentos")
        title_label.set_justify(Gtk.Justification.CENTER)
        title_label.set_halign(Gtk.Align.CENTER)
        context = title_label.get_style_context()
        context.add_class("start-title")
        center_box.pack_start(title_label, False, False, 0)

        # Descripción general
        description_label = Gtk.Label(label="Su solución integral para crear, organizar y proteger todos sus documentos:")
        description_label.set_justify(Gtk.Justification.CENTER)
        description_label.set_halign(Gtk.Align.CENTER)
        context = description_label.get_style_context()
        context.add_class("start-description")
        center_box.pack_start(description_label, False, False, 0)

        # Características principales - Usamos un contenedor para aplicar estilos
        features_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        features_box.set_halign(Gtk.Align.START)
        features_box.set_valign(Gtk.Align.CENTER)
        context = features_box.get_style_context()
        context.add_class("start-features")

        features_items = [
            "Soporte para múltiples formatos: TXT, HTML, Python, Shell, Markdown, Word, Excel",
            "Vista dual para documentos HTML: modo código y navegación web",
            "Sistema completo de copias de seguridad automáticas y bajo demanda",
            "Organización por categorías personalizables para acceso rápido",
            "Personalización de fuentes, tamaños y estilos para edición cómoda",
            "Regresa a esta pantalla, desde cualquier lugar, pulsando el logo Dexter-Organizer"
        ]

        for item in features_items:
            item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            item_box.set_halign(Gtk.Align.START)
            bullet = Gtk.Label(label="•")
            bullet.set_margin_start(5)
            item_box.pack_start(bullet, False, False, 0)
            item_label = Gtk.Label(label=item)
            item_label.set_halign(Gtk.Align.START)
            item_label.set_line_wrap(True)
            item_box.pack_start(item_label, True, True, 0)
            features_box.pack_start(item_box, False, False, 5)

        center_box.pack_start(features_box, False, False, 0)

        # Agregar el contenedor centrado al widget principal
        self.pack_start(center_box, True, True, 0)

    
    def load_module(self, parent_container):
        """Método para cargar este módulo en el contenedor principal"""
        # Limpiar el contenedor padre primero
        for child in parent_container.get_children():
            parent_container.remove(child)
        
        # Añadir este módulo al contenedor
        parent_container.add(self)
        parent_container.show_all()

if __name__ == "__main__":
    win = Gtk.Window(title="DexterStart")
    win.set_default_size(800, 600)
    win.connect("destroy", Gtk.main_quit)
    
    # Crear y añadir el widget de inicio
    start = DexterStart()
    win.add(start)
    
    # Mostrar todo y ejecutar
    win.show_all()
    Gtk.main()
