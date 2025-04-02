#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para la gestión de notificaciones del sistema.
Proporciona funciones para mostrar notificaciones y programar alertas.
"""

import os
import logging
import json
import time
from datetime import datetime, timedelta
import threading
import subprocess
from utils.utils import ensure_dirs_exist, execute_command

class NotificationManager:
    """Gestor de notificaciones del sistema"""
    
    def __init__(self, config_dir=None, notifications_enabled=True):
        """
        Inicializar el gestor de notificaciones
        
        Args:
            config_dir: Directorio de configuración (opcional)
            notifications_enabled: Si las notificaciones están habilitadas
        """
        self.logger = logging.getLogger("DexterSOA.NotificationManager")
        
        # Directorio de configuración
        self.config_dir = config_dir or os.path.expanduser("~/.config/dexter-soa")
        
        # Archivo de notificaciones programadas
        self.schedules_file = os.path.join(self.config_dir, "scheduled_notifications.json")
        
        # Si las notificaciones están habilitadas
        self.notifications_enabled = notifications_enabled
        
        # Hilo de verificación de notificaciones programadas
        self.check_thread = None
        self.check_thread_running = False
        
        # Asegurar que exista el directorio de configuración
        ensure_dirs_exist()
    
    def send_notification(self, title, message, urgency="normal", icon=None):
        """
        Enviar una notificación al sistema
        
        Args:
            title: Título de la notificación
            message: Mensaje de la notificación
            urgency: Urgencia ("low", "normal", "critical")
            icon: Ruta al icono (opcional)
            
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        if not self.notifications_enabled:
            self.logger.info(f"Notificación desactivada: {title}")
            return False
        
        self.logger.debug(f"Enviando notificación: {title}")
        
        try:
            # Preparar comando para notify-send
            command = ["notify-send"]
            
            # Añadir urgencia
            if urgency in ["low", "normal", "critical"]:
                command.extend(["-u", urgency])
            
            # Añadir icono si se especificó
            if icon and os.path.exists(icon):
                command.extend(["-i", icon])
            
            # Añadir título y mensaje
            command.extend([title, message])
            
            # Ejecutar comando
            returncode, output = execute_command(command, shell=False)
            
            if returncode != 0:
                self.logger.error(f"Error al enviar notificación: {output}")
                return False
            
            self.logger.debug("Notificación enviada correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al enviar notificación: {e}")
            return False
    
    def load_scheduled_notifications(self):
        """
        Cargar notificaciones programadas desde el archivo
        
        Returns:
            list: Lista de notificaciones programadas
        """
        ensure_dirs_exist()
        
        if not os.path.exists(self.schedules_file):
            return []
        
        try:
            with open(self.schedules_file, 'r') as f:
                schedules = json.load(f)
            
            # Convertir cadenas de fecha a objetos datetime
            for schedule in schedules:
                if 'next_time' in schedule and schedule['next_time']:
                    schedule['next_time'] = datetime.fromisoformat(schedule['next_time'])
            
            return schedules
        except Exception as e:
            self.logger.error(f"Error al cargar notificaciones programadas: {e}")
            return []
    
    def save_scheduled_notifications(self, schedules):
        """
        Guardar notificaciones programadas en el archivo
        
        Args:
            schedules: Lista de notificaciones programadas
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        ensure_dirs_exist()
        
        try:
            # Convertir objetos datetime a cadenas ISO
            schedules_to_save = []
            for schedule in schedules:
                schedule_copy = schedule.copy()
                if 'next_time' in schedule_copy and isinstance(schedule_copy['next_time'], datetime):
                    schedule_copy['next_time'] = schedule_copy['next_time'].isoformat()
                schedules_to_save.append(schedule_copy)
            
            with open(self.schedules_file, 'w') as f:
                json.dump(schedules_to_save, f, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Error al guardar notificaciones programadas: {e}")
            return False
    
    def add_scheduled_notification(self, title, message, interval_days, urgency="normal", icon=None):
        """
        Añadir una notificación programada
        
        Args:
            title: Título de la notificación
            message: Mensaje de la notificación
            interval_days: Intervalo en días entre notificaciones
            urgency: Urgencia ("low", "normal", "critical")
            icon: Ruta al icono (opcional)
            
        Returns:
            bool: True si se añadió correctamente, False en caso contrario
        """
        self.logger.info(f"Añadiendo notificación programada: {title} (cada {interval_days} días)")
        
        try:
            # Cargar notificaciones existentes
            schedules = self.load_scheduled_notifications()
            
            # Crear nueva notificación programada
            next_time = datetime.now() + timedelta(days=interval_days)
            
            new_schedule = {
                'id': int(time.time()),
                'title': title,
                'message': message,
                'interval_days': interval_days,
                'urgency': urgency,
                'icon': icon,
                'next_time': next_time,
                'enabled': True
            }
            
            # Añadir a la lista
            schedules.append(new_schedule)
            
            # Guardar lista actualizada
            if self.save_scheduled_notifications(schedules):
                self.logger.info(f"Notificación programada añadida correctamente: {title}")
                return True
            else:
                self.logger.error(f"Error al guardar notificación programada: {title}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al añadir notificación programada: {e}")
            return False
    
    def remove_scheduled_notification(self, notification_id):
        """
        Eliminar una notificación programada
        
        Args:
            notification_id: ID de la notificación a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        self.logger.info(f"Eliminando notificación programada: {notification_id}")
        
        try:
            # Cargar notificaciones existentes
            schedules = self.load_scheduled_notifications()
            
            # Filtrar la notificación a eliminar
            new_schedules = [s for s in schedules if s.get('id') != notification_id]
            
            # Verificar si se eliminó alguna
            if len(new_schedules) == len(schedules):
                self.logger.warning(f"No se encontró notificación con ID: {notification_id}")
                return False
            
            # Guardar lista actualizada
            if self.save_scheduled_notifications(new_schedules):
                self.logger.info(f"Notificación programada eliminada correctamente: {notification_id}")
                return True
            else:
                self.logger.error(f"Error al guardar después de eliminar notificación: {notification_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error al eliminar notificación programada: {e}")
            return False
    
    def update_scheduled_notification(self, notification_id, enabled=None, title=None, message=None, 
                                     interval_days=None, urgency=None, icon=None, next_time=None):
        """
        Actualizar una notificación programada
        
        Args:
            notification_id: ID de la notificación a actualizar
            enabled: Estado de activación (opcional)
            title: Nuevo título (opcional)
            message: Nuevo mensaje (opcional)
            interval_days: Nuevo intervalo (opcional)
            urgency: Nueva urgencia (opcional)
            icon: Nuevo icono (opcional)
            next_time: Nueva hora para la próxima notificación (opcional)
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        self.logger.info(f"Actualizando notificación programada: {notification_id}")
        
        try:
            # Cargar notificaciones existentes
            schedules = self.load_scheduled_notifications()
            
            # Buscar la notificación a actualizar
            for schedule in schedules:
                if schedule.get('id') == notification_id:
                    # Actualizar campos según lo especificado
                    if enabled is not None:
                        schedule['enabled'] = enabled
                    if title is not None:
                        schedule['title'] = title
                    if message is not None:
                        schedule['message'] = message
                    if interval_days is not None:
                        schedule['interval_days'] = interval_days
                    if urgency is not None:
                        schedule['urgency'] = urgency
                    if icon is not None:
                        schedule['icon'] = icon
                    if next_time is not None:
                        schedule['next_time'] = next_time
                    
                    # Guardar lista actualizada
                    if self.save_scheduled_notifications(schedules):
                        self.logger.info(f"Notificación programada actualizada correctamente: {notification_id}")
                        return True
                    else:
                        self.logger.error(f"Error al guardar después de actualizar notificación: {notification_id}")
                        return False
            
            # Si no se encontró la notificación
            self.logger.warning(f"No se encontró notificación con ID: {notification_id}")
            return False
                
        except Exception as e:
            self.logger.error(f"Error al actualizar notificación programada: {e}")
            return False
    
    def check_scheduled_notifications(self):
        """
        Verificar notificaciones programadas y enviar las que corresponda
        
        Returns:
            list: Lista de notificaciones enviadas
        """
        if not self.notifications_enabled:
            return []
        
        self.logger.debug("Verificando notificaciones programadas")
        
        try:
            # Cargar notificaciones programadas
            schedules = self.load_scheduled_notifications()
            
            # Verificar si alguna debe enviarse
            now = datetime.now()
            sent_notifications = []
            updated = False
            
            for schedule in schedules:
                # Verificar si está habilitada y es hora de enviarla
                if schedule.get('enabled', True) and 'next_time' in schedule:
                    next_time = schedule['next_time']
                    
                    if next_time <= now:
                        # Enviar notificación
                        title = schedule.get('title', 'DexterSOA')
                        message = schedule.get('message', 'Recordatorio programado')
                        urgency = schedule.get('urgency', 'normal')
                        icon = schedule.get('icon')
                        
                        if self.send_notification(title, message, urgency, icon):
                            sent_notifications.append(schedule)
                            
                            # Calcular siguiente hora de notificación
                            interval_days = schedule.get('interval_days', 7)
                            schedule['next_time'] = now + timedelta(days=interval_days)
                            updated = True
            
            # Guardar cambios si se actualizó alguna notificación
            if updated:
                self.save_scheduled_notifications(schedules)
            
            return sent_notifications
            
        except Exception as e:
            self.logger.error(f"Error al verificar notificaciones programadas: {e}")
            return []
    
    def start_check_thread(self, interval=3600):
        """
        Iniciar hilo de verificación periódica de notificaciones
        
        Args:
            interval: Intervalo de verificación en segundos (1 hora por defecto)
            
        Returns:
            bool: True si se inició correctamente, False en caso contrario
        """
        if self.check_thread_running:
            self.logger.warning("El hilo de verificación ya está en ejecución")
            return False
        
        self.logger.info(f"Iniciando hilo de verificación de notificaciones (intervalo: {interval}s)")
        
        try:
            self.check_thread_running = True
            
            def check_thread_func():
                while self.check_thread_running:
                    self.check_scheduled_notifications()
                    time.sleep(interval)
            
            self.check_thread = threading.Thread(target=check_thread_func)
            self.check_thread.daemon = True
            self.check_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al iniciar hilo de verificación: {e}")
            self.check_thread_running = False
            return False
    
    def stop_check_thread(self):
        """
        Detener hilo de verificación periódica de notificaciones
        
        Returns:
            bool: True si se detuvo correctamente, False en caso contrario
        """
        if not self.check_thread_running:
            return True
        
        self.logger.info("Deteniendo hilo de verificación de notificaciones")
        
        try:
            self.check_thread_running = False
            
            if self.check_thread:
                self.check_thread.join(timeout=1)
                self.check_thread = None
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al detener hilo de verificación: {e}")
            return False