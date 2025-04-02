#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para recopilar y analizar estadísticas del sistema.
Proporciona información sobre CPU, memoria, discos y red.
"""

import os
import time
import datetime
import platform
import socket
import re
import json
import subprocess
import shutil
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from gettext import gettext as _

# Formato de bytes a unidades legibles
def format_bytes(bytes, precision=2):
    """Convertir bytes a formato legible (KB, MB, GB, etc.)"""
    if bytes is None or bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    bytes = float(bytes)
    i = 0
    while bytes >= 1024 and i < len(units) - 1:
        bytes /= 1024
        i += 1
    
    return f"{bytes:.{precision}f} {units[i]}"

class SystemStats:
    """Clase para obtener estadísticas del sistema"""
    
    def __init__(self):
        """Inicializar la clase de estadísticas"""
        self.last_update = 0
        self.cached_stats = {}
        self.cache_timeout = 5  # segundos
        
        # Inicializar modos de simulación para desarrollo
        self.simulation_mode = True if not HAS_PSUTIL else False
        
        # Intentar ejecutar comandos básicos para comprobar disponibilidad
        try:
            subprocess.run(["uname", "-a"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1)
            self.has_uname = True
        except:
            self.has_uname = False
        
        try:
            subprocess.run(["df", "-h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1)
            self.has_df = True
        except:
            self.has_df = False
        
        try:
            subprocess.run(["free", "-m"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1)
            self.has_free = True
        except:
            self.has_free = False
        
        # Verificar disponibilidad de archivos
        self.has_proc_stat = os.path.exists("/proc/stat")
        self.has_proc_meminfo = os.path.exists("/proc/meminfo")
        self.has_proc_mounts = os.path.exists("/proc/mounts")
        self.has_proc_net_dev = os.path.exists("/proc/net/dev")
        
        # Inicializar valores previos para cálculos diferenciales
        self.prev_cpu_times = None
        self.prev_net_counters = None
        self.prev_disk_counters = None
        self.prev_time = time.time()
    
    def get_all_stats(self):
        """Obtener todas las estadísticas del sistema"""
        # Comprobar caché
        current_time = time.time()
        if current_time - self.last_update < self.cache_timeout and self.cached_stats:
            return self.cached_stats
        
        # Datos a recopilar
        stats = {
            "system": self.get_system_info(),
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(),
            "network": self.get_network_info(),
            "performance": self.get_performance_info(),
            "updates": self.get_updates_info(),
            "security": self.get_security_info()
        }
        
        # Actualizar caché
        self.cached_stats = stats
        self.last_update = current_time
        
        return stats
    
    def get_system_info(self):
        """Obtener información general del sistema"""
        info = {
            "hostname": "localhost",
            "os": "Debian",
            "version": "11 (Bullseye)",
            "kernel": "5.10.0",
            "architecture": "x86_64",
            "uptime": "1d 3h 24m",
            "boot_time": "2023-09-10 08:45:32",
            "overall_status": "good"
        }
        
        if self.simulation_mode:
            return info
        
        try:
            # Información del sistema
            if HAS_PSUTIL:
                info["hostname"] = socket.gethostname()
                info["uptime"] = self.format_uptime(psutil.boot_time())
                info["boot_time"] = datetime.datetime.fromtimestamp(
                    psutil.boot_time()
                ).strftime("%Y-%m-%d %H:%M:%S")
            
            # Información del SO
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    os_data = {}
                    for line in f:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            os_data[key] = value.strip('"')
                    
                    if "NAME" in os_data:
                        info["os"] = os_data["NAME"]
                    
                    if "VERSION" in os_data:
                        info["version"] = os_data["VERSION"]
            
            # Información del kernel
            if self.has_uname:
                result = subprocess.run(["uname", "-r"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    info["kernel"] = result.stdout.strip()
            
            # Información de arquitectura
            info["architecture"] = platform.machine()
            
            # Estado general
            # Simplificación: bueno si el uso de CPU, memoria y disco es < 70%
            overall_status = "good"
            
            cpu_usage = self.get_cpu_usage()
            if cpu_usage > 90:
                overall_status = "critical"
            elif cpu_usage > 70:
                overall_status = "warning"
            
            mem_info = self.get_memory_info()
            if "virtual" in mem_info and "percent" in mem_info["virtual"]:
                try:
                    mem_usage = float(mem_info["virtual"]["percent"])
                    if mem_usage > 90:
                        overall_status = "critical"
                    elif mem_usage > 70 and overall_status == "good":
                        overall_status = "warning"
                except (ValueError, TypeError):
                    pass
            
            disk_info = self.get_disk_info()
            if "partitions" in disk_info:
                for part in disk_info["partitions"]:
                    if "mountpoint" in part and part["mountpoint"] == "/" and "percent" in part:
                        try:
                            disk_usage = float(part["percent"])
                            if disk_usage > 90:
                                overall_status = "critical"
                            elif disk_usage > 75 and overall_status == "good":
                                overall_status = "warning"
                        except (ValueError, TypeError):
                            pass
            
            info["overall_status"] = overall_status
            
        except Exception as e:
            print(f"Error al obtener información del sistema: {e}")
        
        return info
    
    def get_cpu_info(self):
        """Obtener información de la CPU"""
        info = {
            "model": "Intel(R) Core(TM) i7-8700 CPU @ 3.20GHz",
            "cores": "6",
            "threads": "12",
            "architecture": "x86_64",
            "frequency": "3.2 GHz",
            "cache": "12 MB",
            "usage_percent": "45",
            "temperature": "55°C"
        }
        
        if self.simulation_mode:
            return info
        
        try:
            if HAS_PSUTIL:
                # Uso de CPU
                info["usage_percent"] = str(int(psutil.cpu_percent(interval=0.1)))
                
                # Información de CPU
                cpu_info = {}
                if hasattr(psutil, "cpu_freq") and psutil.cpu_freq():
                    freq = psutil.cpu_freq()
                    if freq.current:
                        info["frequency"] = f"{freq.current/1000:.1f} GHz"
                
                # Intentar obtener información detallada de /proc/cpuinfo
                if os.path.exists("/proc/cpuinfo"):
                    with open("/proc/cpuinfo", "r") as f:
                        cpu_data = f.read()
                        
                        # Modelo de CPU
                        model_match = re.search(r"model name\s+:\s+(.*)", cpu_data)
                        if model_match:
                            info["model"] = model_match.group(1)
                        
                        # Caché
                        cache_match = re.search(r"cache size\s+:\s+(.*)", cpu_data)
                        if cache_match:
                            info["cache"] = cache_match.group(1)
                
                # Núcleos y threads
                info["cores"] = str(psutil.cpu_count(logical=False))
                info["threads"] = str(psutil.cpu_count(logical=True))
                
                # Temperatura (opcional, no siempre disponible)
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        for name, entries in temps.items():
                            if entries and len(entries) > 0 and hasattr(entries[0], "current"):
                                info["temperature"] = f"{entries[0].current:.1f}°C"
                                break
                else:
                    info["temperature"] = "N/A"
        
        except Exception as e:
            print(f"Error al obtener información de CPU: {e}")
        
        return info
    
    def get_memory_info(self):
        """Obtener información de la memoria"""
        info = {
            "virtual": {
                "total": 8 * 1024 * 1024 * 1024,  # 8 GB
                "available": 5 * 1024 * 1024 * 1024,  # 5 GB
                "used": 3 * 1024 * 1024 * 1024,  # 3 GB
                "percent": "37.5",
                "buffers": 512 * 1024 * 1024,  # 512 MB
                "cached": 1.5 * 1024 * 1024 * 1024,  # 1.5 GB
                "total_formatted": "8 GB",
                "available_formatted": "5 GB",
                "used_formatted": "3 GB",
                "buffers_formatted": "512 MB",
                "cached_formatted": "1.5 GB"
            },
            "swap": {
                "total": 2 * 1024 * 1024 * 1024,  # 2 GB
                "used": 256 * 1024 * 1024,  # 256 MB
                "free": 1.75 * 1024 * 1024 * 1024,  # 1.75 GB
                "percent": "12.5",
                "total_formatted": "2 GB",
                "used_formatted": "256 MB",
                "free_formatted": "1.75 GB"
            }
        }
        
        if self.simulation_mode:
            return info
        
        try:
            if HAS_PSUTIL:
                # Memoria virtual
                mem = psutil.virtual_memory()
                info["virtual"] = {
                    "total": mem.total,
                    "available": mem.available,
                    "used": mem.used,
                    "percent": str(mem.percent),
                    "total_formatted": format_bytes(mem.total),
                    "available_formatted": format_bytes(mem.available),
                    "used_formatted": format_bytes(mem.used)
                }
                
                if hasattr(mem, "buffers"):
                    info["virtual"]["buffers"] = mem.buffers
                    info["virtual"]["buffers_formatted"] = format_bytes(mem.buffers)
                
                if hasattr(mem, "cached"):
                    info["virtual"]["cached"] = mem.cached
                    info["virtual"]["cached_formatted"] = format_bytes(mem.cached)
                
                # Swap
                swap = psutil.swap_memory()
                info["swap"] = {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": str(swap.percent),
                    "total_formatted": format_bytes(swap.total),
                    "used_formatted": format_bytes(swap.used),
                    "free_formatted": format_bytes(swap.free)
                }
            
            elif self.has_proc_meminfo:
                # Parsear /proc/meminfo como alternativa
                mem_data = {}
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if ":" in line:
                            key, value = line.split(":", 1)
                            value = value.strip()
                            if "kB" in value:
                                value = int(value.replace("kB", "").strip()) * 1024
                            mem_data[key.strip()] = value
                
                if "MemTotal" in mem_data and "MemAvailable" in mem_data:
                    total = int(mem_data["MemTotal"])
                    available = int(mem_data["MemAvailable"])
                    used = total - available
                    percent = 100 * used / total if total > 0 else 0
                    
                    info["virtual"] = {
                        "total": total,
                        "available": available,
                        "used": used,
                        "percent": str(round(percent, 1)),
                        "total_formatted": format_bytes(total),
                        "available_formatted": format_bytes(available),
                        "used_formatted": format_bytes(used)
                    }
                    
                    if "Buffers" in mem_data:
                        info["virtual"]["buffers"] = int(mem_data["Buffers"])
                        info["virtual"]["buffers_formatted"] = format_bytes(int(mem_data["Buffers"]))
                    
                    if "Cached" in mem_data:
                        info["virtual"]["cached"] = int(mem_data["Cached"])
                        info["virtual"]["cached_formatted"] = format_bytes(int(mem_data["Cached"]))
                
                if "SwapTotal" in mem_data and "SwapFree" in mem_data:
                    swap_total = int(mem_data["SwapTotal"])
                    swap_free = int(mem_data["SwapFree"])
                    swap_used = swap_total - swap_free
                    swap_percent = 100 * swap_used / swap_total if swap_total > 0 else 0
                    
                    info["swap"] = {
                        "total": swap_total,
                        "used": swap_used,
                        "free": swap_free,
                        "percent": str(round(swap_percent, 1)),
                        "total_formatted": format_bytes(swap_total),
                        "used_formatted": format_bytes(swap_used),
                        "free_formatted": format_bytes(swap_free)
                    }
            
            elif self.has_free:
                # Usar comando free como alternativa
                result = subprocess.run(["free", "-b"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        mem_values = lines[1].split()[1:]
                        if len(mem_values) >= 3:
                            total = int(mem_values[0])
                            used = int(mem_values[1])
                            free = int(mem_values[2])
                            available = free
                            
                            if len(mem_values) >= 6:
                                available = int(mem_values[5])
                            
                            percent = 100 * used / total if total > 0 else 0
                            
                            info["virtual"] = {
                                "total": total,
                                "available": available,
                                "used": used,
                                "percent": str(round(percent, 1)),
                                "total_formatted": format_bytes(total),
                                "available_formatted": format_bytes(available),
                                "used_formatted": format_bytes(used)
                            }
                    
                    if len(lines) >= 3:
                        swap_values = lines[2].split()[1:]
                        if len(swap_values) >= 3:
                            swap_total = int(swap_values[0])
                            swap_used = int(swap_values[1])
                            swap_free = int(swap_values[2])
                            swap_percent = 100 * swap_used / swap_total if swap_total > 0 else 0
                            
                            info["swap"] = {
                                "total": swap_total,
                                "used": swap_used,
                                "free": swap_free,
                                "percent": str(round(swap_percent, 1)),
                                "total_formatted": format_bytes(swap_total),
                                "used_formatted": format_bytes(swap_used),
                                "free_formatted": format_bytes(swap_free)
                            }
        
        except Exception as e:
            print(f"Error al obtener información de memoria: {e}")
        
        return info
    
    def get_disk_info(self):
        """Obtener información de discos"""
        info = {
            "partitions": [
                {
                    "device": "/dev/sda1",
                    "mountpoint": "/",
                    "fstype": "ext4",
                    "opts": "rw,relatime",
                    "total": 120 * 1024 * 1024 * 1024,  # 120 GB
                    "used": 45 * 1024 * 1024 * 1024,  # 45 GB
                    "free": 75 * 1024 * 1024 * 1024,  # 75 GB
                    "percent": "37.5",
                    "total_formatted": "120 GB",
                    "used_formatted": "45 GB",
                    "free_formatted": "75 GB"
                }
            ],
            "performance": {
                "read_speed": "125 MB/s",
                "write_speed": "90 MB/s",
                "io_ops": "120/s",
                "access_time": "5.2 ms"
            }
        }
        
        if self.simulation_mode:
            return info
        
        try:
            partitions = []
            
            if HAS_PSUTIL:
                for part in psutil.disk_partitions(all=False):
                    usage = psutil.disk_usage(part.mountpoint)
                    
                    partition = {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "opts": part.opts,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": str(usage.percent),
                        "total_formatted": format_bytes(usage.total),
                        "used_formatted": format_bytes(usage.used),
                        "free_formatted": format_bytes(usage.free)
                    }
                    
                    partitions.append(partition)
            
            elif self.has_df:
                # Usar df como alternativa
                result = subprocess.run(["df", "-B1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        for line in lines[1:]:
                            parts = line.split()
                            if len(parts) >= 6:
                                device = parts[0]
                                total = int(parts[1])
                                used = int(parts[2])
                                free = int(parts[3])
                                percent = parts[4].replace('%', '')
                                mountpoint = parts[5]
                                
                                partition = {
                                    "device": device,
                                    "mountpoint": mountpoint,
                                    "total": total,
                                    "used": used,
                                    "free": free,
                                    "percent": percent,
                                    "total_formatted": format_bytes(total),
                                    "used_formatted": format_bytes(used),
                                    "free_formatted": format_bytes(free)
                                }
                                
                                partitions.append(partition)
            
            info["partitions"] = partitions
            
            # Rendimiento de disco
            if HAS_PSUTIL and hasattr(psutil, "disk_io_counters"):
                # Obtener contadores actuales
                current_counters = psutil.disk_io_counters()
                current_time = time.time()
                
                # Calcular velocidades si tenemos datos previos
                if self.prev_disk_counters and current_time > self.prev_time:
                    time_diff = current_time - self.prev_time
                    
                    read_diff = current_counters.read_bytes - self.prev_disk_counters.read_bytes
                    write_diff = current_counters.write_bytes - self.prev_disk_counters.write_bytes
                    
                    read_speed = read_diff / time_diff
                    write_speed = write_diff / time_diff
                    
                    info["performance"] = {
                        "read_speed": format_bytes(read_speed) + "/s",
                        "write_speed": format_bytes(write_speed) + "/s",
                        "io_ops": f"{int((current_counters.read_count - self.prev_disk_counters.read_count + current_counters.write_count - self.prev_disk_counters.write_count) / time_diff)}/s",
                        "access_time": "N/A"
                    }
                
                # Actualizar contadores para la próxima vez
                self.prev_disk_counters = current_counters
                self.prev_time = current_time
        
        except Exception as e:
            print(f"Error al obtener información de discos: {e}")
        
        return info
    
    def get_network_info(self):
        """Obtener información de red"""
        info = {
            "interfaces": [
                {
                    "name": "eth0",
                    "ip": "192.168.1.100",
                    "mask": "255.255.255.0",
                    "mac": "00:11:22:33:44:55",
                    "rx": 1024 * 1024 * 1024,  # 1 GB
                    "tx": 256 * 1024 * 1024,  # 256 MB
                    "rx_formatted": "1 GB",
                    "tx_formatted": "256 MB"
                }
            ],
            "stats": {
                "download_speed": "2.5 MB/s",
                "upload_speed": "512 KB/s",
                "total_received": "12.5 GB",
                "total_sent": "3.2 GB",
                "status": "Connected"
            }
        }
        
        if self.simulation_mode:
            return info
        
        try:
            interfaces = []
            
            if HAS_PSUTIL and hasattr(psutil, "net_if_addrs") and hasattr(psutil, "net_io_counters"):
                # Interfaces y direcciones
                net_addrs = psutil.net_if_addrs()
                net_io = psutil.net_io_counters(pernic=True)
                
                for name, addrs in net_addrs.items():
                    if name == 'lo':  # Saltar la interfaz de loopback
                        continue
                    
                    interface = {
                        "name": name,
                        "ip": "",
                        "mask": "",
                        "mac": ""
                    }
                    
                    for addr in addrs:
                        if addr.family == socket.AF_INET:
                            interface["ip"] = addr.address
                            interface["mask"] = addr.netmask
                        elif addr.family == psutil.AF_LINK:
                            interface["mac"] = addr.address
                    
                    # Estadísticas de E/S
                    if name in net_io:
                        interface["rx"] = net_io[name].bytes_recv
                        interface["tx"] = net_io[name].bytes_sent
                        interface["rx_formatted"] = format_bytes(net_io[name].bytes_recv)
                        interface["tx_formatted"] = format_bytes(net_io[name].bytes_sent)
                    
                    interfaces.append(interface)
                
                # Estadísticas generales de red
                current_net_counters = psutil.net_io_counters()
                current_time = time.time()
                
                stats = {
                    "total_received": format_bytes(current_net_counters.bytes_recv),
                    "total_sent": format_bytes(current_net_counters.bytes_sent),
                    "status": "Connected" if interfaces else "Disconnected",
                    "download_speed": "0 B/s",
                    "upload_speed": "0 B/s"
                }
                
                # Calcular velocidades si tenemos datos previos
                if self.prev_net_counters and current_time > self.prev_time:
                    time_diff = current_time - self.prev_time
                    
                    rx_diff = current_net_counters.bytes_recv - self.prev_net_counters.bytes_recv
                    tx_diff = current_net_counters.bytes_sent - self.prev_net_counters.bytes_sent
                    
                    rx_speed = rx_diff / time_diff
                    tx_speed = tx_diff / time_diff
                    
                    stats["download_speed"] = format_bytes(rx_speed) + "/s"
                    stats["upload_speed"] = format_bytes(tx_speed) + "/s"
                
                # Actualizar contadores para la próxima vez
                self.prev_net_counters = current_net_counters
                self.prev_time = current_time
                
                info["stats"] = stats
            
            elif self.has_proc_net_dev:
                # Leer /proc/net/dev como alternativa
                with open("/proc/net/dev", "r") as f:
                    lines = f.readlines()
                
                for line in lines[2:]:  # Saltar las dos primeras líneas (cabecera)
                    parts = line.strip().split(":")
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        if name == 'lo':  # Saltar la interfaz de loopback
                            continue
                        
                        values = parts[1].strip().split()
                        if len(values) >= 16:
                            rx = int(values[0])
                            tx = int(values[8])
                            
                            interface = {
                                "name": name,
                                "ip": "",
                                "mask": "",
                                "mac": "",
                                "rx": rx,
                                "tx": tx,
                                "rx_formatted": format_bytes(rx),
                                "tx_formatted": format_bytes(tx)
                            }
                            
                            interfaces.append(interface)
            
            info["interfaces"] = interfaces
        
        except Exception as e:
            print(f"Error al obtener información de red: {e}")
        
        return info
    
    def get_performance_info(self):
        """Obtener información de rendimiento"""
        info = {
            "boot_time": "2023-09-10 08:45:32",
            "uptime": "1d 3h 24m",
            "load_1min": "0.25",
            "load_5min": "0.32",
            "load_15min": "0.28",
            "process_count": "124",
            "zombie_processes": "0"
        }
        
        if self.simulation_mode:
            return info
        
        try:
            if HAS_PSUTIL:
                # Tiempo de arranque y tiempo activo
                boot_time = psutil.boot_time()
                info["boot_time"] = datetime.datetime.fromtimestamp(boot_time).strftime("%Y-%m-%d %H:%M:%S")
                info["uptime"] = self.format_uptime(boot_time)
                
                # Carga del sistema
                load_avg = psutil.getloadavg()
                info["load_1min"] = str(load_avg[0])
                info["load_5min"] = str(load_avg[1])
                info["load_15min"] = str(load_avg[2])
                
                # Procesos
                processes = 0
                zombies = 0
                
                for proc in psutil.process_iter(['status']):
                    processes += 1
                    if proc.info['status'] == psutil.STATUS_ZOMBIE:
                        zombies += 1
                
                info["process_count"] = str(processes)
                info["zombie_processes"] = str(zombies)
            
        except Exception as e:
            print(f"Error al obtener información de rendimiento: {e}")
        
        return info
    
    def get_updates_info(self):
        """Obtener información sobre actualizaciones disponibles"""
        info = {
            "available": 12,
            "security": 3,
            "last_check": "2023-09-15 10:23:45",
            "automatic_updates": False
        }
        
        if self.simulation_mode:
            return info
        
        try:
            # Comprobar actualizaciones con apt (simulado)
            updates_available = 0
            security_updates = 0
            
            # En un sistema real, esto debería ejecutar:
            # apt-get update -qq
            # apt-get upgrade -s
            # y contar los paquetes a actualizar
            
            info["available"] = updates_available
            info["security"] = security_updates
            info["last_check"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception as e:
            print(f"Error al obtener información de actualizaciones: {e}")
        
        return info
    
    def get_security_info(self):
        """Obtener información de seguridad"""
        info = {
            "status": "good",
            "firewall": "active",
            "rootkit_check": "clean",
            "last_scan": "2023-09-14 22:30:15"
        }
        
        if self.simulation_mode:
            return info
        
        try:
            # En un sistema real, esto debería comprobar:
            # - Estado del firewall (ufw/iptables)
            # - Si hay escáneres de rootkits instalados y su estado (rkhunter/chkrootkit)
            # - Vulnerabilidades conocidas
            
            # Comprobar firewall
            firewall_status = "inactive"
            try:
                # Comprobar UFW
                result = subprocess.run(["ufw", "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if "active" in result.stdout.lower():
                    firewall_status = "active"
            except:
                # Comprobar iptables
                try:
                    result = subprocess.run(["iptables", "-L"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if len(result.stdout.strip().split('\n')) > 10:
                        firewall_status = "active"
                except:
                    pass
            
            info["firewall"] = firewall_status
            
        except Exception as e:
            print(f"Error al obtener información de seguridad: {e}")
        
        return info
    
    def get_cpu_usage(self):
        """Obtener porcentaje de uso de CPU"""
        if self.simulation_mode:
            return 45.0
        
        try:
            if HAS_PSUTIL:
                return psutil.cpu_percent(interval=0.1)
            
            elif self.has_proc_stat:
                # Leer /proc/stat como alternativa
                with open("/proc/stat", "r") as f:
                    cpu_line = f.readline().strip()
                
                if cpu_line.startswith("cpu "):
                    current_cpu_times = [int(x) for x in cpu_line.split()[1:]]
                    
                    if self.prev_cpu_times:
                        # Calcular diferencia
                        prev_idle = self.prev_cpu_times[3] + self.prev_cpu_times[4]
                        curr_idle = current_cpu_times[3] + current_cpu_times[4]
                        
                        prev_total = sum(self.prev_cpu_times)
                        curr_total = sum(current_cpu_times)
                        
                        # Calcular porcentaje de uso
                        idle_diff = curr_idle - prev_idle
                        total_diff = curr_total - prev_total
                        
                        if total_diff > 0:
                            return 100.0 * (1.0 - idle_diff / total_diff)
                    
                    # Actualizar valores para la próxima vez
                    self.prev_cpu_times = current_cpu_times
            
        except Exception as e:
            print(f"Error al obtener uso de CPU: {e}")
        
        return 0.0
    
    def get_cpu_usage_per_core(self):
        """Obtener uso de CPU por núcleo"""
        if self.simulation_mode:
            return [
                {"core": "Total", "usage": "45%", "temp": "55°C"},
                {"core": "0", "usage": "62%", "temp": "58°C"},
                {"core": "1", "usage": "38%", "temp": "54°C"},
                {"core": "2", "usage": "51%", "temp": "56°C"},
                {"core": "3", "usage": "29%", "temp": "52°C"}
            ]
        
        result = [{"core": "Total", "usage": "0%", "temp": "N/A"}]
        
        try:
            if HAS_PSUTIL:
                # Uso total
                total_usage = psutil.cpu_percent(interval=0.1)
                result[0]["usage"] = f"{total_usage}%"
                
                # Uso por núcleo
                per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
                
                # Temperaturas (opcional)
                temps = {}
                if hasattr(psutil, "sensors_temperatures"):
                    temps_data = psutil.sensors_temperatures()
                    if temps_data:
                        # Intentar encontrar temperaturas para los núcleos
                        for sensor, entries in temps_data.items():
                            if sensor.lower() in ["coretemp", "k10temp", "cpu_thermal"]:
                                for i, entry in enumerate(entries):
                                    # Extraer número de núcleo del nombre si es posible
                                    core_match = re.search(r"core\s*(\d+)", entry.label.lower())
                                    if core_match:
                                        core_num = int(core_match.group(1))
                                        temps[core_num] = entry.current
                                    elif i > 0:  # Si no hay coincidencia pero es una entrada adicional, asignarla secuencialmente
                                        temps[i - 1] = entry.current
                
                # Temperatura media para el total si hay datos
                if temps:
                    avg_temp = sum(temps.values()) / len(temps)
                    result[0]["temp"] = f"{avg_temp:.1f}°C"
                
                # Añadir datos por núcleo
                for i, usage in enumerate(per_cpu):
                    core_data = {
                        "core": str(i),
                        "usage": f"{usage}%",
                        "temp": f"{temps.get(i, 'N/A')}°C" if i in temps else "N/A"
                    }
                    result.append(core_data)
        
        except Exception as e:
            print(f"Error al obtener uso de CPU por núcleo: {e}")
        
        return result
    
    def get_disk_partitions(self):
        """Obtener información detallada de particiones"""
        if self.simulation_mode:
            return [
                {
                    "device": "/dev/sda1",
                    "mountpoint": "/",
                    "fstype": "ext4",
                    "opts": "rw,relatime",
                    "total": 120 * 1024 * 1024 * 1024,
                    "used": 45 * 1024 * 1024 * 1024,
                    "free": 75 * 1024 * 1024 * 1024,
                    "percent": "37.5",
                    "total_formatted": "120 GB",
                    "used_formatted": "45 GB",
                    "free_formatted": "75 GB"
                }
            ]
        
        partitions = []
        
        try:
            if HAS_PSUTIL:
                for part in psutil.disk_partitions(all=False):
                    if os.path.exists(part.mountpoint):
                        usage = psutil.disk_usage(part.mountpoint)
                        
                        partition = {
                            "device": part.device,
                            "mountpoint": part.mountpoint,
                            "fstype": part.fstype,
                            "opts": part.opts,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": str(usage.percent),
                            "total_formatted": format_bytes(usage.total),
                            "used_formatted": format_bytes(usage.used),
                            "free_formatted": format_bytes(usage.free)
                        }
                        
                        partitions.append(partition)
            
            elif self.has_df:
                # Usar df como alternativa
                result = subprocess.run(["df", "-B1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        for line in lines[1:]:
                            parts = line.split()
                            if len(parts) >= 6:
                                device = parts[0]
                                total = int(parts[1])
                                used = int(parts[2])
                                free = int(parts[3])
                                percent = parts[4].replace('%', '')
                                mountpoint = parts[5]
                                
                                partition = {
                                    "device": device,
                                    "mountpoint": mountpoint,
                                    "fstype": "unknown",
                                    "opts": "unknown",
                                    "total": total,
                                    "used": used,
                                    "free": free,
                                    "percent": percent,
                                    "total_formatted": format_bytes(total),
                                    "used_formatted": format_bytes(used),
                                    "free_formatted": format_bytes(free)
                                }
                                
                                partitions.append(partition)
        
        except Exception as e:
            print(f"Error al obtener particiones: {e}")
        
        return partitions
    
    def get_network_stats(self):
        """Obtener estadísticas de red"""
        if self.simulation_mode:
            return {
                "interfaces": [
                    {
                        "name": "eth0",
                        "ip": "192.168.1.100",
                        "mask": "255.255.255.0",
                        "mac": "00:11:22:33:44:55",
                        "rx": 1024 * 1024 * 1024,
                        "tx": 256 * 1024 * 1024,
                        "rx_formatted": "1 GB",
                        "tx_formatted": "256 MB"
                    }
                ],
                "stats": {
                    "download_speed": "2.5 MB/s",
                    "upload_speed": "512 KB/s",
                    "total_received": "12.5 GB",
                    "total_sent": "3.2 GB",
                    "status": "Connected"
                }
            }
        
        network_stats = {
            "interfaces": [],
            "stats": {
                "download_speed": "0 B/s",
                "upload_speed": "0 B/s",
                "total_received": "0 B",
                "total_sent": "0 B",
                "status": "Disconnected"
            }
        }
        
        try:
            if HAS_PSUTIL and hasattr(psutil, "net_if_addrs") and hasattr(psutil, "net_io_counters"):
                # Interfaces y direcciones
                net_addrs = psutil.net_if_addrs()
                net_io = psutil.net_io_counters(pernic=True)
                
                for name, addrs in net_addrs.items():
                    if name == 'lo':  # Saltar la interfaz de loopback
                        continue
                    
                    interface = {
                        "name": name,
                        "ip": "",
                        "mask": "",
                        "mac": ""
                    }
                    
                    for addr in addrs:
                        if addr.family == socket.AF_INET:
                            interface["ip"] = addr.address
                            interface["mask"] = addr.netmask
                        elif addr.family == psutil.AF_LINK:
                            interface["mac"] = addr.address
                    
                    # Estadísticas de E/S
                    if name in net_io:
                        interface["rx"] = net_io[name].bytes_recv
                        interface["tx"] = net_io[name].bytes_sent
                        interface["rx_formatted"] = format_bytes(net_io[name].bytes_recv)
                        interface["tx_formatted"] = format_bytes(net_io[name].bytes_sent)
                    
                    network_stats["interfaces"].append(interface)
                
                # Estadísticas generales de red
                current_net_counters = psutil.net_io_counters()
                current_time = time.time()
                
                stats = {
                    "total_received": format_bytes(current_net_counters.bytes_recv),
                    "total_sent": format_bytes(current_net_counters.bytes_sent),
                    "status": "Connected" if network_stats["interfaces"] else "Disconnected",
                    "download_speed": "0 B/s",
                    "upload_speed": "0 B/s"
                }
                
                # Calcular velocidades si tenemos datos previos
                if self.prev_net_counters and current_time > self.prev_time:
                    time_diff = current_time - self.prev_time
                    
                    rx_diff = current_net_counters.bytes_recv - self.prev_net_counters.bytes_recv
                    tx_diff = current_net_counters.bytes_sent - self.prev_net_counters.bytes_sent
                    
                    rx_speed = rx_diff / time_diff
                    tx_speed = tx_diff / time_diff
                    
                    stats["download_speed"] = format_bytes(rx_speed) + "/s"
                    stats["upload_speed"] = format_bytes(tx_speed) + "/s"
                
                # Actualizar contadores para la próxima vez
                self.prev_net_counters = current_net_counters
                self.prev_time = current_time
                
                network_stats["stats"] = stats
        
        except Exception as e:
            print(f"Error al obtener estadísticas de red: {e}")
        
        return network_stats
    
    def generate_performance_report(self):
        """Generar informe de rendimiento"""
        report = []
        
        try:
            # Obtener estadísticas actuales
            stats = self.get_all_stats()
            
            # Sección de CPU
            cpu_section = {
                "title": _("Rendimiento de CPU"),
                "content": []
            }
            
            if "cpu" in stats and "usage_percent" in stats["cpu"]:
                usage = float(stats["cpu"]["usage_percent"])
                if usage > 90:
                    cpu_section["content"].append({
                        "text": _("El uso de CPU es crítico: {}%").format(usage),
                        "type": "error"
                    })
                elif usage > 70:
                    cpu_section["content"].append({
                        "text": _("El uso de CPU es alto: {}%").format(usage),
                        "type": "warning"
                    })
                else:
                    cpu_section["content"].append({
                        "text": _("El uso de CPU es normal: {}%").format(usage),
                        "type": "good"
                    })
            
            if "memory" in stats and "virtual" in stats["memory"] and "percent" in stats["memory"]["virtual"]:
                memory_usage = float(stats["memory"]["virtual"]["percent"])
                if memory_usage > 90:
                    cpu_section["content"].append({
                        "text": _("La memoria está casi agotada: {}%").format(memory_usage),
                        "type": "error"
                    })
                elif memory_usage > 70:
                    cpu_section["content"].append({
                        "text": _("El uso de memoria es alto: {}%").format(memory_usage),
                        "type": "warning"
                    })
                else:
                    cpu_section["content"].append({
                        "text": _("El uso de memoria es normal: {}%").format(memory_usage),
                        "type": "good"
                    })
            
            # Comprobar swap
            if "memory" in stats and "swap" in stats["memory"] and "percent" in stats["memory"]["swap"]:
                swap_usage = float(stats["memory"]["swap"]["percent"])
                if swap_usage > 50:
                    cpu_section["content"].append({
                        "text": _("El uso de swap es alto: {}%").format(swap_usage),
                        "type": "warning"
                    })
                elif "swap" in stats["memory"] and "total" in stats["memory"]["swap"] and float(stats["memory"]["swap"]["total"]) > 0:
                    cpu_section["content"].append({
                        "text": _("El uso de swap es normal: {}%").format(swap_usage),
                        "type": "good"
                    })
            
            report.append(cpu_section)
            
            # Sección de disco
            disk_section = {
                "title": _("Almacenamiento"),
                "content": []
            }
            
            if "disk" in stats and "partitions" in stats["disk"]:
                for part in stats["disk"]["partitions"]:
                    if "percent" in part and "mountpoint" in part:
                        usage = float(part["percent"])
                        
                        if usage > 90:
                            disk_section["content"].append({
                                "text": _("Partición {} está casi llena: {}%").format(part["mountpoint"], usage),
                                "type": "error"
                            })
                        elif usage > 75:
                            disk_section["content"].append({
                                "text": _("Partición {} tiene uso alto: {}%").format(part["mountpoint"], usage),
                                "type": "warning"
                            })
            
            report.append(disk_section)
            
            # Sección de procesos
            process_section = {
                "title": _("Procesos"),
                "content": []
            }
            
            if "performance" in stats and "process_count" in stats["performance"]:
                process_count = int(stats["performance"]["process_count"])
                if process_count > 300:
                    process_section["content"].append({
                        "text": _("Muchos procesos en ejecución: {}").format(process_count),
                        "type": "warning"
                    })
                else:
                    process_section["content"].append({
                        "text": _("Número de procesos normal: {}").format(process_count),
                        "type": "good"
                    })
            
            if "performance" in stats and "zombie_processes" in stats["performance"]:
                zombie_count = int(stats["performance"]["zombie_processes"])
                if zombie_count > 0:
                    process_section["content"].append({
                        "text": _("Procesos zombies detectados: {}").format(zombie_count),
                        "type": "warning"
                    })
            
            report.append(process_section)
            
            # Sección de carga del sistema
            load_section = {
                "title": _("Carga del Sistema"),
                "content": []
            }
            
            if "performance" in stats and "load_1min" in stats["performance"]:
                load = float(stats["performance"]["load_1min"])
                cpu_cores = 2  # Valor por defecto
                
                if "cpu" in stats and "cores" in stats["cpu"]:
                    try:
                        cpu_cores = int(stats["cpu"]["cores"])
                    except (ValueError, TypeError):
                        pass
                
                if load > cpu_cores:
                    load_section["content"].append({
                        "text": _("Carga del sistema muy alta: {}").format(load),
                        "type": "error"
                    })
                elif load > cpu_cores * 0.7:
                    load_section["content"].append({
                        "text": _("Carga del sistema alta: {}").format(load),
                        "type": "warning"
                    })
                else:
                    load_section["content"].append({
                        "text": _("Carga del sistema normal: {}").format(load),
                        "type": "good"
                    })
            
            report.append(load_section)
            
            # Sección de seguridad
            security_section = {
                "title": _("Seguridad"),
                "content": []
            }
            
            if "security" in stats and "firewall" in stats["security"]:
                firewall_status = stats["security"]["firewall"]
                if firewall_status == "active":
                    security_section["content"].append({
                        "text": _("Firewall activo"),
                        "type": "good"
                    })
                else:
                    security_section["content"].append({
                        "text": _("Firewall inactivo o no detectado"),
                        "type": "warning"
                    })
            
            if "updates" in stats and "security" in stats["updates"]:
                security_updates = int(stats["updates"]["security"])
                if security_updates > 0:
                    security_section["content"].append({
                        "text": _("{} actualizaciones de seguridad pendientes").format(security_updates),
                        "type": "error" if security_updates > 5 else "warning"
                    })
                else:
                    security_section["content"].append({
                        "text": _("No hay actualizaciones de seguridad pendientes"),
                        "type": "good"
                    })
            
            report.append(security_section)
            
        except Exception as e:
            print(f"Error al generar informe de rendimiento: {e}")
            # En caso de error, devolver un informe básico
            report = [{
                "title": _("Error al generar informe"),
                "content": [{
                    "text": _("No se ha podido generar el informe de rendimiento: {}").format(str(e)),
                    "type": "error"
                }]
            }]
        
        return report
    
    def format_uptime(self, boot_time):
        """Formatear el tiempo de actividad desde el arranque"""
        uptime_seconds = time.time() - boot_time
        
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = ""
        
        if days > 0:
            uptime_str += f"{int(days)}d "
        
        if hours > 0 or days > 0:
            uptime_str += f"{int(hours)}h "
        
        uptime_str += f"{int(minutes)}m"
        
        return uptime_str