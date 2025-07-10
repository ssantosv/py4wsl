import ctypes
import os
import shlex
import shutil
import subprocess
import threading
import winreg
from ctypes import wintypes
from typing import Tuple

from pykernel import kernel32, wslapi
from pykernel.kernel32 import WaitResult, Overlapped
from pykernel.wslapi import WslHResult, WslDistributionFlags


# ==================================================
# API Windows structures
# ==================================================

class WSL:

    def __init__(self, distro='Ubuntu'):
        self.distro = distro
        self.wsl_api = wslapi.WslAPI()
        self.kernel32py = kernel32.Kernel32()

    def get_distribution_configuration(self):
        config = {
            'name': self.distro,
            'version': None,
            'default_uid': None,
            'flags': None,
            'env_vars': {}
        }

        h_result, configuration = self.wsl_api.wsl_get_distribution_configuration(distribution_name=self.distro)

        if h_result == WslHResult.S_OK and configuration is not None:
            config['version'] = configuration.version
            config['default_uid'] = configuration.uid
            config['flags'] = configuration.flags
            if config['flags'] & WslDistributionFlags.ENABLE_INTEROP:
                print("ENABLE_INTEROP")
            if config['flags'] & WslDistributionFlags.APPEND_NT_PATH:
                print("APPEND_NT_PATH")
            if config['flags'] & WslDistributionFlags.ENABLE_DRIVE_MOUNTING:
                print("ENABLE_DRIVE_MOUNTING")
            if config['flags'] == WslDistributionFlags.NONE:
                print("NONE")

            config['env_vars'] = configuration.env_vars

        return config if h_result == WslHResult.S_OK else None

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
            print(f"Error accesing registry: {e}")
        return None

    def configure_distribution(self, default_uid: int = None, flags: WslDistributionFlags = None) -> bool:
        """
        
        Configure the WSL distribution parameters


        Args:
            default_uid (int): Default user UID
            flags (WslDistributionFlags): Configuration flags
        
        """
        current_config = self.get_distribution_configuration()

        # Keep current values if not specified
        final_uid = default_uid if default_uid is not None else current_config['default_uid']
        final_flags = flags if flags is not None else current_config['flags']

        return self.wsl_api.wsl_configure_distribution(
            distribution_name=self.distro, uid=final_uid, flags=final_flags
        ) == WslHResult.S_OK

    def set_distribution_flag(self, flag: WslDistributionFlags, enable: bool):
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
        return self.wsl_api.wsl_register_distribution(
            distribution_name=distribution_name, tar_gz_path=tar_gz_path
        ) == WslHResult.S_OK

    def unregister_distribution(self, distribution_name: str) -> bool:
        """
        Unregister a WSL distribution.

        Args:
            distribution_name: Name of the distribution to remove
        Returns:
            bool: True if the operation was successful
        """
        return self.wsl_api.wsl_unregister_distribution(distribution_name=distribution_name) == WslHResult.S_OK

    def is_distribution_registered(self, distribution_name: str) -> bool:
        """
        Checks if a distribution is registered.

        Args:
        distribution_name: Name of the distribution to check

        Returns:
        bool: True if the distribution is registered
        """
        return bool(self.wsl_api.wsl_is_distribution_registered(distribution_name))

    def launch_interactive(self, command: str = None, use_current_working_directory: bool = True) -> dict:
        """
        Executes an interactive command using WslLaunchInteractive.
        
            Args:
                command (str, optional): Command to execute. If None, launches the default shell.
                use_current_working_directory (bool): Use the current working directory of the calling process.

            Returns:
                dict: {
                "hr": HRESULT,
                "exit_code": int (only if hr == 0)
                }
        """

        hr, exit_code = self.wsl_api.wsl_launch_interactive(
            distribution_name=self.distro, command=command, use_current_working_directory=use_current_working_directory)

        return {
            "hr": hr,
            "exit_code": exit_code
        }

    def _create_pipe(self) -> Tuple[wintypes.HANDLE, wintypes.HANDLE]:
        """Create an anonymous pipe with handle inheritance"""
        return self.kernel32py.create_pipe()

    def _read_pipe_async(self, handle):
        """Read data from a pipe asynchronously."""
        buffer = ctypes.create_string_buffer(4096)
        overlapped = Overlapped()
        output = b""

        while True:
            success = self.kernel32py.read_file(pipe_handle=handle, buffer=buffer, overlapped=overlapped)

            if not success and ctypes.get_last_error() != 997:  # ERROR_IO_PENDING
                break

            n_bytes_transferred = self.kernel32py.get_overlapped_result(pipe_handle=handle, overlapped=overlapped)
            if n_bytes_transferred == 0:
                break

            output += buffer[:n_bytes_transferred]

        return output

    def _launch_process(self, command):
        """Execute a command using the native API with timeout handling."""
        stdout_read, stdout_write = self._create_pipe()
        stderr_read, stderr_write = self._create_pipe()
        process_handle = wintypes.HANDLE()

        try:
            # Lanzar proceso

            hr = self.wsl_api.wsl_launch(
                distribution_name=self.distro, command=command, std_in=wintypes.HANDLE(0), std_out=stdout_write,
                std_err=stderr_write, process_handle=process_handle
            )

            if hr != WslHResult.S_OK:
                return {"hr": hr, "stdout": b"", "stderr": b"", "exit_code": 1}

            # Cerrar extremos de escritura
            self.kernel32py.close_handle(stdout_write)
            self.kernel32py.close_handle(stderr_write)

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
                    self.kernel32py.close_handle(pipe_handle=handle)

    def _wait_for_process(self, process_handle, timeout=30000):
        """Wait for the process to finish with a maximum timeout."""
        result = self.kernel32py.wait_for_single_object(process_handle=process_handle, timeout=timeout)

        if result == WaitResult.OBJECT_0:
            return self.kernel32py.get_exit_code_process(process_handle=process_handle)

        elif result == WaitResult.TIMEOUT:
            self.kernel32py.terminate_process(process_handle=process_handle)
            return -1
        else:
            return -2

    # ==============================================
    # Public methods
    # ==============================================
    def launch(self, command: str, capture_output: bool = True) -> dict:
        """Execute a command using the native api"""
        result = self._launch_process(command)
        return {
            "stdout": result["stdout"].decode("utf-8", errors="replace") if capture_output else "",
            "stderr": result["stderr"].decode("utf-8", errors="replace") if capture_output else "",
            "exit_code": result["exit_code"]
        }

    def run_command(self, command, capture_output=True, shell=False, input=None):
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
    # Administration
    # ========================

    def parse_wsl_conf(self):
        raw_content = self.read_wsl_conf()
        if isinstance(raw_content, dict):
            # Parsed. Just return.
            return raw_content

        config = {
            'automount': {},
            'network': {},
            'interop': {},
            'user': {},
            'boot': {},
            'useWindowsTimezone': {},
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
            # Check package manager available
            check = self.run_command(f"which {name}")
            if isinstance(check, dict):
                found = bool(check.get('stdout', '').strip())
            else:
                found = bool(check.strip())
            if not found:
                continue

                # Execute command to list packages
            result = self.run_command(cmd)
            output = result.get('stdout', '') if isinstance(result, dict) else result
            if output:
                return output.splitlines()

        # Empty list if no manager available
        return []

    # ========================
    # Windows configuration
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
        raw_content = self.read_wslconfig()
        config = {
            'wsl2': {}
        }
        current_section = None
        if raw_content is not None:
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
                    # Boolean converter
                    if value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    # Convert numbers
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
        """Returns processors in WSL2 or None"""
        conf = self.parse_wslconfig()
        return conf.get('wsl2', {}).get('processors')

    def wsl2_swap(self):
        """Returns swap size in WSL2 or None"""
        conf = self.parse_wslconfig()
        return conf.get('wsl2', {}).get('swap')

    def wsl2_localhost_forwarding(self):
        """Returns True/False for localhostForwarding in WSL2"""
        conf = self.parse_wslconfig()
        return conf.get('wsl2', {}).get('localhostforwarding', True)

    def wsl2_gui_applications(self):
        """Devuelve True/False según la opción guiApplications de WSL2"""
        conf = self.parse_wslconfig()
        return conf.get('wsl2', {}).get('guiapplications', True)

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
        with open(script_path, "w", encoding="utf-8", newline='\n') as f:
            f.write(nuevo_fichero)

        wsl_user = str(self.launch('whoami')["stdout"]).strip()

        wsl_dest = f"/home/{wsl_user}/nosleep.sh"
        self.copy_to_wsl(f"nosleep.sh", wsl_dest)
        self.launch(f"chmod +x '{wsl_dest}'")
        self.launch(f"tmux new-session -d '{wsl_dest}'")

    # ========================
    # File functions
    # ========================
    def copy_to_wsl(self, origin, dest, distro="Ubuntu"):
        """
        Copies a Windows file (origin) to a destination path (dest) in the specified WSL distribution.
        - origin: Absolute path in Windows 
        - dest: Absolute path in Linux (e.g., /home/user/file.txt)
        - distro: Name of the WSL distribution (default 'Ubuntu')

        """
        # wslpath to convert linux destination path
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
                raise RuntimeError("Path convertion with no result.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error executing wslpath: {e.stderr.strip()}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error converting path: {e}") from e

        # Copy the file
        try:
            shutil.copy2(origin, dest_win)

            return True
        except Exception as e:
            raise RuntimeError(f"Error copying file: {e}") from e

    def copy_from_wsl(self, origin, dest, distro="Ubuntu"):
        """
        Copies a file from a path in WSL (origin, Linux) to a destination path in Windows (dest).
        - origin: Absolute path in Linux (e.g., /home/user/file.txt)
        - dest: Absolute path in Windows 
        - distro: Name of the WSL distribution (default 'Ubuntu')
        
        """
        # wslpath converting origin linux path to windows
        try:
            result = subprocess.run(
                ["wsl", "-d", distro, "wslpath", "-w", origin],
                capture_output=True,
                text=True,
                check=True
            )
            origin_win = result.stdout.strip()
            if not origin_win:
                raise RuntimeError("Path convertion with no result.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error executing wslpath: {e.stderr.strip()}") from e
        except Exception as e:
            raise RuntimeError(f"Unexpected error converting path: {e}") from e

        # Check if file exists in windows path
        if not os.path.isfile(origin_win):
            raise FileNotFoundError(f"Origin file does not exists: {origin_win}")

        # Copy file to windows path
        try:
            shutil.copy2(origin_win, dest)
            return True
        except Exception as e:
            raise RuntimeError(f"Error copying file: {e}") from e

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
    # Network funtions
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
        ip = result.stdout.strip().split()[0]
        return ip
