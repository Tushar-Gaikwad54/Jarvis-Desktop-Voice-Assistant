"""
System and Hardware Inspection Tools for J.A.R.V.I.S.
"""

import os
import platform
import shutil
import subprocess
import sys
from typing import Any, Dict
from jarvis.core.permissions import RiskLevel
from jarvis.tools.base import BaseTool


class GetSystemInfoTool(BaseTool):
    name = "get_system_info"
    description = (
        "Retrieves Windows PC hardware and system specifications (CPU, RAM, disk space, OS build). "
        "Use ONLY when the user explicitly asks to check system specs, computer hardware, RAM, CPU, or disk space."
    )
    risk_level = RiskLevel.LOW

    def execute(self, metric: str = "all") -> Dict[str, Any]:
        try:
            # Basic OS / Hardware
            os_name = platform.system()
            os_release = platform.release()
            os_version = platform.version()
            if os.name == "nt":
                ver = sys.getwindowsversion()
                if ver.build >= 22000:
                    os_display = f"Windows 11 (Build {ver.build})"
                else:
                    os_display = f"Windows {os_release} (Build {os_version})"
            else:
                os_display = f"{os_name} {os_release} (Build {os_version})"

            arch = platform.machine()
            processor = platform.processor()
            cpu_count = os.cpu_count() or 4

            # Memory via ctypes GlobalMemoryStatusEx (most reliable on modern Windows)
            ram_info = "Unknown"
            if os.name == "nt":
                try:
                    import ctypes
                    class MEMORYSTATUSEX(ctypes.Structure):
                        _fields_ = [
                            ('dwLength', ctypes.c_ulong),
                            ('dwMemoryLoad', ctypes.c_ulong),
                            ('ullTotalPhys', ctypes.c_ulonglong),
                            ('ullAvailPhys', ctypes.c_ulonglong),
                            ('ullTotalPageFile', ctypes.c_ulonglong),
                            ('ullAvailPageFile', ctypes.c_ulonglong),
                            ('ullTotalVirtual', ctypes.c_ulonglong),
                            ('ullAvailVirtual', ctypes.c_ulonglong),
                            ('sullAvailExtendedVirtual', ctypes.c_ulonglong)
                        ]
                    ms = MEMORYSTATUSEX()
                    ms.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
                        gb_val = ms.ullTotalPhys / (1024 ** 3)
                        ram_info = f"{round(gb_val)} GB"
                except Exception:
                    pass

            if ram_info == "Unknown" and os.name == "nt":
                try:
                    creationflags = 0x08000000
                    p = subprocess.run(
                        ["wmic", "computersystem", "get", "TotalPhysicalMemory"],
                        capture_output=True,
                        text=True,
                        timeout=3,
                        creationflags=creationflags,
                    )
                    lines = [line.strip() for line in p.stdout.splitlines() if line.strip() and not line.strip().lower().startswith("total")]
                    if lines and lines[0].isdigit():
                        bytes_ram = int(lines[0])
                        ram_info = f"{round(bytes_ram / (1024 ** 3))} GB"
                except Exception:
                    pass

            # Disk
            total, used, free = shutil.disk_usage(".")
            disk_free_gb = f"{free / (1024 ** 3):.2f}"
            disk_total_gb = f"{total / (1024 ** 3):.2f}"

            data = {
                "os": os_display,
                "architecture": arch,
                "processor": processor,
                "cpu_cores": cpu_count,
                "ram": ram_info,
                "disk_free_gb": disk_free_gb,
                "disk_total_gb": disk_total_gb,
                "python_version": platform.python_version(),
                "current_working_directory": os.getcwd(),
            }

            output_lines = [
                f"* Operating System: {data['os']}",
                f"* Architecture:     {data['architecture']}",
                f"* CPU Cores:        {data['cpu_cores']} ({data['processor']})",
                f"* RAM Installed:    {data['ram']}",
                f"* Disk (Current):   {disk_free_gb} GB free of {disk_total_gb} GB",
                f"* Python Runtime:   {data['python_version']}",
                f"* Working Dir:      {data['current_working_directory']}",
            ]

            return {
                "success": True,
                "data": data,
                "output": "\n".join(output_lines),
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to query system info: {str(e)}"}

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Target hardware metric to inspect ('all', 'ram', 'cpu', 'disk', 'specs').",
                    "default": "all",
                }
            },
        }
