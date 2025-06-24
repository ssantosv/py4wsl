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

