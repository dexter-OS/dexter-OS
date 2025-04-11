#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk

class AboutManager:
    def __init__(self, parent_window):
        self.parent = parent_window
        
        # Contenedor principal
        self.container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.container.set_margin_top(30)
        self.container.set_margin_bottom(30)
        self.container.set_margin_start(30)
        self.container.set_margin_end(30)
        
        # Logo o icono
        icon = Gtk.Image.new_from_icon_name("document-open")
        icon.set_pixel_size(128)
        self.container.append(icon)
        
        # Título
        title = Gtk.Label(label="<span size='xx-large'><b>DexterOrganizer</b></span>")
        title.set_use_markup(True)
        title.set_margin_top(10)
        self.container.append(title)
        
        # Versión
        version = Gtk.Label(label="<span size='large'>Versión 1.0</span>")
        version.set_use_markup(True)
        version.set_margin_bottom(20)
        self.container.append(version)
        
        # Descripción
        description = Gtk.Label(label="Una aplicación para organizar y gestionar documentos de manera eficiente.")
        description.set_wrap(True)
        description.set_max_width_chars(60)
        description.set_margin_bottom(20)
        self.container.append(description)
        
        # Información del desarrollador
        developer_frame = Gtk.Frame()
        developer_frame.set_label("Desarrollador")
        
        developer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        developer_box.set_margin_top(10)
        developer_box.set_margin_bottom(10)
        developer_box.set_margin_start(10)
        developer_box.set_margin_end(10)
        
        developer_name = Gtk.Label(label="Victor Oubiña Faubel")
        developer_name.set_halign(Gtk.Align.START)
        
        developer_email = Gtk.Label(label="Email: dexteros.lxde@gmail.com")
        developer_email.set_halign(Gtk.Align.START)
        
        developer_website = Gtk.Label(label="Web: https://sourceforge.net/projects/dexter-gnome/")
        developer_website.set_halign(Gtk.Align.START)
        
        developer_box.append(developer_name)
        developer_box.append(developer_email)
        developer_box.append(developer_website)
        
        developer_frame.set_child(developer_box)
        self.container.append(developer_frame)
        
        # Botón para abrir el sitio web
        website_button = Gtk.Button(label="Visitar Sitio Web")
        website_button.connect("clicked", self.on_website_clicked)
        website_button.set_halign(Gtk.Align.CENTER)
        website_button.set_margin_top(20)
        self.container.append(website_button)
        
    def get_container(self):
        return self.container
        
    def on_website_clicked(self, button):
        Gtk.show_uri(self.parent, "https://sourceforge.net/projects/dexter-gnome/", Gdk.CURRENT_TIME)
