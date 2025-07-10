"""
kernel32.py

This module provides a Pythonic interface to selected Windows Kernel32 API functions using ctypes.
It defines structures and wrapper methods for pipe creation, file reading, process management, and synchronization primitives.
"""
import ctypes
from ctypes import wintypes

from enum import IntEnum
from typing import Tuple, Optional


class WaitResult(IntEnum):
    """
    Enum for possible results of wait functions in the Windows API.
    """
    OBJECT_0 = 0x00000000
    TIMEOUT = 0x00000102
    FAILED = 0xFFFFFFFF


class SecurityAttributes(ctypes.Structure):
    """
    Structure for SECURITY_ATTRIBUTES used in Windows API calls.
    """
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", ctypes.c_void_p),
        ("bInheritHandle", wintypes.BOOL)
    ]


class Overlapped(ctypes.Structure):
    """
    Structure for OVERLAPPED used in asynchronous I/O operations in Windows API.
    """
    _fields_ = [
        ("Internal", ctypes.c_ulonglong),
        ("InternalHigh", ctypes.c_ulonglong),
        ("Offset", wintypes.DWORD),
        ("OffsetHigh", wintypes.DWORD),
        ("hEvent", wintypes.HANDLE)
    ]


class Kernel32:
    """
    Wrapper class for selected Kernel32 Windows API functions using ctypes.
    Provides methods for pipe creation, file reading, process management, and synchronization.
    """

    def __init__(self):
        """
        Initialize the Kernel32 wrapper and configure function signatures.
        """
        self.__kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.__configure_kernel32_functions()

    def __configure_kernel32_functions(self):
        """
        Configure argument and return types for the used Kernel32 API functions.
        """
        self.__kernel32.CreatePipe.argtypes = [
            ctypes.POINTER(wintypes.HANDLE),
            ctypes.POINTER(wintypes.HANDLE),
            ctypes.POINTER(SecurityAttributes),
            wintypes.DWORD
        ]
        self.__kernel32.CreatePipe.restype = wintypes.BOOL

        self.__kernel32.ReadFile.argtypes = [
            wintypes.HANDLE,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(Overlapped)
        ]
        self.__kernel32.ReadFile.restype = wintypes.BOOL

        self.__kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.__kernel32.CloseHandle.restype = wintypes.BOOL

        self.__kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.__kernel32.WaitForSingleObject.restype = wintypes.DWORD

        self.__kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self.__kernel32.GetExitCodeProcess.restype = wintypes.BOOL

        self.__kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.__kernel32.TerminateProcess.restype = wintypes.BOOL

    def create_pipe(self) -> Tuple[wintypes.HANDLE, wintypes.HANDLE]:
        """
        Create an anonymous pipe with handle inheritance enabled.

        Returns:
            Tuple[wintypes.HANDLE, wintypes.HANDLE]: (read_handle, write_handle)
        Raises:
            WindowsError: If the pipe creation fails.
        """
        sa = SecurityAttributes()
        sa.nLength = ctypes.sizeof(SecurityAttributes)
        sa.lpSecurityDescriptor = None
        sa.bInheritHandle = wintypes.BOOL(True)

        read_handle = wintypes.HANDLE()
        write_handle = wintypes.HANDLE()

        if not self.__kernel32.CreatePipe(
                ctypes.byref(read_handle),
                ctypes.byref(write_handle),
                ctypes.byref(sa),
                0
        ):
            raise ctypes.WinError(ctypes.get_last_error())

        return read_handle, write_handle

    def read_file(self, pipe_handle: wintypes.HANDLE, buffer, overlapped) -> bool:
        """
        Read data from a file or pipe handle.

        Args:
            pipe_handle (wintypes.HANDLE): Handle to the file or pipe.
            buffer: Buffer to receive the data.
            overlapped: OVERLAPPED structure for asynchronous operations.
        Returns:
            bool: True if successful, False otherwise.
        """
        bytes_read = wintypes.DWORD()

        return self.__kernel32.ReadFile(
            pipe_handle,
            buffer,
            ctypes.sizeof(buffer),
            ctypes.byref(bytes_read),
            ctypes.byref(overlapped)
        )

    def get_overlapped_result(self, pipe_handle: wintypes.HANDLE, overlapped: Overlapped, wait: bool = True) -> int:
        """
        Retrieve the result of an overlapped (asynchronous) operation.

        Args:
            pipe_handle (wintypes.HANDLE): Handle to the file or pipe.
            overlapped (Overlapped): OVERLAPPED structure.
            wait (bool): Whether to wait for the operation to complete.
        Returns:
            int: Number of bytes transferred.
        Raises:
            WindowsError: If the operation fails.
        """
        bytes_transferred = wintypes.DWORD()
        result = self.__kernel32.GetOverlappedResult(
            pipe_handle,
            ctypes.byref(overlapped),
            ctypes.byref(bytes_transferred),
            wintypes.BOOL(wait)
        )
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())
        return bytes_transferred.value

    def close_handle(self, pipe_handle: wintypes.HANDLE) -> bool:
        """
        Close an open object handle.

        Args:
            pipe_handle (wintypes.HANDLE): Handle to close.
        Returns:
            bool: True if successful, False otherwise.
        """
        return self.__kernel32.CloseHandle(pipe_handle)

    def wait_for_single_object(self, process_handle: wintypes.HANDLE, timeout=30000) -> WaitResult:
        """
        Wait until the specified object is in the signaled state or the time-out interval elapses.

        Args:
            process_handle (wintypes.HANDLE): Handle to the object.
            timeout (int): Time-out interval in milliseconds (default: 30000).
        Returns:
            WaitResult: Result of the wait operation.
        """
        return self.__kernel32.WaitForSingleObject(process_handle, timeout)

    def get_exit_code_process(self, process_handle: wintypes.HANDLE) -> Optional[int]:
        """
        Retrieve the termination status of the specified process.

        Args:
            process_handle (wintypes.HANDLE): Handle to the process.
        Returns:
            Optional[int]: Exit code if successful, None otherwise.
        """
        exit_code = wintypes.DWORD()
        return exit_code.value if self.__kernel32.GetExitCodeProcess(process_handle, ctypes.byref(exit_code)) else None

    def terminate_process(self, process_handle: wintypes.HANDLE, exit_code: int = 1) -> bool:
        """
        Terminate the specified process and all of its threads.

        Args:
            process_handle (wintypes.HANDLE): Handle to the process.
            exit_code (int): Exit code to use for the process termination (default: 1).
        Returns:
            bool: True if successful, False otherwise.
        """
        return self.__kernel32.TerminateProcess(process_handle, exit_code)
