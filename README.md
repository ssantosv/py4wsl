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
    wsl.copy_to_wsl("c:\\users\\sergio\\downloads\\freevideo.exe","/home/sergio/freevideo.exe")
    wsl.copy_from_wsl("/home/sergio/freevideo.exe", "c:\\users\\sergio\\downloads\\freevideo2.exe")
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

