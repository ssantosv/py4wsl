# 🐧 WSL-Python: Wrapper to interact with WSL from Python

---

## 🚀 What is WSL-Python?

**WSL-Python** is a library that allows you to easily and powerfully interact with the Windows Subsystem for Linux (WSL) directly from Python. It provides a *wrapper* to execute commands, manage distributions, manipulate files between Windows and WSL, and configure different aspects of your WSL environment, all from your Python code.

> **WSL-Python uses both Python's `subprocess` module and native calls to the Windows `wslapi.dll` DLL, selecting the most suitable method depending on the needs of each operation.** This allows combining flexibility, compatibility, and maximum performance.

Ideal for automation, administration tools, continuous integration, or simply to make your life with WSL much easier.

---

## 🛠️ Main Features

- **Command execution**: Run commands in WSL and capture their output, using both `subprocess` and the native API.
- **Distribution management**: Register, remove, configure, and query WSL distributions directly through the native API.
- **File manipulation**: Copy files between Windows and WSL in both directions.
- **Advanced configuration**: Read and modify `/etc/wsl.conf` and `.wslconfig` settings.
- **Package installation**: Install packages in the WSL distro using `apt-get` (or autodetect the available package manager).
- **Network and system management**: Query IP, network configuration, default user, etc.
- **Automation and maintenance**: *Keep alive* scripts, distribution backup, and more.

---

## 📦 Installation

```
pip install wsl-python  # Coming soon on PyPI
```

Or simply add `wsl.py` to your project.

---

## 📝 Usage Examples

### 1. Run a command in WSL and get the output

```
from wsl import WSL

wsl = WSL(distro='Ubuntu')
result = wsl.launch('ls -l /home')
print(result['stdout'])
```

### 2. Install a package using sudo

```
wsl.install_package('htop', password='your_password')
```

### 3. Copy a file from Windows to WSL

```
wsl.copy_to_wsl('C:\\Users\\user\\file.txt', '/home/user/file.txt')
```

### 4. Query distribution configuration

```
config = wsl.get_distribution_configuration()
print(config)
```

### 5. Read and parse `/etc/wsl.conf`

```
conf = wsl.parse_wsl_conf()
print(conf)
```

### 6. Get the distro's IP

```
ip = wsl.get_wsl_ip()
print(f"WSL IP is: {ip}")
```

---

## 📚 Main Functions

| Category                 | Function                               | Brief Description                                         |
|--------------------------|----------------------------------------|-----------------------------------------------------------|
| Commands                 | `launch`, `run_command`                | Run commands in WSL (`launch` uses the native API, `run_command` uses `subprocess`) |
| Distributions            | `register_distribution`, `unregister_distribution`, `is_distribution_registered`, `get_distribution_configuration`, `configure_distribution` | Manage and configure distros via native API      |
| Files                    | `copy_to_wsl`, `copy_from_wsl`         | Copy files between Windows and WSL                        |
| Configuration            | `parse_wsl_conf`, `parse_wslconfig`    | Read and parse configuration files                        |
| Packages                 | `install_package`, `list_installed_packages` | Install and list packages in the distro                   |
| Network and system       | `get_wsl_ip`, `get_network_config`, `get_default_user` | Query network and user information                        |
| Maintenance              | `wsl_backup`, `wsl_access_dates`       | Backup and access dates                                   |
| Automation               | `keep_alive`, `stop_keep_alive`        | Keep processes alive in WSL                               |

---

## ⚠️ Status and Collaboration

> **Attention!**  
> This library is under development and may contain errors or unexpected behavior.  
> Any collaboration, suggestion, or bug report is more than welcome!  
> You can open issues or send pull requests to help improve the project.

---

## 🤝 Contribute

- Fork the repository
- Create a branch for your feature/fix
- Make a pull request with a clear description of the changes

---

## 📝 License

MIT License

---

Thank you for using and improving **WSL-Python**!  
🐧💻✨

---

# PyWSL

Usage example:

```python
import time
import pywsl 


if __name__ == "__main__":

    wsl = pywsl.WSL(distro="Ubuntu")  
    print(wsl.read_wsl_conf()["stderr"])
    print(wsl.read_wsl_conf()["stdout"])
    print(wsl.list_installed_packages())
    print(wsl.read_wslconfig())
    print(wsl.get_distribution_configuration())
    print(wsl.get_wsl_ip())
    wsl.launch_interactive("nano")
    wsl.copy_to_wsl("c:\\users\\user\\downloads\\freevideo.exe","/home/user/file.exe")
    wsl.copy_from_wsl("/home/user/file.exe", "c:\\users\\user\\downloads\\file.exe")
    print(wsl.get_default_user())
    print(wsl.get_automount_settings()["root"])
    print(wsl.is_interop_enabled())
    print(wsl.wsl_access_dates()["stdout"])
    print(wsl.is_systemd_enabled())
    print(wsl.wsl2_swap())
    print(wsl.wsl2_processors())
    print(wsl.run_command("which apt")["stdout"])
    print(wsl.list_installed_packages())
    wsl.keep_alive()
    time.sleep(24)
    wsl.stop_keep_alive()
    #wsl.wsl_backup("backup.tar")
    print(wsl.wsl_access_dates()["stdout"])
    
    print(wsl.run_command("apt-get"))
    print(wsl.run_command("cat /tmp/mipid"))

    time.sleep(10)
    
    info = wsl.get_wsl_distro_info_by_name()
    if info:
         print("Información de la distribución:")
         for k, v in info.items():
             print(f"{k}: {v}")
    print(wsl.get_wsl_distro_info_by_name()["osVersion"])
            
    print(wsl.install_package("htop","123456"))
    
    wsl.launch_interactive("nano")

```


# 🐧 WSL-Python: Wrapper para interactuar con WSL desde Python

---

## 🚀 ¿Qué es WSL-Python?

**WSL-Python** es una librería que te permite interactuar de forma sencilla y potente con el Subsistema de Windows para Linux (WSL) directamente desde Python. Proporciona un *wrapper* para ejecutar comandos, administrar distribuciones, manipular archivos entre Windows y WSL, y configurar distintos aspectos de tu entorno WSL, todo desde tu código Python.

> **WSL-Python utiliza tanto el módulo `subprocess` de Python como llamadas nativas directas a la DLL `wslapi.dll` de Windows, seleccionando el método más adecuado según las necesidades de cada operación**. Esto permite combinar flexibilidad, compatibilidad y máximo rendimiento.

Ideal para automatización, herramientas de administración, integración continua o simplemente para hacer tu vida con WSL mucho más fácil.

---

## 🛠️ Funcionalidades principales

- **Ejecución de comandos**: Ejecuta comandos en WSL y captura su salida, usando tanto `subprocess` como la API nativa.
- **Gestión de distribuciones**: Registra, elimina, configura y consulta distribuciones WSL directamente mediante la API nativa.
- **Manipulación de archivos**: Copia archivos entre Windows y WSL en ambas direcciones.
- **Configuración avanzada**: Lee y modifica configuraciones de `/etc/wsl.conf` y `.wslconfig`.
- **Instalación de paquetes**: Instala paquetes en la distro WSL usando `apt-get` (o detecta el gestor disponible).
- **Manejo de red y sistema**: Consulta IP, configuración de red, usuario por defecto, etc.
- **Automatización y mantenimiento**: Scripts de *keep alive*, backup de distribuciones, y más.

---

## 📦 Instalación


pip install wsl-python # Próximamente en PyPI

O simplemente añade `wsl.py` a tu proyecto.

---

## 📝 Ejemplos de uso

### 1. Ejecutar un comando en WSL y obtener la salida

from wsl import WSL

wsl = WSL(distro='Ubuntu')
result = wsl.launch('ls -l /home')
print(result['stdout'])

### 2. Instalar un paquete usando sudo

wsl.install_package('htop', password='tu_contraseña')

### 3. Copiar un archivo de Windows a WSL

wsl.copy_to_wsl('C:\Users\usuario\archivo.txt', '/home/usuario/archivo.txt')

### 4. Consultar configuración de la distribución

config = wsl.get_distribution_configuration()
print(config)

### 5. Leer y parsear `/etc/wsl.conf`

conf = wsl.parse_wsl_conf()
print(conf)

### 6. Obtener la IP de la distro

ip = wsl.get_wsl_ip()
print(f"La IP de WSL es: {ip}")

---

## 📚 Funciones principales

| Categoría                | Función                               | Descripción breve                                         |
|--------------------------|---------------------------------------|-----------------------------------------------------------|
| Comandos                 | `launch`, `run_command`               | Ejecuta comandos en WSL (`launch` usa la API nativa, `run_command` usa `subprocess`) |
| Distribuciones           | `register_distribution`, `unregister_distribution`, `is_distribution_registered`, `get_distribution_configuration`, `configure_distribution` | Gestión y configuración de distros vía API nativa      |
| Archivos                 | `copy_to_wsl`, `copy_from_wsl`        | Copia archivos entre Windows y WSL                        |
| Configuración            | `parse_wsl_conf`, `parse_wslconfig`   | Lee y parsea archivos de configuración                    |
| Paquetes                 | `install_package`, `list_installed_packages` | Instala y lista paquetes en la distro                     |
| Red y sistema            | `get_wsl_ip`, `get_network_config`, `get_default_user` | Consulta información de red y usuario                     |
| Mantenimiento            | `wsl_backup`, `wsl_access_dates`      | Backup y fechas de acceso                                 |
| Automatización           | `keep_alive`, `stop_keep_alive`       | Mantiene procesos vivos en WSL                            |

---

## ⚠️ Estado y colaboración

> **¡Atención!**  
> Esta librería está en desarrollo y puede contener errores o comportamientos inesperados.  
> ¡Cualquier colaboración, sugerencia o reporte de bugs es más que bienvenida!  
> Puedes abrir issues o enviar pull requests para ayudar a mejorar el proyecto.

---

## 🤝 Contribuye

- Haz un *fork* del repositorio
- Crea una rama para tu feature/fix
- Haz un *pull request* con una descripción clara de los cambios

---

## 📝 Licencia

MIT License

---

¡Gracias por usar y mejorar **WSL-Python**!  
🐧💻✨




# PyWSL

Usage example:

```python
import time
import pywsl 


if __name__ == "__main__":

    wsl = pywsl.WSL(distro="Ubuntu")  
    print(wsl.read_wsl_conf()["stderr"])
    print(wsl.read_wsl_conf()["stdout"])
    print(wsl.list_installed_packages())
    print(wsl.read_wslconfig())
    print(wsl.get_distribution_configuration())
    print(wsl.get_wsl_ip())
    wsl.launch_interactive("nano")
    wsl.copy_to_wsl("c:\\users\\user\\downloads\\freevideo.exe","/home/user/file.exe")
    wsl.copy_from_wsl("/home/user/file.exe", "c:\\users\\user\\downloads\\file.exe")
    print(wsl.get_default_user())
    print(wsl.get_automount_settings()["root"])
    print(wsl.is_interop_enabled())
    print(wsl.wsl_access_dates()["stdout"])
    print(wsl.is_systemd_enabled())
    print(wsl.wsl2_swap())
    print(wsl.wsl2_processors())
    print(wsl.run_command("which apt")["stdout"])
    print(wsl.list_installed_packages())
    wsl.keep_alive()
    time.sleep(24)
    wsl.stop_keep_alive()
    #wsl.wsl_backup("backup.tar")
    print(wsl.wsl_access_dates()["stdout"])
    
    print(wsl.run_command("apt-get"))
    print(wsl.run_command("cat /tmp/mipid"))

    time.sleep(10)
    
    info = wsl.get_wsl_distro_info_by_name()
    if info:
         print("Información de la distribución:")
         for k, v in info.items():
             print(f"{k}: {v}")
    print(wsl.get_wsl_distro_info_by_name()["osVersion"])
            
    print(wsl.install_package("htop","123456"))
    
    wsl.launch_interactive("nano")
```    

