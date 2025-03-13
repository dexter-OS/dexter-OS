#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# DexterOS Installer - Página de bienvenida
# Version: 1.0
# Author: Victor Oubiña <oubinav78@gmail.com>
#

import os
import gi
import gettext

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

# Configurar traducción
_ = gettext.gettext

class WelcomePage:
    """Página de bienvenida del instalador"""
    
    def __init__(self, app):
        """Inicializa la página de bienvenida"""
        self.app = app
        
        # Cargar el CSS externo
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('/usr/share/dexter-installer/styles/style.css')  # Ajusta la ruta según corresponda
        
        # Aplicar el proveedor CSS al contexto de estilo
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        
        # Crear el contenedor principal
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.content.set_margin_bottom(15)
        
        # Guardar los márgenes originales
        original_margin_start = self.content.get_margin_start()
        original_margin_end = self.content.get_margin_end()
        
        # Temporalmente quitar los márgenes laterales
        self.content.set_margin_start(0)
        self.content.set_margin_end(0)
        
        # Título de la página con esquinas redondeadas
        title_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_container.get_style_context().add_class("title-header")  # Aplicar la clase CSS
        title_container.set_hexpand(True)
        
        # Título de la página
        title = Gtk.Label()
        title.set_markup("<span foreground='white' size='22000' weight='bold'>{}</span>".format(
            _("Bienvenido al instalador de DexterOS")))
        title.set_halign(Gtk.Align.CENTER)
        title.set_hexpand(True)
        title.set_margin_top(10)
        title.set_margin_bottom(10)
        
        title_container.add(title)
        self.content.pack_start(title_container, False, True, 0)
        
        # Restaurar los márgenes para el resto del contenido
        self.content.set_margin_start(original_margin_start)
        self.content.set_margin_end(original_margin_end)
        
        # Subtítulo
        subtitle = Gtk.Label()
        subtitle.set_markup("<span size='12000' >{}</span>".format(
            _("Este asistente le guiará en la instalación del sistema operativo DexterOS en su equipo.")))
        subtitle.set_halign(Gtk.Align.CENTER)
        subtitle.set_line_wrap(True)
        subtitle.set_margin_bottom(20)
        self.content.pack_start(subtitle, False, False, 0)
        
        # Imagen de bienvenida
        try:
            image_path = os.path.join('/usr/share/dexter-installer/images', 'welcome.png')
            if os.path.exists(image_path):
                # Reducimos el tamaño del logo a 300x187 para adaptarlo a la ventana más pequeña
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image_path, 300, 187, True)
                image = Gtk.Image.new_from_pixbuf(pixbuf)
            else:
                # Crear una imagen de placeholder si no existe el archivo
                image = Gtk.Image.new_from_icon_name("computer", Gtk.IconSize.DIALOG)
                image.set_pixel_size(96)  # Tamaño reducido
            
            image.set_halign(Gtk.Align.CENTER)
            self.content.pack_start(image, False, False, 0)
        except Exception as e:
            print(_("No se pudo cargar la imagen de bienvenida: {}").format(str(e)))
        
        # Información adicional
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        info_box.set_margin_top(120)
        info_box.set_margin_start(30)  # Añadir margen adicional izquierdo
        self.content.pack_start(info_box, True, True, 0)
        
        # Información de instalación
        info_label = Gtk.Label()
        info_label.set_markup("<span foreground='white' size='12000'>{}</span>".format(
            _("Durante el proceso de instalación, se le solicitará información para configurar su sistema:")))
        info_label.set_halign(Gtk.Align.CENTER)
        info_label.set_line_wrap(True)
        info_box.pack_start(info_label, False, False, 0)
        
        # Lista de aspectos a configurar - MODIFICADO PARA MOSTRAR DOS COLUMNAS
        points = [
            _("Idioma y ubicación regional y Zona horaria"), _("Disposición del teclado"),
            _("Configuración de las particiones del disco"), _("Creación de una cuenta de usuario"),
            _("Resumen de los cambios"), _("Final y Agradecimiento")
        ]
        
        # Crear un contenedor para las dos columnas
        columns_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=100)
        columns_box.set_halign(Gtk.Align.CENTER)
        columns_box.set_margin_start(10)
        info_box.pack_start(columns_box, False, False, 5)
        
        # Columna izquierda
        left_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        columns_box.pack_start(left_column, True, True, 0)
        
        # Columna derecha
        right_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        columns_box.pack_start(right_column, True, True, 0)
        
        # Distribuir los puntos en las dos columnas
        half = len(points) // 2
        
        # Añadir puntos a la columna izquierda
        for i in range(half):
            point_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            
            bullet = Gtk.Label()
            bullet.set_markup("<span size='large'>•</span>")
            point_box.pack_start(bullet, False, False, 0)
            
            label = Gtk.Label(label=points[i])
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            point_box.pack_start(label, True, True, 0)
            
            left_column.pack_start(point_box, False, False, 5)
        
        # Añadir puntos a la columna derecha
        for i in range(half, len(points)):
            point_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            
            bullet = Gtk.Label()
            bullet.set_markup("<span size='large'>•</span>")
            point_box.pack_start(bullet, False, False, 0)
            
            label = Gtk.Label(label=points[i])
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            point_box.pack_start(label, True, True, 0)
            
            right_column.pack_start(point_box, False, False, 5)
        
        # Nota de recomendación
        note_label = Gtk.Label()
        note_label.set_markup("<span foreground='red' size='12000' style='italic'>{}</span>".format(
            _("Se recomienda que el equipo esté conectado a la red eléctrica durante la instalación.")))
        note_label.set_halign(Gtk.Align.CENTER)
        note_label.set_margin_bottom(20)
        note_label.set_line_wrap(True)
        info_box.pack_start(note_label, False, False, 0)
    
    def get_content(self):
        """Retorna el contenido de la página"""
        return self.content
    
    def validate(self):
        """Valida la página antes de avanzar"""
        # La página de bienvenida no necesita validación
        return True
    
    def save(self):
        """Guarda los datos de la página"""
        # La página de bienvenida no tiene datos que guardar
        pass
    
    def on_enter(self):
        """Se llama cuando se entra a la página"""
        # Actualizar la interfaz si es necesario
        pass
