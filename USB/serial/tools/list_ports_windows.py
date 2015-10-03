#! python
#
# Enumerate serial ports on Windows including a human readable description
# and hardware information.
#
# (C) 2001-2015 Chris Liechti <cliechti@gmx.net>
#
# SPDX-License-Identifier:    BSD-3-Clause

import re
import ctypes
from ctypes.wintypes import BOOL
from ctypes.wintypes import HWND
from ctypes.wintypes import DWORD
from ctypes.wintypes import WORD
from ctypes.wintypes import LONG
from ctypes.wintypes import ULONG
from ctypes.wintypes import LPCSTR
from ctypes.wintypes import HKEY
from ctypes.wintypes import BYTE
import serial
from serial.win32 import ULONG_PTR


def numsplit(text):
    """\
    Convert string into a list of texts and numbers in order to support a
    natural sorting.
    """
    result = []
    for group in re.split(r'(\d+)', text):
        if group:
            try:
                group = int(group)
            except ValueError:
                pass
            result.append(group)
    return result


def ValidHandle(value, func, arguments):
    if value == 0:
        raise ctypes.WinError()
    return value

NULL = 0
HDEVINFO = ctypes.c_void_p
PCTSTR = ctypes.c_char_p
PTSTR = ctypes.c_void_p
CHAR = ctypes.c_char
LPDWORD = PDWORD = ctypes.POINTER(DWORD)
#~ LPBYTE = PBYTE = ctypes.POINTER(BYTE)
LPBYTE = PBYTE = ctypes.c_void_p        # XXX avoids error about types

ACCESS_MASK = DWORD
REGSAM = ACCESS_MASK


def byte_buffer(length):
    """Get a buffer for a string"""
    return (BYTE*length)()


def string(buffer):
    s = []
    for c in buffer:
        if c == 0:
            break
        s.append(chr(c & 0xff))  # "& 0xff": hack to convert signed to unsigned
    return ''.join(s)


class GUID(ctypes.Structure):
    _fields_ = [
        ('Data1', DWORD),
        ('Data2', WORD),
        ('Data3', WORD),
        ('Data4', BYTE*8),
    ]

    def __str__(self):
        return "{%08x-%04x-%04x-%s-%s}" % (
            self.Data1,
            self.Data2,
            self.Data3,
            ''.join(["%02x" % d for d in self.Data4[:2]]),
            ''.join(["%02x" % d for d in self.Data4[2:]]),
        )


class SP_DEVINFO_DATA(ctypes.Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('ClassGuid', GUID),
        ('DevInst', DWORD),
        ('Reserved', ULONG_PTR),
    ]

    def __str__(self):
        return "ClassGuid:%s DevInst:%s" % (self.ClassGuid, self.DevInst)

PSP_DEVINFO_DATA = ctypes.POINTER(SP_DEVINFO_DATA)

PSP_DEVICE_INTERFACE_DETAIL_DATA = ctypes.c_void_p

setupapi = ctypes.windll.LoadLibrary("setupapi")
SetupDiDestroyDeviceInfoList = setupapi.SetupDiDestroyDeviceInfoList
SetupDiDestroyDeviceInfoList.argtypes = [HDEVINFO]
SetupDiDestroyDeviceInfoList.restype = BOOL

SetupDiClassGuidsFromName = setupapi.SetupDiClassGuidsFromNameA
SetupDiClassGuidsFromName.argtypes = [PCTSTR, ctypes.POINTER(GUID), DWORD, PDWORD]
SetupDiClassGuidsFromName.restype = BOOL

SetupDiEnumDeviceInfo = setupapi.SetupDiEnumDeviceInfo
SetupDiEnumDeviceInfo.argtypes = [HDEVINFO, DWORD, PSP_DEVINFO_DATA]
SetupDiEnumDeviceInfo.restype = BOOL

SetupDiGetClassDevs = setupapi.SetupDiGetClassDevsA
SetupDiGetClassDevs.argtypes = [ctypes.POINTER(GUID), PCTSTR, HWND, DWORD]
SetupDiGetClassDevs.restype = HDEVINFO
SetupDiGetClassDevs.errcheck = ValidHandle

SetupDiGetDeviceRegistryProperty = setupapi.SetupDiGetDeviceRegistryPropertyA
SetupDiGetDeviceRegistryProperty.argtypes = [HDEVINFO, PSP_DEVINFO_DATA, DWORD, PDWORD, PBYTE, DWORD, PDWORD]
SetupDiGetDeviceRegistryProperty.restype = BOOL

SetupDiGetDeviceInstanceId = setupapi.SetupDiGetDeviceInstanceIdA
SetupDiGetDeviceInstanceId.argtypes = [HDEVINFO, PSP_DEVINFO_DATA, PTSTR, DWORD, PDWORD]
SetupDiGetDeviceInstanceId.restype = BOOL

SetupDiOpenDevRegKey = setupapi.SetupDiOpenDevRegKey
SetupDiOpenDevRegKey.argtypes = [HDEVINFO, PSP_DEVINFO_DATA, DWORD, DWORD, DWORD, REGSAM]
SetupDiOpenDevRegKey.restype = HKEY

advapi32 = ctypes.windll.LoadLibrary("Advapi32")
RegCloseKey = advapi32.RegCloseKey
RegCloseKey.argtypes = [HKEY]
RegCloseKey.restype = LONG

RegQueryValueEx = advapi32.RegQueryValueExA
RegQueryValueEx.argtypes = [HKEY, LPCSTR, LPDWORD, LPDWORD, LPBYTE, LPDWORD]
RegQueryValueEx.restype = LONG


DIGCF_PRESENT = 2
DIGCF_DEVICEINTERFACE = 16
INVALID_HANDLE_VALUE = 0
ERROR_INSUFFICIENT_BUFFER = 122
SPDRP_HARDWAREID = 1
SPDRP_FRIENDLYNAME = 12
SPDRP_LOCATION_PATHS = 35
DICS_FLAG_GLOBAL = 1
DIREG_DEV = 0x00000001
KEY_READ = 0x20019

# workaround for compatibility between Python 2.x and 3.x
Ports = serial.to_bytes([80, 111, 114, 116, 115])  # "Ports"
PortName = serial.to_bytes([80, 111, 114, 116, 78, 97, 109, 101])  # "PortName"


class WinInfo(object):
    """Wrapper for device info"""

    def __init__(self, dev):
        self.dev = dev
        self.description = None
        self.hwid = None
        self.vid = None
        self.pid = None
        self.serial = None
        self.location = None

    def describe(self):
        """Get a human readable string"""
        return self.description if self.description is not None else 'n/a'

    def hwinfo(self):
        """Get a hardware description string"""
        if self.vid is not None:
            return 'USB VID:PID={}:{}{}{}'.format(
                    self.vid,
                    self.pid,
                    ' SER={}'.format(self.serial) if self.serial is not None else '',
                    ' LOCATION={}'.format(self.location) if self.location is not None else '',
                    )
        else:
            return self.hwid

    def __eq__(self, other):
        return self.dev == other.dev

    def __lt__(self, other):
        return numsplit(self.dev) < numsplit(other.dev)

    def __getitem__(self, index):
        """Item access: backwards compatible -> (port, desc, hwid)"""
        if index == 0:
            return self.dev
        elif index == 1:
            return self.describe()
        elif index == 2:
            return self.hwinfo()
        else:
            raise IndexError('{} > 2'.format(index))


def comports():
    GUIDs = (GUID*8)()  # so far only seen one used, so hope 8 are enough...
    guids_size = DWORD()
    if not SetupDiClassGuidsFromName(
            Ports,
            GUIDs,
            ctypes.sizeof(GUIDs),
            ctypes.byref(guids_size)):
        raise ctypes.WinError()

    # repeat for all possible GUIDs
    for index in range(guids_size.value):
        g_hdi = SetupDiGetClassDevs(
                ctypes.byref(GUIDs[index]),
                None,
                NULL,
                DIGCF_PRESENT)  # was DIGCF_PRESENT|DIGCF_DEVICEINTERFACE which misses CDC ports

        devinfo = SP_DEVINFO_DATA()
        devinfo.cbSize = ctypes.sizeof(devinfo)
        index = 0
        while SetupDiEnumDeviceInfo(g_hdi, index, ctypes.byref(devinfo)):
            index += 1

            # get the real com port name
            hkey = SetupDiOpenDevRegKey(
                    g_hdi,
                    ctypes.byref(devinfo),
                    DICS_FLAG_GLOBAL,
                    0,
                    DIREG_DEV,  # DIREG_DRV for SW info
                    KEY_READ)
            port_name_buffer = byte_buffer(250)
            port_name_length = ULONG(ctypes.sizeof(port_name_buffer))
            RegQueryValueEx(
                    hkey,
                    PortName,
                    None,
                    None,
                    ctypes.byref(port_name_buffer),
                    ctypes.byref(port_name_length))
            RegCloseKey(hkey)

            # unfortunately does this method also include parallel ports.
            # we could check for names starting with COM or just exclude LPT
            # and hope that other "unknown" names are serial ports...
            if string(port_name_buffer).startswith('LPT'):
                continue

            # hardware ID
            szHardwareID = byte_buffer(250)
            # try to get ID that includes serial number
            if not SetupDiGetDeviceInstanceId(
                    g_hdi,
                    ctypes.byref(devinfo),
                    ctypes.byref(szHardwareID),
                    ctypes.sizeof(szHardwareID) - 1,
                    None):
                # fall back to more generic hardware ID if that would fail
                if not SetupDiGetDeviceRegistryProperty(
                        g_hdi,
                        ctypes.byref(devinfo),
                        SPDRP_HARDWAREID,
                        None,
                        ctypes.byref(szHardwareID),
                        ctypes.sizeof(szHardwareID) - 1,
                        None):
                    # Ignore ERROR_INSUFFICIENT_BUFFER
                    if ctypes.GetLastError() != ERROR_INSUFFICIENT_BUFFER:
                        raise ctypes.WinError()
            # stringify
            szHardwareID_str = string(szHardwareID)

            info = WinInfo(string(port_name_buffer))
            info.hwid = szHardwareID_str

            # in case of USB, make a more readable string, similar to that form
            # that we also generate on other platforms
            if szHardwareID_str.startswith('USB'):
                m = re.search(r'VID_([0-9a-f]{4})&PID_([0-9a-f]{4})(\\(\w+))?', szHardwareID_str, re.I)
                if m:
                    info.vid = m.group(1)
                    info.pid = m.group(2)
                    if m.group(4):
                        info.serial = m.group(4)
                # calculate a location string
                # XXX was empty in tests with (internal) USB3 hub :(
                loc_path_str = byte_buffer(250)
                if SetupDiGetDeviceRegistryProperty(
                        g_hdi,
                        ctypes.byref(devinfo),
                        SPDRP_LOCATION_PATHS,
                        None,
                        ctypes.byref(loc_path_str),
                        ctypes.sizeof(loc_path_str) - 1,
                        None):
                    #~ print (string(loc_path_str))
                    m = re.finditer(r'USBROOT\((\w+)\)|#USB\((\w+)\)', string(loc_path_str))
                    location = []
                    for g in m:
                        if g.group(1):
                            location.append('%d' % (int(g.group(1)) + 1))
                        else:
                            if len(location) > 1:
                                location.append('.')
                            else:
                                location.append('-')
                            location.append(g.group(2))
                    if location:
                        info.location = ''.join(location)

            # friendly name
            szFriendlyName = byte_buffer(250)
            if SetupDiGetDeviceRegistryProperty(
                    g_hdi,
                    ctypes.byref(devinfo),
                    SPDRP_FRIENDLYNAME,
                    #~ SPDRP_DEVICEDESC,
                    None,
                    ctypes.byref(szFriendlyName),
                    ctypes.sizeof(szFriendlyName) - 1,
                    None):
                info.description = string(szFriendlyName)
            #~ else:
                # Ignore ERROR_INSUFFICIENT_BUFFER
                #~ if ctypes.GetLastError() != ERROR_INSUFFICIENT_BUFFER:
                    #~ raise IOError("failed to get details for %s (%s)" % (devinfo, szHardwareID.value))
                # ignore errors and still include the port in the list, friendly name will be same as port name
            yield info
        SetupDiDestroyDeviceInfoList(g_hdi)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# test
if __name__ == '__main__':
    for port, desc, hwid in sorted(comports()):
        print("%s: %s [%s]" % (port, desc, hwid))
