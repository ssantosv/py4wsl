import subprocess
import os
import shlex
import threading
from ctypes import wintypes, POINTER, c_char_p
from enum import IntFlag
import ctypes
import winreg
import shutil


# ==================================================
# Estructuras para la API de Windows
# ==================================================
class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", ctypes.c_void_p),
        ("bInheritHandle", wintypes.BOOL)
    ]

class OVERLAPPED(ctypes.Structure):
    _fields_ = [
        ("Internal", ctypes.c_ulonglong),
        ("InternalHigh", ctypes.c_ulonglong),
        ("Offset", wintypes.DWORD),
        ("OffsetHigh", wintypes.DWORD),
        ("hEvent", wintypes.HANDLE)
    ]

class WSL_DISTRIBUTION_FLAGS(IntFlag):  # Usar IntFlag del módulo enum
    NONE = 0x0
    ENABLE_INTEROP = 0x1
    APPEND_NT_PATH = 0x2
    ENABLE_DRIVE_MOUNTING = 0x4


class WSL:
    
    def __init__(self, distro='Ubuntu'):
        self.distro = distro
        self._setup_ctypes()
        self.ole32 = ctypes.WinDLL('ole32')

        self.wslapi.WslRegisterDistribution.argtypes = [
            ctypes.c_wchar_p,  # distributionName
            ctypes.c_wchar_p   # tarGzFilename
        ]
        self.wslapi.WslRegisterDistribution.restype = ctypes.c_long
        
        self.wslapi.WslUnregisterDistribution.argtypes = [
            ctypes.c_wchar_p  # distributionName
        ]
        self.wslapi.WslUnregisterDistribution.restype = ctypes.c_long
        
        self.wslapi.WslIsDistributionRegistered.argtypes = [
            ctypes.c_wchar_p  # distributionName
        ]
        self.wslapi.WslIsDistributionRegistered.restype = wintypes.BOOL

    def _setup_ctypes(self):
        # Configuraciones existentes...
        
        # Nueva configuración para WslConfigureDistribution
        self.wslapi.WslConfigureDistribution.argtypes = [
            ctypes.c_wchar_p,          # distributionName
            ctypes.c_ulong,            # defaultUID
            ctypes.c_ulong             # wslDistributionFlags (como DWORD)
        ]
        self.wslapi.WslConfigureDistribution.restype = ctypes.c_long

        # Configuración para WslGetDistributionConfiguration
        self.wslapi.WslGetDistributionConfiguration.argtypes = [
            ctypes.c_wchar_p,          # distributionName
            POINTER(ctypes.c_ulong),   # distributionVersion
            POINTER(ctypes.c_ulong),   # defaultUID
            POINTER(ctypes.c_ulong),   # wslDistributionFlags
            POINTER(POINTER(c_char_p)),# defaultEnvironmentVariables
            POINTER(ctypes.c_ulong)    # defaultEnvironmentVariableCount
        ]
        self.wslapi.WslGetDistributionConfiguration.restype = ctypes.c_long
    def get_distribution_configuration(self):
        config = {
            #'name': None,
            'version': None,
            'default_uid': None,
            'flags': None,
            'env_vars': {}
        }

        
        version = ctypes.c_ulong()
        uid = ctypes.c_ulong()
        flags = ctypes.c_ulong()
        env_vars = ctypes.POINTER(ctypes.c_wchar_p)()
        env_count = ctypes.c_ulong()

        hr = self.wslapi.WslGetDistributionConfiguration(
            self.distro,
            
            ctypes.byref(version),
            ctypes.byref(uid),
            ctypes.byref(flags),
            ctypes.byref(env_vars),
            ctypes.byref(env_count)
        )

        if hr == 0:
            config['version'] = version.value
            config['default_uid'] = uid.value
            config['flags'] = flags.value  
            if config['flags'] & 0x1: 
                print("ENABLE_INTEROP")
            if config['flags'] & 0x2:
                print("APPEND_NT_PATH")
            if config['flags'] & 0x4:
                print("ENABLE_DRIVE_MOUNTING")
            if config['flags'] == 0:
                print("NONE")
            
            # Manejar variables de entorno de forma segura
            for i in range(env_count.value):
                var = env_vars[i]
                if var:
                    key_value = var.split('=', 1)
                    if len(key_value) == 2:
                        config['env_vars'][key_value[0]] = key_value[1]
            # Solo libera el array principal, no cada cadena individual
            ctypes.windll.ole32.CoTaskMemFree(env_vars)


        return config if hr == 0 else None

    def get_wsl_distro_info_by_name(self):
        """
        Returns a dictionary with the requested data for the WSL distribution whose name matches distro_name.
        If not found, returns None.
        """
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Lxss"
        fields = ["BasePath", "Flavor", "PackageFamilyName", "Version", "osVersion"]
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as lxss_key:
                i = 0
                while True:
                    try:
                        guid = winreg.EnumKey(lxss_key, i)
                        with winreg.OpenKey(lxss_key, guid) as distro_key:
                            try:
                                name = winreg.QueryValueEx(distro_key, "DistributionName")[0]
                            except FileNotFoundError:
                                name = None
                            if isinstance(name, str) and name.lower() == self.distro.lower():
                                result = {
                                    "BasePath": None,
                                    "Flavor": None,
                                    "GUID": guid,
                                    "osVersion": None,
                                    "PackageFamilyName": None
                                }
                                for field in fields:
                                    try:
                                        value = winreg.QueryValueEx(distro_key, field)[0]
                                        if field.lower() in ("version", "osversion"):
                                            result["osVersion"] = value
                                        else:
                                            result[field] = value
                                    except FileNotFoundError:
                                        continue
                                return result
                        i += 1
                    except OSError:
                        break
        except Exception as e:
            print(f"Error accediendo al registro: {e}")
        return None


    def configure_distribution(self, 
                             default_uid: int = None, 
                             flags: WSL_DISTRIBUTION_FLAGS = None):
        """
        
        Configure the WSL distribution parameters


        Args:
            default_uid (int): Default user UID
            flags (WSL_DISTRIBUTION_FLAGS): Configuration flags
        
        """
        current_config = self.get_distribution_configuration()
        
        # Mantener valores actuales si no se especifican
        final_uid = default_uid if default_uid is not None else current_config['default_uid']
        final_flags = flags if flags is not None else current_config['flags']

        hr = self.wslapi.WslConfigureDistribution(
            self.distro,
            final_uid,
            final_flags.value if isinstance(final_flags, WSL_DISTRIBUTION_FLAGS) else final_flags
        )
        
        return hr == 0

    def set_distribution_flag(self, flag: WSL_DISTRIBUTION_FLAGS, enable: bool):
        """"Modify a specific flag while keeping the others unchanged"""
        config = self.get_distribution_configuration()
        if not config:
            return False
            
        current_flags = config['flags']
        
        if enable:
            new_flags = current_flags | flag
        else:
            new_flags = current_flags & ~flag
            
        return self.configure_distribution(flags=new_flags)

    def register_distribution(self, distribution_name: str, tar_gz_path: str) -> bool:
        """
       Register a new WSL distribution.

        Args:
        distribution_name: Unique name of the distribution (e.g., "MyDistro")
        tar_gz_path: Full path to the .tar.gz file containing the filesystem

        Returns:
        bool: True if registration was successful, False if it faileda
        """
        hr = self.wslapi.WslRegisterDistribution(distribution_name, tar_gz_path)
        return hr == 0  # S_OK = 0

    def unregister_distribution(self, distribution_name: str) -> bool:
        """
        Unregister a WSL distribution.

        Args:
            distribution_name: Name of the distribution to remove
        Returns:
            bool: True if the operation was successful
        """
        hr = self.wslapi.WslUnregisterDistribution(distribution_name)
        return hr == 0  # S_OK = 0

    def is_distribution_registered(self, distribution_name: str) -> bool:
        """
        Checks if a distribution is registered.

        Args:
        distribution_name: Name of the distribution to check

        Returns:
        bool: True if the distribution is registered
        """
        return bool(self.wslapi.WslIsDistributionRegistered(distribution_name))
    
    def _setup_ctypes(self):
        self.wslapi = ctypes.WinDLL("wslapi.dll")
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        # Configurar WslLaunch
        self.wslapi.WslLaunch.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            wintypes.BOOL,
            wintypes.HANDLE,
            wintypes.HANDLE,
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.HANDLE)
        ]
        self.wslapi.WslLaunch.restype = ctypes.c_long

        # Configurar funciones de kernel32
        self._configure_kernel32_functions()

    def launch_interactive(self, command: str = None, use_current_working_directory: bool = True) -> dict:
        """
        Ejecuta un comando interactivo usando WslLaunchInteractive.
        
            Args:
                command (str, optional): Command to execute. If None, launches the default shell.
                use_current_working_directory (bool): Use the current working directory of the calling process.

            Returns:
                dict: {
                "hr": HRESULT,
                "exit_code": int (only if hr == 0)
                }
        """
        exit_code = wintypes.DWORD()
        
        hr = self.wslapi.WslLaunchInteractive(
            self.distro,
            command,
            use_current_working_directory,
            ctypes.byref(exit_code)
        )
        
        return {
            "hr": hr,
            "exit_code": exit_code.value if hr == 0 else None
        }
    
    def _configure_kernel32_functions(self):
        """Configura las funciones de la API de Windows"""
        self.kernel32.CreatePipe.argtypes = [
            ctypes.POINTER(wintypes.HANDLE),
            ctypes.POINTER(wintypes.HANDLE),
            ctypes.POINTER(SECURITY_ATTRIBUTES),
            wintypes.DWORD
        ]
        self.kernel32.CreatePipe.restype = wintypes.BOOL

        self.kernel32.ReadFile.argtypes = [
            wintypes.HANDLE,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(OVERLAPPED)
        ]
        self.kernel32.ReadFile.restype = wintypes.BOOL

        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL

        self.kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel32.WaitForSingleObject.restype = wintypes.DWORD

        self.kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self.kernel32.GetExitCodeProcess.restype = wintypes.BOOL


    def _create_pipe(self):
        """Create an anonymous pipe with handle inheritance"""
        sa = SECURITY_ATTRIBUTES()
        sa.nLength = ctypes.sizeof(SECURITY_ATTRIBUTES)
        sa.lpSecurityDescriptor = None
        sa.bInheritHandle = True

        read_handle = wintypes.HANDLE()
        write_handle = wintypes.HANDLE()

        if not self.kernel32.CreatePipe(
            ctypes.byref(read_handle),
            ctypes.byref(write_handle),
            ctypes.byref(sa),
            0
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        
        return read_handle, write_handle

    def _read_pipe_async(self, handle):
        """Read data from a pipe asynchronously."""
        buffer = ctypes.create_string_buffer(4096)
        bytes_read = wintypes.DWORD()
        overlapped = OVERLAPPED()
        output = b""

        while True:
            success = self.kernel32.ReadFile(
                handle,
                buffer,
                ctypes.sizeof(buffer),
                ctypes.byref(bytes_read),
                ctypes.byref(overlapped)
            )
            
            if not success and ctypes.get_last_error() != 997:  # ERROR_IO_PENDING
                break
                
            self.kernel32.GetOverlappedResult(handle, ctypes.byref(overlapped), ctypes.byref(bytes_read), True)
            if bytes_read.value == 0:
                break
                
            output += buffer[:bytes_read.value]
        
        return output

    def _launch_process(self, command):
        """Execute a command using the native API with timeout handling."""
        stdout_read, stdout_write = self._create_pipe()
        stderr_read, stderr_write = self._create_pipe()
        process_handle = wintypes.HANDLE()

        try:
            # Lanzar proceso
            hr = self.wslapi.WslLaunch(
                self.distro,
                command,
                True,
                wintypes.HANDLE(0),
                stdout_write,
                stderr_write,
                ctypes.byref(process_handle)
            )

            if hr != 0:
                return {"hr": hr, "stdout": b"", "stderr": b"", "exit_code": 1}

            # Cerrar extremos de escritura
            self.kernel32.CloseHandle(stdout_write)
            self.kernel32.CloseHandle(stderr_write)

            # Leer salida en hilos separados
            stdout_buffer = []
            stderr_buffer = []
            
            stdout_thread = threading.Thread(
                target=lambda: stdout_buffer.append(self._read_pipe_async(stdout_read))
            )
            stderr_thread = threading.Thread(
                target=lambda: stderr_buffer.append(self._read_pipe_async(stderr_read))
            )
            
            stdout_thread.start()
            stderr_thread.start()

            # Esperar proceso con timeout
            exit_code = self._wait_for_process(process_handle)
            
            # Esperar hilos
            stdout_thread.join()
            stderr_thread.join()

            return {
                "hr": 0,
                "stdout": stdout_buffer[0] if stdout_buffer else b"",
                "stderr": stderr_buffer[0] if stderr_buffer else b"",
                "exit_code": exit_code
            }

        finally:
            # Limpieza de handles
            handles = [stdout_read, stderr_read, process_handle]
            for handle in handles:
                if handle:
                    self.kernel32.CloseHandle(handle)

    def _wait_for_process(self, process_handle, timeout=30000):
        """Wait for the process to finish with a maximum timeout."""
        result = self.kernel32.WaitForSingleObject(process_handle, timeout)
        
        if result == 0x00000000:  # WAIT_OBJECT_0
            exit_code = wintypes.DWORD()
            self.kernel32.GetExitCodeProcess(process_handle, ctypes.byref(exit_code))
            return exit_code.value
        elif result == 0x00000102:  # WAIT_TIMEOUT
            self.kernel32.TerminateProcess(process_handle, 1)
            return -1
        else:
            return -2

    # ==============================================
    # Métodos públicos
    # ==============================================
    def launch(self, command: str, capture_output: bool = True) -> dict:
        """Execute a command using the native api"""
        result = self._launch_process(command)
        return {
            "stdout": result["stdout"].decode("utf-8", errors="replace") if capture_output else "",
            "stderr": result["stderr"].decode("utf-8", errors="replace") if capture_output else "",
            "exit_code": result["exit_code"]
        }
    def run_command(self, command, capture_output=True, shell=False,input=None):
        """Execute a command using subprocess"""
        base_cmd = ['wsl.exe', '-d', self.distro]
        
        try:
            if shell:
                full_cmd = base_cmd + ['/bin/bash', '-c', command]
                args = ' '.join(full_cmd)
                print(full_cmd)
            else:
                args = base_cmd + shlex.split(command)
                print(command)

            result = subprocess.run(
                args,
                input=input,
                capture_output=capture_output,
                text=True,
                check=True,
                shell=False
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "stdout": e.stdout,
                "stderr": e.stderr,
                "exit_code": e.returncode
            }
    # ========================
    # Funciones de administración
    # ========================
    
    def parse_wsl_conf(self):
        raw_content = self.read_wsl_conf()
        if isinstance(raw_content, dict):
            # Ya está parseado, simplemente retorna
            return raw_content
        # Si es string, entonces lo analizas línea a línea
        config = {
            'automount': {},
            'network': {},
            'interop': {},
            'user': {},
            'boot': {},
            'useWindowsTimezone':{},
            'systemd': {}
        }
        current_section = None
        for line in raw_content.split('\n'):
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].lower()
                continue
            if '=' in line and current_section:
                key, value = line.split('=', 1)
                key = key.strip().lower()
                value = value.strip()
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                if current_section in config:
                    config[current_section][key] = value
        return config
    
    def install_package(self, package, password):
        """Install a package using sudo"""
        return self.run_command(
            f"sudo -S apt-get install -y {package}",
            input=f"{password}\n",
            shell=False
        )


    def is_interop_enabled(self):
        """Returns True if interoperatibility is enabled"""
        conf = self.parse_wsl_conf()
        return conf.get('interop', {}).get('enabled', True)  

    def is_systemd_enabled(self):
        """Returns True if systemd is enabled"""
        conf = self.parse_wsl_conf()
        return conf.get('systemd', {}).get('enabled', True)  
    
    def is_useWindowsTimezone_enabled(self):
        """Returns True if useWindowsTimezone is enabled"""
        conf = self.parse_wsl_conf()
        return conf.get('useWindowsTimezone', {}).get('enabled', True)  

    def get_network_config(self):
        """Returns network configuration in dict format"""
        conf = self.parse_wsl_conf()
        return {
            'hostname': conf.get('network', {}).get('hostname'),
            'generate_hosts': conf.get('network', {}).get('generatehosts', True),
            'generate_resolvconf': conf.get('network', {}).get('generateresolvconf', True)
        }

    def get_automount_settings(self):
        """Returns mount config"""
        conf = self.parse_wsl_conf()
        return {
            'enabled': conf.get('automount', {}).get('enabled', True),
            'root': conf.get('automount', {}).get('root', '/mnt'),
            'options': conf.get('automount', {}).get('options', '')
        }

    def get_default_user(self):
        """Returns default user"""
        return self.parse_wsl_conf().get('user', {}).get('default')

    def read_wsl_conf(self, output_format='raw'):
        """Reads /etc/wsl.conf"""
        return self._launch_process("cat /etc/wsl.conf")
        

    def list_installed_packages(self):
        """List installed packages"""
        commands = [
        ("apt", "apt list"),
        ("dnf", "dnf list installed"),
        ("yum", "yum list installed"),
        ("zypper", "zypper se --installed-only"),
    ]
        for name, cmd in commands:
        # Verifica si el gestor de paquetes está disponible
            check = self.run_command(f"which {name}")
            if isinstance(check, dict):
                found = bool(check.get('stdout', '').strip())
            else:
                found = bool(check.strip())
            if not found:
                continue  # El gestor no está presente, prueba el siguiente

            # Ejecuta el comando para listar paquetes
            result = self.run_command(cmd)
            output = result.get('stdout', '') if isinstance(result, dict) else result
            if output:
                return output.splitlines()

        # Si ninguno está disponible, retorna una lista vacía
        return []

    # ========================
    # Funciones de configuración Windows
    # ========================
    def read_wslconfig(self):
        """Read .wslconfig"""
        path = os.path.expanduser("~/.wslconfig")
        
        try:
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            print(f"Error leyendo {path}: {e}")
            return None

    def parse_wslconfig(self):
        """Analyzes .wslconfig and return dictionary"""
        raw_content = self.read_wslconfig()  # Debe devolver el texto plano del archivo
        config = {
            'wsl2': {}
        }
        current_section = None
        for line in raw_content.split('\n'):
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].lower()
                continue
            if '=' in line and current_section:
                key, value = line.split('=', 1)
                key = key.strip().lower()
                value = value.strip()
                # Convertir booleanos
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                # Convertir números si corresponde
                elif value.isdigit():
                    value = int(value)
                if current_section in config:
                    config[current_section][key] = value
        return config
    
    def wsl2_memory(self):
        """Returns memory limit in WSL2 or None"""
        conf = self.parse_wslconfig()
        return conf.get('wsl2', {}).get('memory')

    def wsl2_processors(self):
        """Returns processors in WSL2 o None"""
        conf = self.parse_wslconfig()
        return conf.get('wsl2', {}).get('processors')

    def wsl2_swap(self):
        """Returns swap size in WSL2 o None"""
        conf = self.parse_wslconfig()
        return conf.get('wsl2', {}).get('swap')

    def wsl2_localhost_forwarding(self):
        """Returns True/False for localhostForwarding in WSL2"""
        conf = self.parse_wslconfig()
        return conf.get('wsl2', {}).get('localhostforwarding', True)  # True por defecto

    def wsl2_gui_applications(self):
        """Devuelve True/False según la opción guiApplications de WSL2"""
        conf = self.parse_wslconfig()
        return conf.get('wsl2', {}).get('guiapplications', True)  # True por defecto


    # ========================
    # Funciones de mantenimiento
    # ========================
    def wsl_access_dates(self):
        return self.run_command("stat /")
        

    # ========================
    # Funciones de keep alive
    # ========================
    def stop_keep_alive(self):
        self.launch("pkill -f nosleep.sh")
       
    
    def keep_alive(self):
        
        nuevo_fichero = """
#!/bin/sh
while true
do
sleep 1s
done
"""
        current_dir = os.getcwd()
        script_path = os.path.join(current_dir, "nosleep.sh")
        with open(script_path, "w", encoding="utf-8",newline='\n') as f:
            f.write(nuevo_fichero)
        
        wsl_user = str(self.launch('whoami')["stdout"]).strip()
        
        wsl_dest = f"/home/{wsl_user}/nosleep.sh"
        self.copy_to_wsl(f"nosleep.sh",wsl_dest)        
        self.launch(f"chmod +x '{wsl_dest}'")
        self.launch(f"tmux new-session -d '{wsl_dest}'")

    # ========================
    # Funciones de archivo
    # ========================
    def copy_to_wsl(self, origin, dest, distro="Ubuntu"):
        """
        Copies a Windows file (origin) to a destination path (dest) in the specified WSL distribution.
        - origin: Absolute path in Windows 
        - dest: Absolute path in Linux (e.g., /home/user/file.txt)
        - distro: Name of the WSL distribution (default 'Ubuntu')

        """
        #Paso 1: Convertir la ruta destino de Linux a ruta Windows usando wslpath
        print(dest)
        try:
             result = subprocess.run(
                 ["wsl", "-d", distro, "wslpath", "-w", dest],
                 capture_output=True,
                 text=True,
                 check=True
             )
             dest_win = result.stdout.strip()
             if not dest:
                 raise RuntimeError("La conversión de rutaº no devolvió resultado.")
        except subprocess.CalledProcessError as e:
             raise RuntimeError(f"Error ejecutando wslpath: {e.stderr.strip()}") from e
        except Exception as e:
             raise RuntimeError(f"Error inesperado al convertir la ruta: {e}") from e

             

        # Paso 3: Copiar el archivo
        try:
            shutil.copy2(origin, dest_win)
            
            return True
        except Exception as e:
            raise RuntimeError(f"Error copiando el archivo: {e}") from e


    def copy_from_wsl(self, origin, dest, distro="Ubuntu"):
        """
        Copies a file from a path in WSL (origin, Linux) to a destination path in Windows (dest).
        - origin: Absolute path in Linux (e.g., /home/user/file.txt)
        - dest: Absolute path in Windows 
        - distro: Name of the WSL distribution (default 'Ubuntu')
        
        """
        # Paso 1: Convertir la ruta de origen de Linux a Windows usando wslpath
        try:
            result = subprocess.run(
                ["wsl", "-d", distro, "wslpath", "-w", origin],
                capture_output=True,
                text=True,
                check=True
            )
            origin_win = result.stdout.strip()
            if not origin_win:
                raise RuntimeError("La conversión de ruta no devolvió resultado.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error ejecutando wslpath: {e.stderr.strip()}") from e
        except Exception as e:
            raise RuntimeError(f"Error inesperado al convertir la ruta: {e}") from e

        # Paso 2: Verificar que el archivo existe en la ruta de Windows
        if not os.path.isfile(origin_win):
            raise FileNotFoundError(f"El archivo de origen no existe: {origin_win}")

        # Paso 3: Copiar el archivo al destino en Windows
        try:
            shutil.copy2(origin_win, dest)
            return True
        except Exception as e:
            raise RuntimeError(f"Error copiando el archivo: {e}") from e


    def wsl_backup(self, dest, distro="Ubuntu"):
        cmd = f"wsl --export {distro} {dest})"
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return process

    # ========================
    # Funciones de red
    # ========================


    def get_wsl_ip(self):
        """
        Gets current IP.
        If distro_name is None, uses defautl.
        """
        if self.distro:
            cmd = f"wsl -d {self.distro} hostname -I"
        else:
            cmd = "wsl hostname -I"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        ip = result.stdout.strip().split()[0]  # Primer IPa devuelta
        return ip
    