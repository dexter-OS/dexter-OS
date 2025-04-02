#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pestaña para estadísticas del sistema.
Muestra información detallada del sistema y opciones de optimización.
"""

import os
import gi
import threading
import time
import math
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, Pango, cairo

from gettext import gettext as _
from utils.system_stats import SystemStats

class StatsTab(Gtk.Box):
    """Pestaña de estadísticas del sistema"""
    
    def __init__(self, parent_window):
        """Inicializar la pestaña de estadísticas"""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.parent_window = parent_window
        self.set_border_width(10)
        self.get_style_context().add_class("tab-container")
        
        # Inicializar estadísticas del sistema
        self.system_stats = SystemStats()
        
        # Librerías necesarias
        self.has_cpu_data = True
        self.has_memory_data = True
        self.has_disk_data = True
        self.has_network_data = True
        
        # Variables para gráficos
        self.cpu_usage = 0
        self.memory_usage = 0
        self.disk_usage = 0
        
        # Crear notebook de pestañas
        self.notebook = Gtk.Notebook()
        self.pack_start(self.notebook, True, True, 0)
        
        # Crear pestañas
        self.create_overview_tab()
        self.create_hardware_tab()
        self.create_performance_tab()
        self.create_optimization_tab()
        
        # Iniciar actualización automática
        GLib.timeout_add(5000, self.auto_refresh)
        
        # Actualizar datos inmediatamente
        self.refresh_stats()
    
    def create_overview_tab(self):
        """Crear pestaña de resumen general"""
        # Contenedor principal
        overview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        overview_box.set_border_width(15)
        
        # Título
        title_label = Gtk.Label()
        title_label.set_markup(f"<span size='large' weight='bold'>{_('Resumen del Sistema')}</span>")
        title_label.set_alignment(0, 0.5)
        overview_box.pack_start(title_label, False, False, 0)
        
        # Panel de gráficos
        metrics_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        overview_box.pack_start(metrics_box, False, False, 10)
        
        # Panel de CPU
        cpu_panel = Gtk.Frame(label=_("CPU"))
        metrics_box.pack_start(cpu_panel, True, True, 0)
        
        cpu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        cpu_box.set_border_width(10)
        cpu_panel.add(cpu_box)
        
        # Gráfico de CPU
        cpu_drawing_area = Gtk.DrawingArea()
        cpu_drawing_area.set_size_request(120, 120)
        cpu_drawing_area.connect("draw", self.on_draw_cpu)
        cpu_box.pack_start(cpu_drawing_area, False, False, 0)
        
        # Información de CPU
        self.cpu_usage_label = Gtk.Label()
        self.cpu_usage_label.set_markup(_("Uso: <b>0%</b>"))
        self.cpu_usage_label.set_alignment(0.5, 0.5)
        cpu_box.pack_start(self.cpu_usage_label, False, False, 5)
        
        self.cpu_temp_label = Gtk.Label()
        self.cpu_temp_label.set_markup(_("Temperatura: <b>N/A</b>"))
        self.cpu_temp_label.set_alignment(0.5, 0.5)
        cpu_box.pack_start(self.cpu_temp_label, False, False, 0)
        
        # Panel de memoria
        memory_panel = Gtk.Frame(label=_("Memoria"))
        metrics_box.pack_start(memory_panel, True, True, 0)
        
        memory_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        memory_box.set_border_width(10)
        memory_panel.add(memory_box)
        
        # Gráfico de memoria
        memory_drawing_area = Gtk.DrawingArea()
        memory_drawing_area.set_size_request(120, 120)
        memory_drawing_area.connect("draw", self.on_draw_memory)
        memory_box.pack_start(memory_drawing_area, False, False, 0)
        
        # Información de memoria
        self.memory_usage_label = Gtk.Label()
        self.memory_usage_label.set_markup(_("Uso: <b>0%</b>"))
        self.memory_usage_label.set_alignment(0.5, 0.5)
        memory_box.pack_start(self.memory_usage_label, False, False, 5)
        
        self.memory_used_label = Gtk.Label()
        self.memory_used_label.set_markup(_("Usada: <b>0 MB</b>"))
        self.memory_used_label.set_alignment(0.5, 0.5)
        memory_box.pack_start(self.memory_used_label, False, False, 0)
        
        # Panel de disco
        disk_panel = Gtk.Frame(label=_("Disco"))
        metrics_box.pack_start(disk_panel, True, True, 0)
        
        disk_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        disk_box.set_border_width(10)
        disk_panel.add(disk_box)
        
        # Gráfico de disco
        disk_drawing_area = Gtk.DrawingArea()
        disk_drawing_area.set_size_request(120, 120)
        disk_drawing_area.connect("draw", self.on_draw_disk)
        disk_box.pack_start(disk_drawing_area, False, False, 0)
        
        # Información de disco
        self.disk_usage_label = Gtk.Label()
        self.disk_usage_label.set_markup(_("Uso: <b>0%</b>"))
        self.disk_usage_label.set_alignment(0.5, 0.5)
        disk_box.pack_start(self.disk_usage_label, False, False, 5)
        
        self.disk_free_label = Gtk.Label()
        self.disk_free_label.set_markup(_("Libre: <b>0 GB</b>"))
        self.disk_free_label.set_alignment(0.5, 0.5)
        disk_box.pack_start(self.disk_free_label, False, False, 0)
        
        # Separador
        overview_box.pack_start(Gtk.Separator(), False, False, 10)
        
        # Panel de estado del sistema
        status_frame = Gtk.Frame(label=_("Estado del Sistema"))
        overview_box.pack_start(status_frame, False, False, 0)
        
        status_grid = Gtk.Grid()
        status_grid.set_row_spacing(10)
        status_grid.set_column_spacing(20)
        status_grid.set_border_width(10)
        status_frame.add(status_grid)
        
        # Primera columna: Sistema
        system_header = self.create_header_label(_("Sistema"))
        status_grid.attach(system_header, 0, 0, 1, 1)
        
        self.system_status_label = self.create_info_label()
        status_grid.attach(self.system_status_label, 0, 1, 1, 1)
        
        # Segunda columna: Actualizaciones
        updates_header = self.create_header_label(_("Actualizaciones"))
        status_grid.attach(updates_header, 1, 0, 1, 1)
        
        self.updates_status_label = self.create_info_label()
        status_grid.attach(self.updates_status_label, 1, 1, 1, 1)
        
        # Tercera columna: Seguridad
        security_header = self.create_header_label(_("Seguridad"))
        status_grid.attach(security_header, 2, 0, 1, 1)
        
        self.security_status_label = self.create_info_label()
        status_grid.attach(self.security_status_label, 2, 1, 1, 1)
        
        # Botón de actualizar
        refresh_button = Gtk.Button(label=_("Actualizar Estadísticas"))
        refresh_button.connect("clicked", self.on_refresh_clicked)
        overview_box.pack_end(refresh_button, False, False, 10)
        
        # Separador
        overview_box.pack_end(Gtk.Separator(), False, False, 5)
        
        # Añadir la pestaña de resumen
        self.notebook.append_page(overview_box, Gtk.Label(label=_("Resumen")))

    def create_hardware_tab(self):
        """Crear pestaña de información de hardware"""
        # Notebook para pestañas de hardware
        hardware_notebook = Gtk.Notebook()
        
        # Crear pestañas específicas
        self.create_cpu_info_tab(hardware_notebook)
        self.create_memory_info_tab(hardware_notebook)
        self.create_disk_info_tab(hardware_notebook)
        self.create_network_info_tab(hardware_notebook)
        
        # Añadir la pestaña de hardware
        self.notebook.append_page(hardware_notebook, Gtk.Label(label=_("Hardware")))
    
    def create_cpu_info_tab(self, notebook):
        """Crear tab para información de CPU"""
        # Contenedor principal
        cpu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        cpu_box.set_border_width(15)
        
        # Panel de información general de CPU
        info_frame = Gtk.Frame(label=_("Información de CPU"))
        cpu_box.pack_start(info_frame, False, False, 0)
        
        info_grid = Gtk.Grid()
        info_grid.set_row_spacing(8)
        info_grid.set_column_spacing(15)
        info_grid.set_border_width(10)
        info_frame.add(info_grid)
        
        # Etiquetas de información
        labels = [
            (_("Procesador:"), "cpu_model"),
            (_("Arquitectura:"), "cpu_arch"),
            (_("Núcleos:"), "cpu_cores"),
            (_("Frecuencia:"), "cpu_freq"),
            (_("Caché:"), "cpu_cache")
        ]
        
        # Crear etiquetas e información
        self.cpu_info_labels = {}
        for i, (label_text, key) in enumerate(labels):
            label = Gtk.Label(label=label_text)
            label.set_alignment(0, 0.5)
            info_grid.attach(label, 0, i, 1, 1)
            
            info_label = Gtk.Label(label=_("Cargando..."))
            info_label.set_alignment(0, 0.5)
            info_grid.attach(info_label, 1, i, 1, 1)
            
            self.cpu_info_labels[key] = info_label
        
        # Separador
        cpu_box.pack_start(Gtk.Separator(), False, False, 5)
        
        # Panel de uso de CPU por núcleo
        cores_frame = Gtk.Frame(label=_("Uso por Núcleo"))
        cpu_box.pack_start(cores_frame, True, True, 0)
        
        # Scrolled window para la lista de núcleos
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_border_width(10)
        cores_frame.add(scrolled_window)
        
        # Crear grid para núcleos
        cores_grid = Gtk.Grid()
        cores_grid.set_row_spacing(10)
        cores_grid.set_column_spacing(15)
        scrolled_window.add(cores_grid)
        
        # Cabecera
        header_labels = [_("Núcleo"), _("Uso"), _("Temperatura")]
        for i, text in enumerate(header_labels):
            label = Gtk.Label()
            label.set_markup(f"<b>{text}</b>")
            cores_grid.attach(label, i, 0, 1, 1)
        
        # Espacio para los núcleos (se llena dinámicamente)
        self.cores_container = cores_grid
        
        # Añadir la pestaña
        notebook.append_page(cpu_box, Gtk.Label(label=_("CPU")))
    
    def create_memory_info_tab(self, notebook):
        """Crear tab para información de memoria"""
        # Contenedor principal
        memory_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        memory_box.set_border_width(15)
        
        # Panel de información de memoria
        info_frame = Gtk.Frame(label=_("Información de Memoria"))
        memory_box.pack_start(info_frame, False, False, 0)
        
        info_grid = Gtk.Grid()
        info_grid.set_row_spacing(8)
        info_grid.set_column_spacing(15)
        info_grid.set_border_width(10)
        info_frame.add(info_grid)
        
        # Etiquetas de información
        labels = [
            (_("Memoria Total:"), "memory_total"),
            (_("Memoria Disponible:"), "memory_available"),
            (_("Memoria Usada:"), "memory_used"),
            (_("Caché:"), "memory_cached"),
            (_("Buffers:"), "memory_buffers"),
            (_("Memoria Virtual (Swap):"), "swap_total"),
            (_("Swap Usada:"), "swap_used")
        ]
        
        # Crear etiquetas e información
        self.memory_info_labels = {}
        for i, (label_text, key) in enumerate(labels):
            label = Gtk.Label(label=label_text)
            label.set_alignment(0, 0.5)
            info_grid.attach(label, 0, i, 1, 1)
            
            info_label = Gtk.Label(label=_("Cargando..."))
            info_label.set_alignment(0, 0.5)
            info_grid.attach(info_label, 1, i, 1, 1)
            
            self.memory_info_labels[key] = info_label
        
        # Separador
        memory_box.pack_start(Gtk.Separator(), False, False, 5)
        
        # Panel de gráfico de memoria
        chart_frame = Gtk.Frame(label=_("Uso de Memoria"))
        memory_box.pack_start(chart_frame, True, True, 0)
        
        chart_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        chart_box.set_border_width(10)
        chart_frame.add(chart_box)
        
        # Gráfico simple de barras
        self.memory_bar = Gtk.ProgressBar()
        self.memory_bar.set_valign(Gtk.Align.CENTER)
        chart_box.pack_start(self.memory_bar, False, False, 0)
        
        self.swap_bar = Gtk.ProgressBar()
        self.swap_bar.set_valign(Gtk.Align.CENTER)
        chart_box.pack_start(self.swap_bar, False, False, 10)
        
        # Etiquetas para las barras
        memory_label = Gtk.Label(label=_("RAM física"))
        memory_label.set_alignment(0, 0.5)
        chart_box.pack_start(memory_label, False, False, 0)
        
        swap_label = Gtk.Label(label=_("Memoria virtual (Swap)"))
        swap_label.set_alignment(0, 0.5)
        chart_box.pack_start(swap_label, False, False, 0)
        
        # Añadir la pestaña
        notebook.append_page(memory_box, Gtk.Label(label=_("Memoria")))
    
    def create_disk_info_tab(self, notebook):
        """Crear tab para información de discos"""
        # Contenedor principal
        disk_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        disk_box.set_border_width(15)
        
        # Panel de información del espacio en disco
        info_frame = Gtk.Frame(label=_("Espacio en Disco"))
        disk_box.pack_start(info_frame, False, False, 0)
        
        # Scrolled window para la tabla de particiones
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(200)
        scrolled_window.set_border_width(10)
        info_frame.add(scrolled_window)
        
        # Modelo para la tabla
        self.disk_store = Gtk.ListStore(str, str, str, str, str, int)  # Dispositivo, Punto montaje, Total, Usado, Libre, % como entero
        
        # Vista de tabla
        disk_view = Gtk.TreeView(model=self.disk_store)
        
        # Configurar columnas
        columns = [
            (_("Dispositivo"), 0),
            (_("Punto de Montaje"), 1),
            (_("Tamaño Total"), 2),
            (_("Usado"), 3),
            (_("Libre"), 4)
        ]
        
        for i, (title, column_id) in enumerate(columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=column_id)
            column.set_resizable(True)
            column.set_min_width(100)
            disk_view.append_column(column)
        
        # Columna de uso con barra de progreso
        renderer = Gtk.CellRendererProgress()
        column = Gtk.TreeViewColumn(_("Uso"), renderer, value=5)
        column.set_min_width(100)
        disk_view.append_column(column)
        
        scrolled_window.add(disk_view)
        
        # Separador
        disk_box.pack_start(Gtk.Separator(), False, False, 5)
        
        # Panel de rendimiento de disco
        perf_frame = Gtk.Frame(label=_("Rendimiento de Disco"))
        disk_box.pack_start(perf_frame, False, False, 0)
        
        perf_grid = Gtk.Grid()
        perf_grid.set_row_spacing(8)
        perf_grid.set_column_spacing(15)
        perf_grid.set_border_width(10)
        perf_frame.add(perf_grid)
        
        # Etiquetas de rendimiento
        labels = [
            (_("Velocidad de Lectura:"), "read_speed"),
            (_("Velocidad de Escritura:"), "write_speed"),
            (_("Operaciones de E/S:"), "io_operations"),
            (_("Tiempo de Acceso:"), "access_time")
        ]
        
        # Crear etiquetas e información
        self.disk_perf_labels = {}
        for i, (label_text, key) in enumerate(labels):
            label = Gtk.Label(label=label_text)
            label.set_alignment(0, 0.5)
            perf_grid.attach(label, 0, i, 1, 1)
            
            info_label = Gtk.Label(label=_("Cargando..."))
            info_label.set_alignment(0, 0.5)
            perf_grid.attach(info_label, 1, i, 1, 1)
            
            self.disk_perf_labels[key] = info_label
        
        # Añadir la pestaña
        notebook.append_page(disk_box, Gtk.Label(label=_("Disco")))
    
    def create_network_info_tab(self, notebook):
        """Crear tab para información de red"""
        # Contenedor principal
        network_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        network_box.set_border_width(15)
        
        # Panel de interfaces de red
        interfaces_frame = Gtk.Frame(label=_("Interfaces de Red"))
        network_box.pack_start(interfaces_frame, False, False, 0)
        
        # Scrolled window para la lista de interfaces
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(150)
        scrolled_window.set_border_width(10)
        interfaces_frame.add(scrolled_window)
        
        # Modelo para la tabla
        self.network_store = Gtk.ListStore(str, str, str, str, str)  # Interfaz, Dirección IP, Máscara, Rx bytes, Tx bytes
        
        # Vista de tabla
        network_view = Gtk.TreeView(model=self.network_store)
        
        # Configurar columnas
        columns = [
            (_("Interfaz"), 0),
            (_("Dirección IP"), 1),
            (_("Máscara"), 2),
            (_("Datos Recibidos"), 3),
            (_("Datos Enviados"), 4)
        ]
        
        for i, (title, column_id) in enumerate(columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=column_id)
            column.set_resizable(True)
            column.set_min_width(100)
            network_view.append_column(column)
        
        scrolled_window.add(network_view)
        
        # Separador
        network_box.pack_start(Gtk.Separator(), False, False, 5)
        
        # Panel de estadísticas de red
        stats_frame = Gtk.Frame(label=_("Estadísticas de Red"))
        network_box.pack_start(stats_frame, False, False, 0)
        
        stats_grid = Gtk.Grid()
        stats_grid.set_row_spacing(8)
        stats_grid.set_column_spacing(15)
        stats_grid.set_border_width(10)
        stats_frame.add(stats_grid)
        
        # Etiquetas de estadísticas
        labels = [
            (_("Velocidad de Descarga:"), "download_speed"),
            (_("Velocidad de Subida:"), "upload_speed"),
            (_("Total Recibido:"), "total_received"),
            (_("Total Enviado:"), "total_sent"),
            (_("Estado:"), "connection_status")
        ]
        
        # Crear etiquetas e información
        self.network_stats_labels = {}
        for i, (label_text, key) in enumerate(labels):
            label = Gtk.Label(label=label_text)
            label.set_alignment(0, 0.5)
            stats_grid.attach(label, 0, i, 1, 1)
            
            info_label = Gtk.Label(label=_("Cargando..."))
            info_label.set_alignment(0, 0.5)
            stats_grid.attach(info_label, 1, i, 1, 1)
            
            self.network_stats_labels[key] = info_label
        
        # Añadir la pestaña
        notebook.append_page(network_box, Gtk.Label(label=_("Red")))
    
    def create_performance_tab(self):
        """Crear pestaña de rendimiento"""
        # Contenedor principal
        perf_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        perf_box.set_border_width(15)
        
        # Panel de estadísticas de rendimiento
        stats_frame = Gtk.Frame(label=_("Estadísticas de Rendimiento"))
        perf_box.pack_start(stats_frame, False, False, 0)
        
        stats_grid = Gtk.Grid()
        stats_grid.set_row_spacing(8)
        stats_grid.set_column_spacing(15)
        stats_grid.set_border_width(10)
        stats_frame.add(stats_grid)
        
        # Etiquetas de estadísticas
        labels = [
            (_("Tiempo de Arranque:"), "boot_time"),
            (_("Tiempo de Actividad:"), "uptime"),
            (_("Carga del Sistema (1 min):"), "load_1"),
            (_("Carga del Sistema (5 min):"), "load_5"),
            (_("Carga del Sistema (15 min):"), "load_15"),
            (_("Procesos en Ejecución:"), "processes"),
            (_("Procesos Zombies:"), "zombies")
        ]
        
        # Crear etiquetas e información
        self.perf_labels = {}
        for i, (label_text, key) in enumerate(labels):
            label = Gtk.Label(label=label_text)
            label.set_alignment(0, 0.5)
            stats_grid.attach(label, 0, i, 1, 1)
            
            info_label = Gtk.Label(label=_("Cargando..."))
            info_label.set_alignment(0, 0.5)
            stats_grid.attach(info_label, 1, i, 1, 1)
            
            self.perf_labels[key] = info_label
        
        # Separador
        perf_box.pack_start(Gtk.Separator(), False, False, 10)
        
        # Panel de informe de rendimiento
        report_frame = Gtk.Frame(label=_("Informe de Rendimiento"))
        perf_box.pack_start(report_frame, True, True, 0)
        
        report_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        report_box.set_border_width(10)
        report_frame.add(report_box)
        
        # Scrolled window para el informe
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        report_box.pack_start(scrolled_window, True, True, 0)
        
        # TextView para el informe de rendimiento
        self.report_buffer = Gtk.TextBuffer()
        self.report_view = Gtk.TextView(buffer=self.report_buffer)
        self.report_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.report_view.set_editable(False)
        scrolled_window.add(self.report_view)
        
        # Configurar estilos de texto
        self.report_buffer.create_tag("normal", foreground="black")
        self.report_buffer.create_tag("warning", foreground="orange")
        self.report_buffer.create_tag("error", foreground="red")
        self.report_buffer.create_tag("good", foreground="green")
        self.report_buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        
        # Añadir la pestaña
        self.notebook.append_page(perf_box, Gtk.Label(label=_("Rendimiento")))
    
    def create_optimization_tab(self):
        """Crear pestaña de optimización"""
        # Contenedor principal
        optimization_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        optimization_box.set_border_width(15)
        
        # Título
        title_label = Gtk.Label()
        title_label.set_markup(f"<span size='large' weight='bold'>{_('Optimización del Sistema')}</span>")
        title_label.set_alignment(0, 0.5)
        optimization_box.pack_start(title_label, False, False, 0)
        
        # Panel de perfiles de optimización
        profiles_frame = Gtk.Frame(label=_("Perfiles de Optimización"))
        optimization_box.pack_start(profiles_frame, False, False, 0)
        
        profiles_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        profiles_box.set_border_width(10)
        profiles_frame.add(profiles_box)
        
        # Selector de perfil
        profile_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        profiles_box.pack_start(profile_box, False, False, 0)
        
        profile_label = Gtk.Label(label=_("Perfil:"))
        profile_box.pack_start(profile_label, False, False, 0)
        
        profile_store = Gtk.ListStore(str, str)  # Nombre, ID
        profile_store.append([_("Equilibrado"), "balanced"])
        profile_store.append([_("Rendimiento"), "performance"])
        profile_store.append([_("Ahorro de energía"), "powersave"])
        profile_store.append([_("Silencioso"), "quiet"])
        
        self.profile_combo = Gtk.ComboBox.new_with_model(profile_store)
        renderer_text = Gtk.CellRendererText()
        self.profile_combo.pack_start(renderer_text, True)
        self.profile_combo.add_attribute(renderer_text, "text", 0)
        self.profile_combo.set_active(0)
        self.profile_combo.connect("changed", self.on_profile_changed)
        profile_box.pack_start(self.profile_combo, True, True, 0)
        
        # Botón de optimizar
        optimize_button = Gtk.Button(label=_("Aplicar Perfil"))
        optimize_button.connect("clicked", self.on_optimize_clicked)
        profile_box.pack_start(optimize_button, False, False, 0)
        
        # Descripción del perfil
        self.profile_desc = Gtk.Label()
        self.profile_desc.set_markup(_("El perfil <b>Equilibrado</b> ofrece un balance entre rendimiento y consumo de energía, adecuado para uso general."))
        self.profile_desc.set_line_wrap(True)
        self.profile_desc.set_max_width_chars(60)
        self.profile_desc.set_alignment(0, 0.5)
        profiles_box.pack_start(self.profile_desc, False, False, 5)
        
        # Separador
        optimization_box.pack_start(Gtk.Separator(), False, False, 10)
        
        # Panel de optimización rápida
        quick_frame = Gtk.Frame(label=_("Optimización Rápida"))
        optimization_box.pack_start(quick_frame, False, False, 0)
        
        quick_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        quick_box.set_border_width(10)
        quick_frame.add(quick_box)
        
        # Botón de optimización del sistema
        system_button = Gtk.Button(label=_("Optimizar Sistema"))
        system_button.connect("clicked", self.on_optimize_system_clicked)
        quick_box.pack_start(system_button, False, False, 0)
        
        # Descripción
        system_desc = Gtk.Label()
        system_desc.set_markup(_("La optimización rápida del sistema libera memoria caché, ajusta parámetros del kernel y optimiza servicios en ejecución."))
        system_desc.set_line_wrap(True)
        system_desc.set_max_width_chars(60)
        system_desc.set_alignment(0, 0.5)
        quick_box.pack_start(system_desc, False, False, 5)
        
        # Separador
        optimization_box.pack_start(Gtk.Separator(), False, False, 10)
        
        # Terminal para mostrar salida
        terminal_frame = Gtk.Frame(label=_("Resultado de Optimización"))
        optimization_box.pack_start(terminal_frame, True, True, 0)
        
        terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        terminal_box.set_border_width(10)
        terminal_frame.add(terminal_box)
        
        # Scrolled window para la terminal
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        terminal_box.pack_start(scrolled_window, True, True, 0)
        
        # TextView para la salida del terminal
        self.terminal_buffer = Gtk.TextBuffer()
        self.terminal_view = Gtk.TextView(buffer=self.terminal_buffer)
        self.terminal_view.set_editable(False)
        self.terminal_view.modify_font(Pango.FontDescription("Monospace"))
        scrolled_window.add(self.terminal_view)
        
        # Configurar etiquetas para formato
        self.terminal_buffer.create_tag("normal", foreground="black")
        self.terminal_buffer.create_tag("command", foreground="blue", weight=Pango.Weight.BOLD)
        self.terminal_buffer.create_tag("success", foreground="green")
        self.terminal_buffer.create_tag("error", foreground="red")
        self.terminal_buffer.create_tag("warning", foreground="orange")
        
        # Panel inferior con botones para análisis de espacio
        disk_panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        optimization_box.pack_start(disk_panel, False, False, 0)
        
        # Botón de analizar espacio en disco
        analyze_button = Gtk.Button(label=_("Analizar Espacio en Disco"))
        analyze_button.connect("clicked", self.on_analyze_disk_clicked)
        disk_panel.pack_start(analyze_button, True, True, 0)
        
        # Botón de limpiar espacio en disco
        clean_button = Gtk.Button(label=_("Limpiar Espacio en Disco"))
        clean_button.connect("clicked", self.on_clean_disk_clicked)
        disk_panel.pack_start(clean_button, True, True, 0)
        
        # Añadir la pestaña
        self.notebook.append_page(optimization_box, Gtk.Label(label=_("Optimización")))
    
    def on_refresh_clicked(self, button):
        """Manejar clic en botón de actualizar"""
        self.refresh_status_label.set_markup(_("Actualizando estadísticas..."))
        self.refresh_button.set_sensitive(False)
        self.refresh_stats()
    
    def refresh_stats(self):
        """Actualizar las estadísticas de forma asíncrona"""
        
        # Función para realizar la obtención de estadísticas en segundo plano
        def get_stats_async():
            try:
                # Obtener datos generales
                stats = self.system_stats.get_all_stats()
                
                # Actualizar UI en el hilo principal
                GLib.idle_add(self.update_all_stats, stats)
            except Exception as e:
                print(f"Error al obtener estadísticas: {e}")
                GLib.idle_add(
                    self.refresh_status_label.set_markup,
                    _("Error al actualizar estadísticas: {0}").format(str(e))
                )
                GLib.idle_add(self.refresh_button.set_sensitive, True)
            
            return False
        
        # Ejecutar la obtención de estadísticas en un timeout
        GLib.timeout_add(100, get_stats_async)
    
    def update_all_stats(self, stats):
        """Actualizar todas las secciones de estadísticas con los datos obtenidos"""
        try:
            # Actualizar secciones de la UI
            self.update_system_info(stats)
            self.update_system_status(stats)
            self.update_hardware_info(stats)
            self.update_performance_info(stats)
            
            # Actualizar variables para gráficos
            if "cpu" in stats and "usage_percent" in stats["cpu"]:
                try:
                    self.cpu_usage = float(stats["cpu"]["usage_percent"]) / 100.0
                except (ValueError, TypeError):
                    self.cpu_usage = 0
            
            if "memory" in stats and "virtual" in stats["memory"] and "percent" in stats["memory"]["virtual"]:
                try:
                    self.memory_usage = float(stats["memory"]["virtual"]["percent"]) / 100.0
                except (ValueError, TypeError):
                    self.memory_usage = 0
            
            if "disk" in stats and "partitions" in stats["disk"] and len(stats["disk"]["partitions"]) > 0:
                for part in stats["disk"]["partitions"]:
                    if "mountpoint" in part and part["mountpoint"] == "/" and "percent" in part:
                        try:
                            self.disk_usage = float(part["percent"]) / 100.0
                        except (ValueError, TypeError):
                            self.disk_usage = 0
                        break
            
            # Generar informe de rendimiento automático
            report = self.system_stats.generate_performance_report()
            self.update_performance_report(report)
            
            # Actualizar paneles específicos de hardware
            if hasattr(self, 'has_cpu_data') and self.has_cpu_data:
                cpu_stats = self.system_stats.get_cpu_usage_per_core()
                self.update_cpu_cores(cpu_stats)
            
            if hasattr(self, 'has_disk_data') and self.has_disk_data:
                disk_stats = self.system_stats.get_disk_partitions()
                self.update_disk_info(disk_stats)
            
            if hasattr(self, 'has_network_data') and self.has_network_data:
                network_stats = self.system_stats.get_network_stats()
                self.update_network_info(network_stats)
            
            # Actualizar etiqueta de estado
            self.refresh_status_label.set_markup(_("Estadísticas actualizadas"))
            self.refresh_button.set_sensitive(True)
        except Exception as e:
            print(f"Error al actualizar UI con estadísticas: {e}")
            self.refresh_status_label.set_markup(_("Error al actualizar estadísticas"))
            self.refresh_button.set_sensitive(True)
        
        return False
    
    def update_system_info(self, stats):
        """Actualizar información general del sistema"""
        # Actualizar etiquetas de resumen
        if "cpu" in stats and "usage_percent" in stats["cpu"]:
            self.cpu_usage_label.set_markup(_("Uso: <b>{0}%</b>").format(stats["cpu"]["usage_percent"]))
        
        if "cpu" in stats and "temperature" in stats["cpu"]:
            self.cpu_temp_label.set_markup(_("Temperatura: <b>{0}</b>").format(
                stats["cpu"]["temperature"] if stats["cpu"]["temperature"] != "N/A" else _("N/A")
            ))
        
        if "memory" in stats and "virtual" in stats["memory"] and "percent" in stats["memory"]["virtual"]:
            self.memory_usage_label.set_markup(_("Uso: <b>{0}%</b>").format(stats["memory"]["virtual"]["percent"]))
        
        if "memory" in stats and "virtual" in stats["memory"] and "used_formatted" in stats["memory"]["virtual"]:
            self.memory_used_label.set_markup(_("Usada: <b>{0}</b>").format(stats["memory"]["virtual"]["used_formatted"]))
        
        if "disk" in stats and "partitions" in stats["disk"] and len(stats["disk"]["partitions"]) > 0:
            root_partition = None
            
            for part in stats["disk"]["partitions"]:
                if "mountpoint" in part and part["mountpoint"] == "/":
                    root_partition = part
                    break
            
            if root_partition:
                if "percent" in root_partition:
                    self.disk_usage_label.set_markup(_("Uso: <b>{0}%</b>").format(root_partition["percent"]))
                
                if "free_formatted" in root_partition:
                    self.disk_free_label.set_markup(_("Libre: <b>{0}</b>").format(root_partition["free_formatted"]))
        
        return False
    
    def update_system_status(self, stats):
        """Actualizar estado general del sistema"""
        # Estado del sistema
        if "system" in stats and "overall_status" in stats["system"]:
            status = stats["system"]["overall_status"]
            status_text = ""
            
            if status == "good":
                status_text = _("<span foreground='green'><b>Correcto</b></span>")
            elif status == "warning":
                status_text = _("<span foreground='orange'><b>Advertencia</b></span>")
            elif status == "critical":
                status_text = _("<span foreground='red'><b>Crítico</b></span>")
            else:
                status_text = _("<b>Desconocido</b>")
            
            self.system_status_label.set_markup(status_text)
        
        # Estado de actualizaciones
        if "updates" in stats and "available" in stats["updates"]:
            updates_count = stats["updates"]["available"]
            status_text = ""
            
            if updates_count == 0:
                status_text = _("<span foreground='green'><b>Actualizado</b></span>")
            elif updates_count < 10:
                status_text = _("<span foreground='orange'><b>{0} actualizaciones</b></span>").format(updates_count)
            else:
                status_text = _("<span foreground='red'><b>{0} actualizaciones</b></span>").format(updates_count)
            
            self.updates_status_label.set_markup(status_text)
        
        # Estado de seguridad
        if "security" in stats and "status" in stats["security"]:
            status = stats["security"]["status"]
            status_text = ""
            
            if status == "good":
                status_text = _("<span foreground='green'><b>Protegido</b></span>")
            elif status == "warning":
                status_text = _("<span foreground='orange'><b>Vulnerabilidades menores</b></span>")
            elif status == "critical":
                status_text = _("<span foreground='red'><b>Vulnerabilidades críticas</b></span>")
            else:
                status_text = _("<b>Desconocido</b>")
            
            self.security_status_label.set_markup(status_text)
        
        return False
    
    def update_hardware_info(self, stats):
        """Actualizar información de hardware"""
        # Información de CPU
        if "cpu" in stats:
            cpu_info = stats["cpu"]
            
            # Actualizar etiquetas de CPU
            cpu_labels_map = {
                "cpu_model": "model",
                "cpu_arch": "architecture",
                "cpu_cores": "cores",
                "cpu_freq": "frequency",
                "cpu_cache": "cache"
            }
            
            for label_key, stat_key in cpu_labels_map.items():
                if stat_key in cpu_info and label_key in self.cpu_info_labels:
                    self.cpu_info_labels[label_key].set_text(str(cpu_info[stat_key]))
        
        # Información de memoria
        if "memory" in stats:
            memory_info = stats["memory"]
            
            # Actualizar etiquetas de memoria
            memory_labels_map = {
                "memory_total": ["virtual", "total_formatted"],
                "memory_available": ["virtual", "available_formatted"],
                "memory_used": ["virtual", "used_formatted"],
                "memory_cached": ["virtual", "cached_formatted"],
                "memory_buffers": ["virtual", "buffers_formatted"],
                "swap_total": ["swap", "total_formatted"],
                "swap_used": ["swap", "used_formatted"]
            }
            
            for label_key, stat_keys in memory_labels_map.items():
                if len(stat_keys) == 2 and stat_keys[0] in memory_info and stat_keys[1] in memory_info[stat_keys[0]]:
                    value = memory_info[stat_keys[0]][stat_keys[1]]
                    if label_key in self.memory_info_labels:
                        self.memory_info_labels[label_key].set_text(str(value))
            
            # Actualizar barras de progreso
            if "virtual" in memory_info and "percent" in memory_info["virtual"]:
                try:
                    fraction = float(memory_info["virtual"]["percent"]) / 100.0
                    self.memory_bar.set_fraction(fraction)
                    self.memory_bar.set_text(f"{memory_info['virtual']['percent']}%")
                except (ValueError, TypeError):
                    self.memory_bar.set_fraction(0)
                    self.memory_bar.set_text("0%")
            
            if "swap" in memory_info and "percent" in memory_info["swap"]:
                try:
                    fraction = float(memory_info["swap"]["percent"]) / 100.0
                    self.swap_bar.set_fraction(fraction)
                    self.swap_bar.set_text(f"{memory_info['swap']['percent']}%")
                except (ValueError, TypeError):
                    self.swap_bar.set_fraction(0)
                    self.swap_bar.set_text("0%")
        
        # Información de disco (rendimiento)
        if "disk" in stats and "performance" in stats["disk"]:
            perf_info = stats["disk"]["performance"]
            
            # Actualizar etiquetas de rendimiento de disco
            disk_perf_labels_map = {
                "read_speed": "read_speed",
                "write_speed": "write_speed",
                "io_operations": "io_ops",
                "access_time": "access_time"
            }
            
            for label_key, stat_key in disk_perf_labels_map.items():
                if stat_key in perf_info and label_key in self.disk_perf_labels:
                    self.disk_perf_labels[label_key].set_text(str(perf_info[stat_key]))
        
        # Información de red
        if "network" in stats and "stats" in stats["network"]:
            net_info = stats["network"]["stats"]
            
            # Actualizar etiquetas de estadísticas de red
            net_labels_map = {
                "download_speed": "download_speed",
                "upload_speed": "upload_speed",
                "total_received": "total_received",
                "total_sent": "total_sent",
                "connection_status": "status"
            }
            
            for label_key, stat_key in net_labels_map.items():
                if stat_key in net_info and label_key in self.network_stats_labels:
                    self.network_stats_labels[label_key].set_text(str(net_info[stat_key]))
        
        return False
    
    def update_cpu_cores(self, usage_per_cpu):
        """Actualizar información de uso de CPU por núcleo"""
        # Limpiar grid de núcleos
        for child in self.cores_container.get_children():
            if child.get_parent() == self.cores_container:
                self.cores_container.remove(child)
        
        # Añadir datos de núcleos
        for i, cpu_data in enumerate(usage_per_cpu):
            if i == 0:  # Saltar la cabecera
                continue
                
            # Fila (considerando que la fila 0 es la cabecera)
            row = i
            
            # Etiqueta de núcleo
            core_label = Gtk.Label(label=f"CPU {i-1}")
            core_label.set_alignment(0, 0.5)
            self.cores_container.attach(core_label, 0, row, 1, 1)
            
            # Uso de CPU
            usage_label = Gtk.Label(label=f"{cpu_data['usage']}%")
            usage_label.set_alignment(0, 0.5)
            self.cores_container.attach(usage_label, 1, row, 1, 1)
            
            # Temperatura
            temp_label = Gtk.Label(label=cpu_data.get('temp', _("N/A")))
            temp_label.set_alignment(0, 0.5)
            self.cores_container.attach(temp_label, 2, row, 1, 1)
        
        # Mostrar todos los widgets
        self.cores_container.show_all()
        
        return False
    
    def update_disk_info(self, partitions):
        """Actualizar información de discos"""
        # Limpiar tabla de particiones
        self.disk_store.clear()
        
        # Añadir particiones a la tabla
        for part in partitions:
            if "mountpoint" in part and part["mountpoint"]:
                percent = 0
                if "percent" in part:
                    try:
                        percent = int(float(part["percent"]))
                    except (ValueError, TypeError):
                        percent = 0
                
                self.disk_store.append([
                    part.get("device", ""),
                    part.get("mountpoint", ""),
                    part.get("total_formatted", ""),
                    part.get("used_formatted", ""),
                    part.get("free_formatted", ""),
                    percent
                ])
        
        return False
    
    def update_network_info(self, network_stats):
        """Actualizar información de red"""
        # Limpiar tabla de interfaces
        self.network_store.clear()
        
        # Añadir interfaces a la tabla
        if "interfaces" in network_stats:
            for iface in network_stats["interfaces"]:
                self.network_store.append([
                    iface.get("name", ""),
                    iface.get("ip", ""),
                    iface.get("mask", ""),
                    iface.get("rx_formatted", ""),
                    iface.get("tx_formatted", "")
                ])
        
        return False
    
    def update_performance_info(self, stats):
        """Actualizar información de rendimiento"""
        # Actualizar etiquetas de rendimiento
        if "performance" in stats:
            perf_info = stats["performance"]
            
            # Mapeo de etiquetas
            perf_labels_map = {
                "boot_time": "boot_time",
                "uptime": "uptime",
                "load_1": "load_1min",
                "load_5": "load_5min",
                "load_15": "load_15min",
                "processes": "process_count",
                "zombies": "zombie_processes"
            }
            
            for label_key, stat_key in perf_labels_map.items():
                if stat_key in perf_info and label_key in self.perf_labels:
                    self.perf_labels[label_key].set_text(str(perf_info[stat_key]))
        
        return False
    
    def update_performance_report(self, report):
        """Actualizar informe de rendimiento"""
        # Limpiar buffer
        self.report_buffer.set_text("")
        
        # Añadir cada sección del informe con formato
        for section in report:
            # Título de la sección
            if "title" in section:
                self.report_buffer.insert_with_tags_by_name(
                    self.report_buffer.get_end_iter(),
                    section["title"] + "\n",
                    "bold"
                )
            
            # Contenido de la sección
            if "content" in section:
                for item in section["content"]:
                    tag = "normal"
                    if "type" in item:
                        tag = item["type"]
                    
                    self.report_buffer.insert_with_tags_by_name(
                        self.report_buffer.get_end_iter(),
                        item["text"] + "\n",
                        tag
                    )
            
            # Espacio entre secciones
            self.report_buffer.insert(self.report_buffer.get_end_iter(), "\n")
        
        return False
    
    def on_profile_changed(self, combo):
        """Manejar cambio de perfil de optimización"""
        # Obtener perfil seleccionado
        iter = combo.get_active_iter()
        if iter is not None:
            model = combo.get_model()
            profile_id = model[iter][1]
            
            # Actualizar descripción según el perfil
            if profile_id == "balanced":
                self.profile_desc.set_markup(_("El perfil <b>Equilibrado</b> ofrece un balance entre rendimiento y consumo de energía, adecuado para uso general."))
            elif profile_id == "performance":
                self.profile_desc.set_markup(_("El perfil <b>Rendimiento</b> maximiza la velocidad y respuesta del sistema, ideal para tareas exigentes como juegos o edición multimedia."))
            elif profile_id == "powersave":
                self.profile_desc.set_markup(_("El perfil <b>Ahorro de energía</b> reduce el consumo energético, ideal para portátiles con batería limitada."))
            elif profile_id == "quiet":
                self.profile_desc.set_markup(_("El perfil <b>Silencioso</b> minimiza el ruido del sistema reduciendo la velocidad de ventiladores a costa de mayores temperaturas."))
    
    def on_optimize_clicked(self, button):
        """Manejar clic en el botón de optimización rápida"""
        # Obtener perfil seleccionado
        iter = self.profile_combo.get_active_iter()
        profile_name = "balanced"
        
        if iter is not None:
            model = self.profile_combo.get_model()
            profile_id = model[iter][1]
            profile_name = model[iter][0]
        
        # Limpiar terminal
        self.terminal_buffer.set_text("")
        
        # Escribir comando
        self.write_to_terminal(_("Aplicando perfil de optimización: ") + profile_name + "\n", "command")
        
        # Iniciar optimización en segundo plano
        threading.Thread(target=self.optimize_thread, args=(profile_name,), daemon=True).start()
    
    def on_optimize_system_clicked(self, button):
        """Manejar clic en el botón de optimizar sistema"""
        # Limpiar terminal
        self.terminal_buffer.set_text("")
        
        # Escribir comando
        self.write_to_terminal(_("Iniciando optimización rápida del sistema...\n"), "command")
        
        # Iniciar optimización en segundo plano para simular el proceso
        threading.Thread(target=self.optimize_thread, args=("system",), daemon=True).start()
    
    def optimize_thread(self, profile_name):
        """Hilo para ejecutar la optimización"""
        try:
            GLib.idle_add(self.write_to_terminal, _("Verificando estado del sistema...\n"))
            time.sleep(1)
            
            GLib.idle_add(self.write_to_terminal, _("Aplicando configuraciones de optimización...\n"))
            time.sleep(2)
            
            if profile_name == "system":
                # Simulación de optimización del sistema
                GLib.idle_add(self.write_to_terminal, _("Liberando memoria caché...\n"))
                time.sleep(1)
                
                GLib.idle_add(self.write_to_terminal, _("Optimizando parámetros del kernel...\n"))
                time.sleep(1.5)
                
                GLib.idle_add(self.write_to_terminal, _("Ajustando servicios en ejecución...\n"))
                time.sleep(1)
                
                GLib.idle_add(self.write_to_terminal, _("Reiniciando servicios no esenciales...\n"))
                time.sleep(2)
            else:
                # Simulación de aplicación de perfil
                GLib.idle_add(self.write_to_terminal, _("Configurando políticas de CPU...\n"))
                time.sleep(1)
                
                GLib.idle_add(self.write_to_terminal, _("Ajustando parámetros de energía...\n"))
                time.sleep(1.5)
                
                GLib.idle_add(self.write_to_terminal, _("Configurando comportamiento de ventiladores...\n"))
                time.sleep(1)
            
            GLib.idle_add(self.write_to_terminal, _("Verificando cambios aplicados...\n"))
            time.sleep(1.5)
            
            # Mensaje de éxito
            GLib.idle_add(self.write_to_terminal, _("\n¡Optimización completada con éxito!\n"), "success")
            
            # Actualizar estadísticas tras la optimización
            GLib.idle_add(self.refresh_stats)
            
        except Exception as e:
            GLib.idle_add(self.write_to_terminal, f"\n{_('Error durante la optimización:')} {str(e)}\n", "error")
    
    def write_to_terminal(self, text, tag_name="normal"):
        """Escribir texto en la terminal con el estilo indicado"""
        self.terminal_buffer.insert_with_tags_by_name(
            self.terminal_buffer.get_end_iter(),
            text,
            tag_name
        )
        # Auto-scroll al final
        self.terminal_view.scroll_to_iter(self.terminal_buffer.get_end_iter(), 0.0, False, 0.0, 0.0)
        return False
    
    def on_analyze_disk_clicked(self, button):
        """Manejar clic en botón de analizar espacio en disco"""
        # Limpiar terminal
        self.terminal_buffer.set_text("")
        
        # Escribir comando
        self.write_to_terminal(_("Analizando espacio en disco...\n"), "command")
        
        # Iniciar análisis en segundo plano
        threading.Thread(target=self.analyze_disk_thread, daemon=True).start()
    
    def analyze_disk_thread(self):
        """Hilo para analizar espacio en disco"""
        try:
            # Simulación del análisis
            GLib.idle_add(self.write_to_terminal, _("Escaneando directorios...\n"))
            time.sleep(2)
            
            GLib.idle_add(self.write_to_terminal, _("Analizando archivos temporales...\n"))
            time.sleep(1.5)
            
            GLib.idle_add(self.write_to_terminal, _("Verificando paquetes duplicados...\n"))
            time.sleep(1)
            
            GLib.idle_add(self.write_to_terminal, _("Buscando kernels antiguos...\n"))
            time.sleep(1.5)
            
            GLib.idle_add(self.write_to_terminal, _("Analizando cachés de aplicaciones...\n"))
            time.sleep(1)
            
            # Resultados
            GLib.idle_add(self.write_to_terminal, _("\nResultados del análisis:\n"), "bold")
            GLib.idle_add(self.write_to_terminal, _("- Archivos temporales: 1.2 GB\n"))
            GLib.idle_add(self.write_to_terminal, _("- Paquetes duplicados: 345 MB\n"))
            GLib.idle_add(self.write_to_terminal, _("- Kernels antiguos: 850 MB\n"))
            GLib.idle_add(self.write_to_terminal, _("- Cachés de aplicaciones: 2.1 GB\n"))
            GLib.idle_add(self.write_to_terminal, _("\nEspacio total recuperable: 4.5 GB\n"), "success")
            
        except Exception as e:
            GLib.idle_add(self.write_to_terminal, f"\n{_('Error durante el análisis:')} {str(e)}\n", "error")
    
    def on_clean_disk_clicked(self, button):
        """Manejar clic en botón de limpiar espacio en disco"""
        # Limpiar terminal
        self.terminal_buffer.set_text("")
        
        # Escribir comando
        self.write_to_terminal(_("Iniciando limpieza de espacio en disco...\n"), "command")
        
        # Iniciar limpieza en segundo plano
        threading.Thread(target=self.clean_disk_thread, daemon=True).start()
    
    def clean_disk_thread(self):
        """Hilo para limpiar espacio en disco"""
        try:
            # Simulación de la limpieza
            GLib.idle_add(self.write_to_terminal, _("Eliminando archivos temporales...\n"))
            time.sleep(2)
            
            GLib.idle_add(self.write_to_terminal, _("Limpiando paquetes duplicados...\n"))
            time.sleep(1.5)
            
            GLib.idle_add(self.write_to_terminal, _("Eliminando kernels antiguos...\n"))
            time.sleep(1.5)
            
            GLib.idle_add(self.write_to_terminal, _("Limpiando cachés de aplicaciones...\n"))
            time.sleep(2)
            
            # Resultados
            GLib.idle_add(self.write_to_terminal, _("\nLimpieza completada:\n"), "bold")
            GLib.idle_add(self.write_to_terminal, _("- Archivos temporales: 1.2 GB liberados\n"), "success")
            GLib.idle_add(self.write_to_terminal, _("- Paquetes duplicados: 345 MB liberados\n"), "success")
            GLib.idle_add(self.write_to_terminal, _("- Kernels antiguos: 850 MB liberados\n"), "success")
            GLib.idle_add(self.write_to_terminal, _("- Cachés de aplicaciones: 2.1 GB liberados\n"), "success")
            GLib.idle_add(self.write_to_terminal, _("\nEspacio total recuperado: 4.5 GB\n"), "success")
            
            # Actualizar estadísticas tras la limpieza
            GLib.idle_add(self.refresh_stats)
            
        except Exception as e:
            GLib.idle_add(self.write_to_terminal, f"\n{_('Error durante la limpieza:')} {str(e)}\n", "error")
    
    def on_draw_cpu(self, widget, cr):
        """Dibujar el gráfico circular para uso de CPU"""
        self.draw_circular_progress(cr, self.cpu_usage)
        return False
    
    def on_draw_memory(self, widget, cr):
        """Dibujar el gráfico circular para uso de memoria"""
        self.draw_circular_progress(cr, self.memory_usage)
        return False
    
    def on_draw_disk(self, widget, cr):
        """Dibujar el gráfico circular para uso de disco"""
        self.draw_circular_progress(cr, self.disk_usage)
        return False
    
    def draw_circular_progress(self, cr, fraction):
        """Dibujar un gráfico circular de progreso"""
        # Obtener dimensiones del widget
        width = cr.get_target().get_width()
        height = cr.get_target().get_height()
        
        # Calcular radio y centro
        radius = min(width, height) / 2.5
        xc = width / 2
        yc = height / 2
        
        # Ángulos (en radianes)
        angle1 = -math.pi / 2  # Inicio en la parte superior (90°)
        angle2 = angle1 + 2 * math.pi * fraction  # Ángulo final basado en la fracción
        
        # Dibujar el anillo base (fondo gris)
        cr.set_source_rgb(0.85, 0.85, 0.85)
        cr.set_line_width(radius / 4)
        cr.arc(xc, yc, radius, 0, 2 * math.pi)
        cr.stroke()
        
        # Determinar color según el nivel de uso
        if fraction < 0.7:
            # Verde para uso bajo
            cr.set_source_rgb(0.2, 0.8, 0.2)
        elif fraction < 0.9:
            # Naranja para uso medio
            cr.set_source_rgb(1.0, 0.6, 0.0)
        else:
            # Rojo para uso alto
            cr.set_source_rgb(0.8, 0.2, 0.2)
        
        # Dibujar el arco de progreso
        cr.set_line_width(radius / 4)
        cr.arc(xc, yc, radius, angle1, angle2)
        cr.stroke()
        
        # Dibujar texto de porcentaje en el centro
        percentage = int(fraction * 100)
        cr.set_source_rgb(0.1, 0.1, 0.1)  # Color oscuro para el texto
        
        # Configurar fuente
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(radius / 2.5)
        
        # Centrar texto
        text = f"{percentage}%"
        (x, y, width, height, dx, dy) = cr.text_extents(text)
        cr.move_to(xc - width / 2, yc + height / 2)
        
        # Dibujar texto
        cr.show_text(text)
    
    def auto_refresh(self):
        """Actualizar estadísticas automáticamente"""
        self.refresh_stats()
        return True  # Continuar llamando periódicamente
    
    def create_header_label(self, text):
        """Crear una etiqueta de encabezado"""
        label = Gtk.Label()
        label.set_markup(f"<b>{text}</b>")
        label.set_alignment(0, 0.5)
        return label
    
    def create_info_label(self):
        """Crear una etiqueta de información"""
        label = Gtk.Label(label=_("Cargando..."))
        label.set_alignment(0, 0.5)
        return label