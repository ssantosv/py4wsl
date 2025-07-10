"""
This module provides a Python wrapper for selected functions from the Windows OLE32 library using ctypes.
It currently supports memory management via CoTaskMemFree.
"""
import ctypes
from typing import Any


class Ole32:
    """
    Wrapper for the Windows OLE32 library functions using ctypes.
    Provides access to memory management functions such as CoTaskMemFree.
    """

    def __init__(self):
        """
        Initializes the Ole32 wrapper and configures the required OLE32 functions.
        """
        self.__ole32 = ctypes.WinDLL('ole32')
        self.__configure_ole32_functions()

    def __configure_ole32_functions(self):
        """
        Configures the argument and return types for the OLE32 functions used.
        """
        # Set the argument and return types for CoTaskMemFree
        self.__ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
        self.__ole32.CoTaskMemFree.restype = None

    def co_task_mem_free(self, mem_buffer: Any) -> None:
        """
        Frees a memory buffer allocated by OLE functions.

        Args:
            mem_buffer (Any): The memory buffer to be freed.
        """
        self.__ole32.CoTaskMemFree(mem_buffer)
