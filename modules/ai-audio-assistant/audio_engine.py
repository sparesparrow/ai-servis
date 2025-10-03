"""
Cross-Platform Audio Engine
Supports Linux (PipeWire/ALSA), Windows (WASAPI), and macOS (Core Audio)
"""
import asyncio
import logging
import platform
import subprocess
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import psutil

from audio_models import AudioEngine, AudioDevice, AudioDeviceType, AudioConfig

logger = logging.getLogger(__name__)


class CrossPlatformAudioEngine(AudioEngine):
    """Cross-platform audio engine implementation"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.system = platform.system().lower()
        self.devices: Dict[str, AudioDevice] = {}
        self.default_device: Optional[AudioDevice] = None
        self.is_initialized = False
        
        # Platform-specific implementations
        self.linux_engine = None
        self.windows_engine = None
        self.macos_engine = None
        
        # Initialize platform-specific engine
        self._initialize_platform_engine()
    
    def _initialize_platform_engine(self):
        """Initialize platform-specific audio engine"""
        if self.system == "linux":
            self.linux_engine = LinuxAudioEngine(self.config)
        elif self.system == "windows":
            self.windows_engine = WindowsAudioEngine(self.config)
        elif self.system == "darwin":  # macOS
            self.macos_engine = MacOSAudioEngine(self.config)
        else:
            logger.warning(f"Unsupported platform: {self.system}")
    
    async def initialize(self) -> bool:
        """Initialize the audio engine"""
        try:
            if self.system == "linux":
                if self.linux_engine:
                    success = await self.linux_engine.initialize()
                    if success:
                        self.devices = await self.linux_engine.get_devices()
                        self.default_device = await self.linux_engine.get_default_device()
            elif self.system == "windows":
                if self.windows_engine:
                    success = await self.windows_engine.initialize()
                    if success:
                        self.devices = await self.windows_engine.get_devices()
                        self.default_device = await self.windows_engine.get_default_device()
            elif self.system == "darwin":
                if self.macos_engine:
                    success = await self.macos_engine.initialize()
                    if success:
                        self.devices = await self.macos_engine.get_devices()
                        self.default_device = await self.macos_engine.get_default_device()
            
            self.is_initialized = True
            logger.info(f"Audio engine initialized for {self.system}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize audio engine: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the audio engine"""
        try:
            if self.system == "linux" and self.linux_engine:
                await self.linux_engine.shutdown()
            elif self.system == "windows" and self.windows_engine:
                await self.windows_engine.shutdown()
            elif self.system == "darwin" and self.macos_engine:
                await self.macos_engine.shutdown()
            
            self.is_initialized = False
            logger.info("Audio engine shutdown")
            return True
            
        except Exception as e:
            logger.error(f"Error shutting down audio engine: {e}")
            return False
    
    async def get_devices(self) -> List[AudioDevice]:
        """Get available audio devices"""
        if self.system == "linux" and self.linux_engine:
            return await self.linux_engine.get_devices()
        elif self.system == "windows" and self.windows_engine:
            return await self.windows_engine.get_devices()
        elif self.system == "darwin" and self.macos_engine:
            return await self.macos_engine.get_devices()
        
        return list(self.devices.values())
    
    async def set_default_device(self, device_id: str) -> bool:
        """Set default audio device"""
        if device_id in self.devices:
            self.default_device = self.devices[device_id]
            
            if self.system == "linux" and self.linux_engine:
                return await self.linux_engine.set_default_device(device_id)
            elif self.system == "windows" and self.windows_engine:
                return await self.windows_engine.set_default_device(device_id)
            elif self.system == "darwin" and self.macos_engine:
                return await self.macos_engine.set_default_device(device_id)
            
            return True
        
        return False
    
    async def get_volume(self, device_id: Optional[str] = None) -> float:
        """Get device volume"""
        if self.system == "linux" and self.linux_engine:
            return await self.linux_engine.get_volume(device_id)
        elif self.system == "windows" and self.windows_engine:
            return await self.windows_engine.get_volume(device_id)
        elif self.system == "darwin" and self.macos_engine:
            return await self.macos_engine.get_volume(device_id)
        
        return 0.5  # Default volume
    
    async def set_volume(self, volume: float, device_id: Optional[str] = None) -> bool:
        """Set device volume"""
        if self.system == "linux" and self.linux_engine:
            return await self.linux_engine.set_volume(volume, device_id)
        elif self.system == "windows" and self.windows_engine:
            return await self.windows_engine.set_volume(volume, device_id)
        elif self.system == "darwin" and self.macos_engine:
            return await self.macos_engine.set_volume(volume, device_id)
        
        return False
    
    async def mute(self, device_id: Optional[str] = None) -> bool:
        """Mute device"""
        if self.system == "linux" and self.linux_engine:
            return await self.linux_engine.mute(device_id)
        elif self.system == "windows" and self.windows_engine:
            return await self.windows_engine.mute(device_id)
        elif self.system == "darwin" and self.macos_engine:
            return await self.macos_engine.mute(device_id)
        
        return False
    
    async def unmute(self, device_id: Optional[str] = None) -> bool:
        """Unmute device"""
        if self.system == "linux" and self.linux_engine:
            return await self.linux_engine.unmute(device_id)
        elif self.system == "windows" and self.windows_engine:
            return await self.windows_engine.unmute(device_id)
        elif self.system == "darwin" and self.macos_engine:
            return await self.macos_engine.unmute(device_id)
        
        return False


class LinuxAudioEngine(AudioEngine):
    """Linux audio engine using PipeWire/ALSA"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.devices: Dict[str, AudioDevice] = {}
        self.default_device: Optional[AudioDevice] = None
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize Linux audio engine"""
        try:
            # Check for PipeWire first, then ALSA
            if await self._check_pipewire():
                await self._initialize_pipewire()
            elif await self._check_alsa():
                await self._initialize_alsa()
            else:
                logger.warning("No audio system found (PipeWire or ALSA)")
                return False
            
            self.is_initialized = True
            logger.info("Linux audio engine initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Linux audio engine: {e}")
            return False
    
    async def _check_pipewire(self) -> bool:
        """Check if PipeWire is available"""
        try:
            result = await asyncio.create_subprocess_exec(
                "pw-cli", "info", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    async def _check_alsa(self) -> bool:
        """Check if ALSA is available"""
        try:
            result = await asyncio.create_subprocess_exec(
                "aplay", "-l",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    async def _initialize_pipewire(self):
        """Initialize PipeWire audio system"""
        try:
            # Get PipeWire devices
            result = await asyncio.create_subprocess_exec(
                "pw-cli", "list-objects", "Node",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                await self._parse_pipewire_devices(stdout.decode())
            
        except Exception as e:
            logger.error(f"Error initializing PipeWire: {e}")
    
    async def _initialize_alsa(self):
        """Initialize ALSA audio system"""
        try:
            # Get ALSA devices
            result = await asyncio.create_subprocess_exec(
                "aplay", "-l",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                await self._parse_alsa_devices(stdout.decode())
            
        except Exception as e:
            logger.error(f"Error initializing ALSA: {e}")
    
    async def _parse_pipewire_devices(self, output: str):
        """Parse PipeWire device output"""
        try:
            # Parse PipeWire JSON output
            import json
            
            try:
                data = json.loads(output)
                if isinstance(data, dict) and "objects" in data:
                    objects = data["objects"]
                else:
                    objects = [data] if isinstance(data, dict) else data
            except json.JSONDecodeError:
                # Fallback to text parsing
                objects = []
                lines = output.split('\n')
                for line in lines:
                    if "audio" in line.lower() and "sink" in line.lower():
                        objects.append({"type": "Node", "info": {"props": {"node.name": line.strip()}}})
            
            device_id = 0
            
            for obj in objects:
                if obj.get("type") == "Node":
                    info = obj.get("info", {})
                    props = info.get("props", {})
                    
                    # Extract device information
                    name = props.get("node.name", f"PipeWire Device {device_id}")
                    description = props.get("node.description", name)
                    device_type = self._determine_device_type(name, description)
                    
                    # Get audio properties
                    sample_rate = int(props.get("audio.rate", "44100"))
                    channels = int(props.get("audio.channels", "2"))
                    bit_depth = int(props.get("audio.format", "16"))
                    
                    device = AudioDevice(
                        id=f"pipewire_{device_id}",
                        name=description,
                        type=device_type,
                        is_default=device_id == 0,
                        sample_rate=sample_rate,
                        channels=channels,
                        bit_depth=bit_depth,
                        properties={
                            "node_name": name,
                            "node_id": info.get("id"),
                            "media_class": props.get("media.class"),
                            "device_class": props.get("device.class"),
                            "device_name": props.get("device.name"),
                            "device_description": props.get("device.description")
                        }
                    )
                    self.devices[device.id] = device
                    device_id += 1
            
            if self.devices:
                self.default_device = list(self.devices.values())[0]
                
        except Exception as e:
            logger.error(f"Error parsing PipeWire devices: {e}")
            # Fallback to basic device creation
            device = AudioDevice(
                id="pipewire_default",
                name="PipeWire Default Device",
                type=AudioDeviceType.SPEAKERS,
                is_default=True,
                sample_rate=44100,
                channels=2,
                bit_depth=16
            )
            self.devices[device.id] = device
            self.default_device = device
    
    async def _parse_alsa_devices(self, output: str):
        """Parse ALSA device output"""
        try:
            lines = output.split('\n')
            device_id = 0
            
            for line in lines:
                if "card" in line and ":" in line:
                    # Extract device information
                    parts = line.split(":")
                    if len(parts) > 1:
                        name = parts[1].strip()
                        device_type = self._determine_device_type(name, name)
                        
                        # Try to get more detailed info
                        card_info = await self._get_alsa_card_info(device_id)
                        
                        device = AudioDevice(
                            id=f"alsa_{device_id}",
                            name=name,
                            type=device_type,
                            is_default=device_id == 0,
                            sample_rate=card_info.get("sample_rate", 44100),
                            channels=card_info.get("channels", 2),
                            bit_depth=card_info.get("bit_depth", 16),
                            properties={
                                "card_id": device_id,
                                "card_name": name,
                                "driver": card_info.get("driver"),
                                "mixer_name": card_info.get("mixer_name"),
                                "components": card_info.get("components", [])
                            }
                        )
                        self.devices[device.id] = device
                        device_id += 1
            
            if self.devices:
                self.default_device = list(self.devices.values())[0]
                
        except Exception as e:
            logger.error(f"Error parsing ALSA devices: {e}")
            # Fallback to basic device creation
            device = AudioDevice(
                id="alsa_default",
                name="ALSA Default Device",
                type=AudioDeviceType.SPEAKERS,
                is_default=True,
                sample_rate=44100,
                channels=2,
                bit_depth=16
            )
            self.devices[device.id] = device
            self.default_device = device
    
    def _determine_device_type(self, name: str, description: str) -> AudioDeviceType:
        """Determine device type from name and description"""
        name_lower = name.lower()
        desc_lower = description.lower()
        
        # Check for specific device types
        if any(keyword in name_lower or keyword in desc_lower for keyword in ["headphone", "headset"]):
            return AudioDeviceType.HEADPHONES
        elif any(keyword in name_lower or keyword in desc_lower for keyword in ["bluetooth", "bt"]):
            return AudioDeviceType.BLUETOOTH
        elif any(keyword in name_lower or keyword in desc_lower for keyword in ["usb"]):
            return AudioDeviceType.USB
        elif any(keyword in name_lower or keyword in desc_lower for keyword in ["hdmi"]):
            return AudioDeviceType.HDMI
        elif any(keyword in name_lower or keyword in desc_lower for keyword in ["analog", "line"]):
            return AudioDeviceType.ANALOG
        elif any(keyword in name_lower or keyword in desc_lower for keyword in ["digital", "spdif"]):
            return AudioDeviceType.DIGITAL
        else:
            return AudioDeviceType.SPEAKERS
    
    async def _get_alsa_card_info(self, card_id: int) -> Dict[str, Any]:
        """Get detailed ALSA card information"""
        try:
            # Get card info using aplay
            result = await asyncio.create_subprocess_exec(
                "aplay", "-l", f"card{card_id}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode()
                # Parse card information
                info = {
                    "sample_rate": 44100,
                    "channels": 2,
                    "bit_depth": 16,
                    "driver": "unknown",
                    "mixer_name": f"card{card_id}",
                    "components": []
                }
                
                # Extract driver information
                for line in output.split('\n'):
                    if "card" in line and ":" in line:
                        parts = line.split(":")
                        if len(parts) > 2:
                            driver_info = parts[2].strip()
                            if "[" in driver_info and "]" in driver_info:
                                driver = driver_info.split("[")[1].split("]")[0]
                                info["driver"] = driver
                
                return info
            
        except Exception as e:
            logger.debug(f"Could not get ALSA card info for card {card_id}: {e}")
        
        # Return default info
        return {
            "sample_rate": 44100,
            "channels": 2,
            "bit_depth": 16,
            "driver": "unknown",
            "mixer_name": f"card{card_id}",
            "components": []
        }
    
    async def shutdown(self) -> bool:
        """Shutdown Linux audio engine"""
        self.is_initialized = False
        return True
    
    async def get_devices(self) -> List[AudioDevice]:
        """Get available audio devices"""
        return list(self.devices.values())
    
    async def get_default_device(self) -> Optional[AudioDevice]:
        """Get default audio device"""
        return self.default_device
    
    async def set_default_device(self, device_id: str) -> bool:
        """Set default audio device"""
        if device_id in self.devices:
            self.default_device = self.devices[device_id]
            return True
        return False
    
    async def get_volume(self, device_id: Optional[str] = None) -> float:
        """Get device volume using amixer"""
        try:
            device = self.devices.get(device_id) if device_id else self.default_device
            if not device:
                return 0.5
            
            # Use amixer to get volume
            result = await asyncio.create_subprocess_exec(
                "amixer", "get", "Master",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode()
                # Parse volume percentage from amixer output
                for line in output.split('\n'):
                    if '[' in line and '%' in line:
                        # Extract percentage
                        start = line.find('[') + 1
                        end = line.find('%')
                        if start > 0 and end > start:
                            volume_str = line[start:end]
                            try:
                                volume = float(volume_str) / 100.0
                                return max(0.0, min(1.0, volume))
                            except ValueError:
                                pass
            
            return 0.5
            
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            return 0.5
    
    async def set_volume(self, volume: float, device_id: Optional[str] = None) -> bool:
        """Set device volume using amixer"""
        try:
            device = self.devices.get(device_id) if device_id else self.default_device
            if not device:
                return False
            
            # Convert to percentage
            volume_percent = int(volume * 100)
            volume_percent = max(0, min(100, volume_percent))
            
            # Use amixer to set volume
            result = await asyncio.create_subprocess_exec(
                "amixer", "set", "Master", f"{volume_percent}%",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                device.volume = volume
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False
    
    async def mute(self, device_id: Optional[str] = None) -> bool:
        """Mute device using amixer"""
        try:
            device = self.devices.get(device_id) if device_id else self.default_device
            if not device:
                return False
            
            result = await asyncio.create_subprocess_exec(
                "amixer", "set", "Master", "mute",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error muting device: {e}")
            return False
    
    async def unmute(self, device_id: Optional[str] = None) -> bool:
        """Unmute device using amixer"""
        try:
            device = self.devices.get(device_id) if device_id else self.default_device
            if not device:
                return False
            
            result = await asyncio.create_subprocess_exec(
                "amixer", "set", "Master", "unmute",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error unmuting device: {e}")
            return False


class WindowsAudioEngine(AudioEngine):
    """Windows audio engine using WASAPI"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.devices: Dict[str, AudioDevice] = {}
        self.default_device: Optional[AudioDevice] = None
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize Windows audio engine"""
        try:
            # Use PowerShell to get audio devices
            await self._get_windows_devices()
            
            self.is_initialized = True
            logger.info("Windows audio engine initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Windows audio engine: {e}")
            return False
    
    async def _get_windows_devices(self):
        """Get Windows audio devices using PowerShell and WASAPI"""
        try:
            # Enhanced PowerShell script to get audio devices with WASAPI info
            ps_script = """
            Add-Type -TypeDefinition @"
            using System;
            using System.Runtime.InteropServices;
            using System.Collections.Generic;
            
            [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
            public class MMDeviceEnumerator { }
            
            [ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            public interface IMMDeviceEnumerator {
                int NotNeeded();
                int GetDefaultAudioEndpoint(int dataFlow, int role, out IntPtr ppDevice);
                int EnumAudioEndpoints(int dataFlow, int stateMask, out IntPtr ppDevices);
                int GetDevice(string pwstrId, out IntPtr ppDevice);
                int RegisterEndpointNotificationCallback(IntPtr pClient);
                int UnregisterEndpointNotificationCallback(IntPtr pClient);
            }
            
            [ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            public interface IMMDevice {
                int Activate(ref Guid iid, int dwClsCtx, IntPtr pActivationParams, out IntPtr ppInterface);
                int OpenPropertyStore(int stgmAccess, out IntPtr ppProperties);
                int GetId(out IntPtr ppstrId);
                int GetState(out int pdwState);
            }
            
            [ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            public interface IPropertyStore {
                int GetCount(out int cProps);
                int GetAt(int iProp, out PropertyKey pkey);
                int GetValue(ref PropertyKey key, out PropVariant pv);
                int SetValue(ref PropertyKey key, ref PropVariant propvar);
                int Commit();
            }
            
            [StructLayout(LayoutKind.Sequential)]
            public struct PropertyKey {
                public Guid fmtid;
                public int pid;
            }
            
            [StructLayout(LayoutKind.Sequential)]
            public struct PropVariant {
                public short vt;
                public short wReserved1;
                public short wReserved2;
                public short wReserved3;
                public IntPtr ptr;
            }
            "@
            
            $e = New-Object -ComObject MMDeviceEnumerator
            $devices = $e.EnumAudioEndpoints(0, 1)  # eRender, DEVICE_STATE_ACTIVE
            
            $deviceList = @()
            $deviceCount = 0
            
            do {
                $device = $devices.Item($deviceCount)
                if ($device -eq $null) { break }
                
                $deviceId = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($device.GetId())
                $deviceState = $device.GetState()
                
                $props = $device.OpenPropertyStore(0)  # STGM_READ
                $deviceName = "Unknown Device"
                $deviceDesc = "Unknown Description"
                
                try {
                    $nameKey = New-Object -TypeName PropertyKey
                    $nameKey.fmtid = [Guid]::Parse("A45C254E-DF1C-4EFD-8020-67D146A850E0")
                    $nameKey.pid = 2  # PKEY_Device_FriendlyName
                    
                    $nameVar = New-Object -TypeName PropVariant
                    $props.GetValue([ref]$nameKey, [ref]$nameVar)
                    $deviceName = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($nameVar.ptr)
                } catch { }
                
                $deviceList += @{
                    Id = $deviceId
                    Name = $deviceName
                    State = $deviceState
                    Index = $deviceCount
                }
                
                $deviceCount++
            } while ($true)
            
            $deviceList | ConvertTo-Json
            """
            
            result = await asyncio.create_subprocess_exec(
                "powershell", "-Command", ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                try:
                    devices_data = json.loads(stdout.decode())
                    if isinstance(devices_data, list):
                        for device_data in devices_data:
                            device_type = self._determine_device_type(
                                device_data.get("Name", ""), 
                                device_data.get("Name", "")
                            )
                            
                            device = AudioDevice(
                                id=f"windows_{device_data.get('Index', 0)}",
                                name=device_data.get("Name", f"Windows Audio Device {device_data.get('Index', 0)}"),
                                type=device_type,
                                is_default=device_data.get("Index", 0) == 0,
                                sample_rate=44100,
                                channels=2,
                                bit_depth=16,
                                properties={
                                    "device_id": device_data.get("Id"),
                                    "state": device_data.get("State"),
                                    "index": device_data.get("Index"),
                                    "wasapi": True
                                }
                            )
                            self.devices[device.id] = device
                except json.JSONDecodeError:
                    # Fallback: create default device
                    device = AudioDevice(
                        id="windows_default",
                        name="Windows Default Audio Device",
                        type=AudioDeviceType.SPEAKERS,
                        is_default=True,
                        sample_rate=44100,
                        channels=2,
                        bit_depth=16,
                        properties={"wasapi": True}
                    )
                    self.devices[device.id] = device
            else:
                # Fallback to basic WMI query
                await self._get_windows_devices_fallback()
            
            if self.devices:
                self.default_device = list(self.devices.values())[0]
            
        except Exception as e:
            logger.error(f"Error getting Windows devices: {e}")
            await self._get_windows_devices_fallback()
    
    async def _get_windows_devices_fallback(self):
        """Fallback method to get Windows devices using WMI"""
        try:
            ps_script = """
            Get-WmiObject -Class Win32_SoundDevice | Select-Object Name, DeviceID | ConvertTo-Json
            """
            
            result = await asyncio.create_subprocess_exec(
                "powershell", "-Command", ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                try:
                    devices_data = json.loads(stdout.decode())
                    if isinstance(devices_data, list):
                        for i, device_data in enumerate(devices_data):
                            device_type = self._determine_device_type(
                                device_data.get("Name", ""), 
                                device_data.get("Name", "")
                            )
                            
                            device = AudioDevice(
                                id=f"windows_{i}",
                                name=device_data.get("Name", f"Windows Audio Device {i}"),
                                type=device_type,
                                is_default=i == 0,
                                sample_rate=44100,
                                channels=2,
                                bit_depth=16,
                                properties={
                                    "device_id": device_data.get("DeviceID"),
                                    "wmi": True
                                }
                            )
                            self.devices[device.id] = device
                except json.JSONDecodeError:
                    pass
            
            # Always create at least one default device
            if not self.devices:
                device = AudioDevice(
                    id="windows_default",
                    name="Windows Default Audio Device",
                    type=AudioDeviceType.SPEAKERS,
                    is_default=True,
                    sample_rate=44100,
                    channels=2,
                    bit_depth=16,
                    properties={"fallback": True}
                )
                self.devices[device.id] = device
            
        except Exception as e:
            logger.error(f"Error in Windows fallback device detection: {e}")
    
    async def shutdown(self) -> bool:
        """Shutdown Windows audio engine"""
        self.is_initialized = False
        return True
    
    async def get_devices(self) -> List[AudioDevice]:
        """Get available audio devices"""
        return list(self.devices.values())
    
    async def get_default_device(self) -> Optional[AudioDevice]:
        """Get default audio device"""
        return self.default_device
    
    async def set_default_device(self, device_id: str) -> bool:
        """Set default audio device"""
        if device_id in self.devices:
            self.default_device = self.devices[device_id]
            return True
        return False
    
    async def get_volume(self, device_id: Optional[str] = None) -> float:
        """Get device volume using PowerShell"""
        try:
            # PowerShell script to get volume
            ps_script = """
            [audio]::Volume * 100
            """
            
            result = await asyncio.create_subprocess_exec(
                "powershell", "-Command", ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                try:
                    volume_percent = float(stdout.decode().strip())
                    return max(0.0, min(1.0, volume_percent / 100.0))
                except ValueError:
                    pass
            
            return 0.5
            
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            return 0.5
    
    async def set_volume(self, volume: float, device_id: Optional[str] = None) -> bool:
        """Set device volume using PowerShell"""
        try:
            volume_percent = int(volume * 100)
            volume_percent = max(0, min(100, volume_percent))
            
            # PowerShell script to set volume
            ps_script = f"""
            [audio]::Volume = {volume_percent / 100.0}
            """
            
            result = await asyncio.create_subprocess_exec(
                "powershell", "-Command", ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False
    
    async def mute(self, device_id: Optional[str] = None) -> bool:
        """Mute device using PowerShell"""
        try:
            # PowerShell script to mute
            ps_script = """
            [audio]::Mute = $true
            """
            
            result = await asyncio.create_subprocess_exec(
                "powershell", "-Command", ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error muting device: {e}")
            return False
    
    async def unmute(self, device_id: Optional[str] = None) -> bool:
        """Unmute device using PowerShell"""
        try:
            # PowerShell script to unmute
            ps_script = """
            [audio]::Mute = $false
            """
            
            result = await asyncio.create_subprocess_exec(
                "powershell", "-Command", ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error unmuting device: {e}")
            return False


class MacOSAudioEngine(AudioEngine):
    """macOS audio engine using Core Audio"""
    
    def __init__(self, config: AudioConfig):
        self.config = config
        self.devices: Dict[str, AudioDevice] = {}
        self.default_device: Optional[AudioDevice] = None
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize macOS audio engine"""
        try:
            # Use system_profiler to get audio devices
            await self._get_macos_devices()
            
            self.is_initialized = True
            logger.info("macOS audio engine initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize macOS audio engine: {e}")
            return False
    
    async def _get_macos_devices(self):
        """Get macOS audio devices using Core Audio and system_profiler"""
        try:
            # Try Core Audio approach first
            await self._get_macos_core_audio_devices()
            
            # If no devices found, try system_profiler
            if not self.devices:
                await self._get_macos_system_profiler_devices()
            
            # Always ensure we have at least one device
            if not self.devices:
                device = AudioDevice(
                    id="macos_default",
                    name="macOS Default Audio Device",
                    type=AudioDeviceType.SPEAKERS,
                    is_default=True,
                    sample_rate=44100,
                    channels=2,
                    bit_depth=16,
                    properties={"fallback": True}
                )
                self.devices[device.id] = device
            
            if self.devices:
                self.default_device = list(self.devices.values())[0]
            
        except Exception as e:
            logger.error(f"Error getting macOS devices: {e}")
    
    async def _get_macos_core_audio_devices(self):
        """Get macOS devices using Core Audio via AppleScript"""
        try:
            # AppleScript to get Core Audio devices
            script = """
            tell application "System Events"
                set deviceList to {}
                try
                    set audioDevices to (do shell script "system_profiler SPAudioDataType -json")
                    set deviceData to (do shell script "echo '" & audioDevices & "' | python3 -c \"
import json, sys
data = json.load(sys.stdin)
devices = data.get('SPAudioDataType', [])
for i, device in enumerate(devices):
    print(f'{i}|{device.get(\\\"_name\\\", \\\"Unknown\\\")}|{device.get(\\\"coreaudio_default_audio_output_device\\\", \\\"false\\\")}')
\"")
                    
                    repeat with line in paragraphs of deviceData
                        if line is not \"\" then
                            set AppleScript's text item delimiters to \"|\"
                            set deviceInfo to text items of line
                            set deviceIndex to item 1 of deviceInfo
                            set deviceName to item 2 of deviceInfo
                            set isDefault to item 3 of deviceInfo
                            
                            set deviceInfo to {deviceIndex, deviceName, isDefault}
                            set end of deviceList to deviceInfo
                        end if
                    end repeat
                end try
            end tell
            
            return deviceList
            """
            
            result = await asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                output = stdout.decode().strip()
                if output:
                    lines = output.split('\n')
                    for line in lines:
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 3:
                                device_index = int(parts[0])
                                device_name = parts[1]
                                is_default = parts[2].lower() == 'true'
                                
                                device_type = self._determine_device_type(device_name, device_name)
                                
                                device = AudioDevice(
                                    id=f"macos_{device_index}",
                                    name=device_name,
                                    type=device_type,
                                    is_default=is_default,
                                    sample_rate=44100,
                                    channels=2,
                                    bit_depth=16,
                                    properties={
                                        "core_audio": True,
                                        "device_index": device_index
                                    }
                                )
                                self.devices[device.id] = device
                                
        except Exception as e:
            logger.debug(f"Core Audio device detection failed: {e}")
    
    async def _get_macos_system_profiler_devices(self):
        """Get macOS devices using system_profiler"""
        try:
            result = await asyncio.create_subprocess_exec(
                "system_profiler", "SPAudioDataType", "-json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                try:
                    data = json.loads(stdout.decode())
                    audio_items = data.get("SPAudioDataType", [])
                    
                    for i, item in enumerate(audio_items):
                        device_name = item.get("_name", f"macOS Audio Device {i}")
                        device_type = self._determine_device_type(device_name, device_name)
                        is_default = item.get("coreaudio_default_audio_output_device", "false").lower() == "true"
                        
                        device = AudioDevice(
                            id=f"macos_{i}",
                            name=device_name,
                            type=device_type,
                            is_default=is_default or i == 0,
                            sample_rate=44100,
                            channels=2,
                            bit_depth=16,
                            properties={
                                "system_profiler": True,
                                "device_index": i,
                                "coreaudio_default": is_default
                            }
                        )
                        self.devices[device.id] = device
                
                except json.JSONDecodeError:
                    # Fallback: create default device
                    device = AudioDevice(
                        id="macos_default",
                        name="macOS Default Audio Device",
                        type=AudioDeviceType.SPEAKERS,
                        is_default=True,
                        sample_rate=44100,
                        channels=2,
                        bit_depth=16,
                        properties={"system_profiler_fallback": True}
                    )
                    self.devices[device.id] = device
            
        except Exception as e:
            logger.debug(f"System profiler device detection failed: {e}")
    
    async def shutdown(self) -> bool:
        """Shutdown macOS audio engine"""
        self.is_initialized = False
        return True
    
    async def get_devices(self) -> List[AudioDevice]:
        """Get available audio devices"""
        return list(self.devices.values())
    
    async def get_default_device(self) -> Optional[AudioDevice]:
        """Get default audio device"""
        return self.default_device
    
    async def set_default_device(self, device_id: str) -> bool:
        """Set default audio device"""
        if device_id in self.devices:
            self.default_device = self.devices[device_id]
            return True
        return False
    
    async def get_volume(self, device_id: Optional[str] = None) -> float:
        """Get device volume using osascript"""
        try:
            # AppleScript to get volume
            script = "output volume of (get volume settings)"
            
            result = await asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                try:
                    volume_percent = float(stdout.decode().strip())
                    return max(0.0, min(1.0, volume_percent / 100.0))
                except ValueError:
                    pass
            
            return 0.5
            
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            return 0.5
    
    async def set_volume(self, volume: float, device_id: Optional[str] = None) -> bool:
        """Set device volume using osascript"""
        try:
            volume_percent = int(volume * 100)
            volume_percent = max(0, min(100, volume_percent))
            
            # AppleScript to set volume
            script = f"set volume output volume {volume_percent}"
            
            result = await asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False
    
    async def mute(self, device_id: Optional[str] = None) -> bool:
        """Mute device using osascript"""
        try:
            # AppleScript to mute
            script = "set volume with output muted"
            
            result = await asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error muting device: {e}")
            return False
    
    async def unmute(self, device_id: Optional[str] = None) -> bool:
        """Unmute device using osascript"""
        try:
            # AppleScript to unmute
            script = "set volume without output muted"
            
            result = await asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error unmuting device: {e}")
            return False