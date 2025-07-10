"""
wslapi.py

This module provides a Python interface to the Windows Subsystem for Linux (WSL) API using ctypes. It defines classes and methods to interact with WSL distributions, including launching commands, registering/unregistering distributions, configuring distributions, and retrieving configuration details.

Classes:
    WslHResult: HRESULT codes for WSL API operations.
    WslDistributionFlags: Flags for WSL distribution configuration.
    DistributionConfig: Data class for WSL distribution configuration.
    WslAPI: Main class for interacting with the WSL API.
"""
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import Tuple, Optional, Dict, Any

from pykernel import ole32


class WslHResult(IntEnum):
    """
    HRESULT codes returned by WSL API functions.
    """
    S_OK = 0x00000000
    E_FAIL = 0x80004005
    E_ACCESS_DENIED = 0x80070005


class WslDistributionFlags(IntFlag):
    """
    Flags for configuring WSL distributions.
    """
    NONE = 0x0
    ENABLE_INTEROP = 0x1
    APPEND_NT_PATH = 0x2
    ENABLE_DRIVE_MOUNTING = 0x4
    WSL2 = 0X8


@dataclass
class DistributionConfig:
    """
    Data class representing the configuration of a WSL distribution.

    Attributes:
        version (int): WSL version.
        uid (int): Default user ID.
        flags (WslDistributionFlags): Distribution flags.
        env_vars (Optional[Dict[str, Any]]): Environment variables.
    """
    version: int
    uid: int
    flags: WslDistributionFlags
    env_vars: Optional[Dict[str, Any]] = None


class WslAPI:
    """
    Python wrapper for the Windows WSL API (wslapi.dll).

    Provides methods to manage and interact with WSL distributions.
    """

    def __init__(self):
        """
        Initialize the WslAPI instance, loading wslapi.dll and configuring function signatures.
        """
        self.__wslapi = ctypes.WinDLL("wslapi.dll")
        self.__configure_wslapi_functions()
        self.__ole32py = ole32.Ole32()

    def __configure_wslapi_functions(self):
        """
        Configure argument and return types for WSL API functions.
        """
        self.__wslapi.WslLaunch.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_wchar_p,
            wintypes.BOOL,
            wintypes.HANDLE,
            wintypes.HANDLE,
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.HANDLE)
        ]
        self.__wslapi.WslLaunch.restype = ctypes.HRESULT

        self.__wslapi.WslRegisterDistribution.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_wchar_p
        ]
        self.__wslapi.WslRegisterDistribution.restype = ctypes.HRESULT

        self.__wslapi.WslUnregisterDistribution.argtypes = [
            ctypes.c_wchar_p
        ]
        self.__wslapi.WslUnregisterDistribution.restype = ctypes.HRESULT

        self.__wslapi.WslIsDistributionRegistered.argtypes = [
            ctypes.c_wchar_p
        ]
        self.__wslapi.WslIsDistributionRegistered.restype = wintypes.BOOL

        self.__wslapi.WslConfigureDistribution.argtypes = [
            wintypes.LPCWSTR,
            wintypes.ULONG,
            wintypes.ULONG
        ]
        self.__wslapi.WslConfigureDistribution.restype = ctypes.HRESULT

        self.__wslapi.WslGetDistributionConfiguration.argtypes = [
            wintypes.LPCWSTR,
            ctypes.POINTER(wintypes.ULONG),
            ctypes.POINTER(wintypes.ULONG),
            ctypes.POINTER(wintypes.ULONG),
            ctypes.POINTER(ctypes.c_void_p)
        ]
        self.__wslapi.WslGetDistributionConfiguration.restype = ctypes.HRESULT

        self.__wslapi.WslLaunchInteractive.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.BOOL,
            ctypes.POINTER(wintypes.DWORD)
        ]
        self.__wslapi.WslLaunchInteractive.restype = ctypes.HRESULT

    def wsl_launch(self, distribution_name: str, command: str, std_out: wintypes.HANDLE, std_in: wintypes.HANDLE,
                   std_err: wintypes.HANDLE, process_handle: wintypes.HANDLE,
                   use_current_working_directory: bool = True) -> WslHResult:
        """
        Launch a process in the specified WSL distribution.

        Args:
            distribution_name (str): Name of the WSL distribution.
            command (str): Command to execute.
            std_out (wintypes.HANDLE): Handle for standard output.
            std_in (wintypes.HANDLE): Handle for standard input.
            std_err (wintypes.HANDLE): Handle for standard error.
            process_handle (wintypes.HANDLE): Handle to receive the process handle.
            use_current_working_directory (bool): Whether to use the current working directory.

        Returns:
            WslHResult: Result code from the WSL API.
        """
        return self.__wslapi.WslLaunch(
            distribution_name, command, use_current_working_directory, std_in, std_out, std_err, process_handle
        )

    def wsl_register_distribution(self, distribution_name: str, tar_gz_path: str) -> ctypes.HRESULT:
        """
        Register a new WSL distribution from a tar.gz root filesystem.

        Args:
            distribution_name (str): Name of the WSL distribution.
            tar_gz_path (str): Path to the root filesystem tar.gz file.

        Returns:
            ctypes.HRESULT: Result code from the WSL API.
        """
        return self.__wslapi.WslRegisterDistribution(distribution_name, tar_gz_path)

    def wsl_unregister_distribution(self, distribution_name: str) -> ctypes.HRESULT:
        """
        Unregister (delete) a WSL distribution.

        Args:
            distribution_name (str): Name of the WSL distribution.

        Returns:
            ctypes.HRESULT: Result code from the WSL API.
        """
        return self.__wslapi.WslUnregisterDistribution(distribution_name)

    def wsl_is_distribution_registered(self, distribution_name: str) -> bool:
        """
        Check if a WSL distribution is registered.

        Args:
            distribution_name (str): Name of the WSL distribution.

        Returns:
            bool: True if registered, False otherwise.
        """
        return self.__wslapi.WslIsDistributionRegistered(distribution_name)

    def wsl_configure_distribution(self, distribution_name: str, uid: int,
                                   flags: WslDistributionFlags) -> ctypes.HRESULT:
        """
        Configure a WSL distribution's default user and flags.

        Args:
            distribution_name (str): Name of the WSL distribution.
            uid (int): Default user ID.
            flags (WslDistributionFlags): Distribution flags.

        Returns:
            ctypes.HRESULT: Result code from the WSL API.
        """
        return self.__wslapi.WslConfigureDistribution(distribution_name, uid, flags)

    def wsl_get_distribution_configuration(
            self, distribution_name: str) -> Tuple[WslHResult, Optional[DistributionConfig]]:
        """
        Retrieve the configuration of a WSL distribution.

        Args:
            distribution_name (str): Name of the WSL distribution.

        Returns:
            Tuple[WslHResult, Optional[DistributionConfig]]: Result code and configuration data (if successful).
        """
        version = ctypes.c_ulong()
        uid = ctypes.c_ulong()
        flags = ctypes.c_ulong()
        env_vars = ctypes.c_void_p()
        result = self.__wslapi.WslGetDistributionConfiguration(
            distribution_name,
            ctypes.byref(version),
            ctypes.byref(uid),
            ctypes.byref(flags),
            ctypes.byref(env_vars)
        )
        distribution_config = None
        if result == WslHResult.S_OK:
            env_vars_dict = None
            env_string = ctypes.cast(env_vars, ctypes.c_wchar_p).value
            if env_string:
                env_vars_dict = {}
                # Parse environment variables from null-separated string
                raw_vars = env_string.split('\0')
                for var in raw_vars:
                    if '=' in var:
                        key, val = var.split('=', 1)
                        env_vars_dict[key] = val

            # Free memory allocated by the API
            self.__ole32py.co_task_mem_free(mem_buffer=env_vars)

            distribution_config = DistributionConfig(
                version=version.value, uid=uid.value, flags=WslDistributionFlags(flags.value), env_vars=env_vars_dict
            )
        return result, distribution_config

    def wsl_launch_interactive(self, distribution_name: str, command: str,
                               use_current_working_directory: bool = True) -> Tuple[WslHResult, Optional[int]]:
        """
        Launch a command interactively in the specified WSL distribution.

        Args:
            distribution_name (str): Name of the WSL distribution.
            command (str): Command to execute.
            use_current_working_directory (bool): Whether to use the current working directory.

        Returns:
            Tuple[WslHResult, Optional[int]]: Result code and exit code (if successful).
        """
        exit_code = wintypes.DWORD()
        h_result = self.__wslapi.WslLaunchInteractive(
            distribution_name, command, use_current_working_directory, ctypes.byref(exit_code)
        )
        return h_result, exit_code.value if h_result == WslHResult.S_OK else None
