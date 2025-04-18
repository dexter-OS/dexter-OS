#!/usr/bin/env python3

import os
from gi.repository import Gtk, GdkPixbuf

class DexterAbout(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)        
        self.init_ui()
        
    def init_ui(self):
        self.set_border_width(20)
        self.set_hexpand(True)
        self.set_vexpand(True)
        
        # Envolver notebook en un Frame para controlar fondo y border-radius
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.set_name("about-frame")
        frame.set_border_width(0)
        self.pack_start(frame, True, True, 0)

        notebook = Gtk.Notebook()
        notebook.set_tab_pos(Gtk.PositionType.TOP)
        notebook.set_name("about-notebook")
        frame.add(notebook)

        # Contenedor interno centrado
        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        center_box.set_halign(Gtk.Align.CENTER)
        center_box.set_valign(Gtk.Align.CENTER)
        center_box.set_hexpand(True)
        center_box.set_vexpand(True)
        center_box.set_name("center-box")

        # --- Pestaña 1: Acerca de ---
        about_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        about_box.set_border_width(15)
        about_box.set_margin_top(20)
        about_box.set_margin_bottom(20)
        about_box.set_margin_start(20)
        about_box.set_margin_end(20)
        about_box.set_name("about-box")
        # Elimina fondo explícito, se hereda del frame

        # Logo
        logo_path = "/usr/share/icons/hicolor/scalable/apps/dexter-organizer.svg"
        if os.path.exists(logo_path):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 96, 96, True)
            logo = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            logo = Gtk.Image.new_from_icon_name("document-new", Gtk.IconSize.DIALOG)
        logo.set_halign(Gtk.Align.CENTER)
        center_box.pack_start(logo, False, False, 0)

        # Título de la aplicación
        app_name = Gtk.Label(label="Dexter Organizer")
        app_name.set_name("about-title")
        app_name.set_halign(Gtk.Align.CENTER)
        center_box.pack_start(app_name, False, False, 0)

        # Versión
        version = Gtk.Label(label="Versión 1.0")
        version.set_name("about-version")
        version.set_halign(Gtk.Align.CENTER)
        center_box.pack_start(version, False, False, 0)

        # Desarrollador
        developer = Gtk.Label(label="Desarrollado por Victor Oubiña")
        developer.set_halign(Gtk.Align.CENTER)
        center_box.pack_start(developer, False, False, 0)

        # Email
        email_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        email_box.set_halign(Gtk.Align.CENTER)
        email_link = Gtk.LinkButton.new_with_label("dexteros.lxde@gmail.com")
        email_link.set_uri("mailto:dexteros.lxde@gmail.com")
        email_box.pack_start(email_link, False, False, 0)
        center_box.pack_start(email_box, False, False, 0)

        # Sitio web
        web_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        web_box.set_halign(Gtk.Align.CENTER)
        web_link = Gtk.LinkButton.new_with_label("DexterOS")
        web_link.set_uri("https://dexter-os.sourceforge.io")
        web_box.pack_start(web_link, False, False, 0)
        center_box.pack_start(web_box, False, False, 0)

        # Descripción
        description = Gtk.Label(label="Aplicación para organización de documentos")
        description.set_margin_top(5)
        description.set_halign(Gtk.Align.CENTER)
        center_box.pack_start(description, False, False, 0)

        # Agregar el contenedor centrado al contenedor principal
        about_box.pack_start(center_box, True, True, 0)

        notebook.append_page(about_box, Gtk.Label(label="Acerca de"))

        # --- Pestaña 2: Créditos y Licencia ---
        credits_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        credits_box.set_border_width(15)
        credits_box.set_margin_top(20)
        credits_box.set_margin_bottom(20)
        credits_box.set_margin_start(20)
        credits_box.set_margin_end(20)
        # Elimina fondo explícito, se hereda del frame

        # Título
        title = Gtk.Label(label="Créditos y Licencia")
        title.set_name("about-credits-title")
        title.set_justify(Gtk.Justification.CENTER)
        title.set_halign(Gtk.Align.CENTER)
        credits_box.pack_start(title, False, False, 0)

        # Separador
        separator = Gtk.HSeparator()
        separator.set_margin_top(5)
        separator.set_margin_bottom(15)
        credits_box.pack_start(separator, False, False, 0)

        # Créditos
        credits_title = Gtk.Label(label="Desarrolladores:")
        credits_title.set_halign(Gtk.Align.START)
        credits_box.pack_start(credits_title, False, False, 0)
        credits_content = Gtk.Label(label="• Victor Oubiña - Programación y Diseño\n• Colaboradores de la comunidad DexterOS")
        credits_content.set_halign(Gtk.Align.START)
        credits_box.pack_start(credits_content, False, False, 0)

        # Agradecimientos
        thanks_title = Gtk.Label(label="Agradecimientos:")
        thanks_title.set_margin_top(10)
        thanks_title.set_halign(Gtk.Align.START)
        credits_box.pack_start(thanks_title, False, False, 0)
        thanks_content = Gtk.Label(label="• GNOME Project - Por GTK y Libadwaita\n• Comunidad de DexterOS")
        thanks_content.set_halign(Gtk.Align.START)
        credits_box.pack_start(thanks_content, False, False, 0)

        # Licencia
        license_title = Gtk.Label(label="Licencia:")
        license_title.set_margin_top(10)
        license_title.set_halign(Gtk.Align.START)
        credits_box.pack_start(license_title, False, False, 0)
        # Marco y scroll para la licencia
        frame = Gtk.Frame()
        frame.set_hexpand(True)
        frame.set_vexpand(True)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(150)
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)
        license_text = (
            "Dexter Organizer\n"
            "Copyright (C) 2025 Victor Oubiña\n\n"
            "Este programa es software libre: puede redistribuirlo y/o modificarlo\n"
            "bajo los términos de la Licencia Pública General GNU publicada por\n"
            "la Free Software Foundation, ya sea la versión 3 de la Licencia, o\n"
            "(a su elección) cualquier versión posterior.\n\n"
            "Este programa se distribuye con la esperanza de que sea útil,\n"
            "pero SIN NINGUNA GARANTÍA; sin siquiera la garantía implícita de\n"
            "COMERCIABILIDAD o APTITUD PARA UN PROPÓSITO PARTICULAR. Ver el\n"
            "GNU General Public License para más detalles.\n\n"
            "Debería haber recibido una copia de la Licencia Pública General GNU\n"
            "junto con este programa. Si no, consulte <https://www.gnu.org/licenses/>."
        )
        license_view = Gtk.TextView()
        license_view.set_editable(False)
        license_view.set_cursor_visible(False)
        license_view.set_wrap_mode(Gtk.WrapMode.WORD)
        license_view.set_hexpand(True)
        buffer = license_view.get_buffer()
        buffer.set_text(license_text)
        license_view.set_top_margin(5)
        license_view.set_left_margin(5)
        license_view.set_bottom_margin(5)
        scroll.add(license_view)
        frame.add(scroll)
        credits_box.pack_start(frame, True, True, 0)

        notebook.append_page(credits_box, Gtk.Label(label="Créditos y Licencia"))

if __name__ == "__main__":
    win = Gtk.Window(title="DexterAbout")
    win.set_default_size(800, 600)
    win.connect("destroy", Gtk.main_quit)
    
    # Crear y añadir el widget de inicio
    start = DexterAbout()
    win.add(start)
    
    # Mostrar todo y ejecutar
    win.show_all()
    Gtk.main()
