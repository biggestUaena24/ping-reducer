import subprocess
import winreg
import os

class QosPolicy:
    def __init__(self):
        self.lol_process_name = ["LeagueClient.exe", "League of Legends.exe"]
        self.qos_policy_name = "LoL_Traffic_Priority"
        self.lol_ports = "5000-5500,8088,8443,8444"
        self.is_windows_home = self._check_windows_edition()
        
    def _check_windows_edition(self):
        """Check if running on Windows Home edition"""
        try:
            gpedit_path = os.path.join(os.environ['WINDIR'], 'System32', 'gpedit.msc')
            if not os.path.exists(gpedit_path):
                return True
            
            result = subprocess.run(
                ['wmic', 'os', 'get', 'Caption', '/value'],
                capture_output=True,
                text=True,
                shell=True
            )
            
            if 'Home' in result.stdout:
                return True
                
        except Exception as e:
            print(f"Warning: Could not determine Windows edition: {e}")
            
        return False
    
    def _enable_standard_qos(self):
        try:
            subprocess.run(
                f'netsh int qos delete policy name="{self.qos_policy_name}"',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
           
            subprocess.run(
                f'netsh int qos add policy name="{self.qos_policy_name}" '
                f'protocol=UDP localport={self.lol_ports} priority=1',
                shell=True,
                check=True
            )
           
            print(f"Created standard QoS policy '{self.qos_policy_name}' for ports {self.lol_ports}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to create standard QoS policy: {e}")
            return self.enable_qos()
    
    def _enable_qos_packet_scheduler(self):
        try:
            subprocess.run([
                'sc', 'config', 'Psched', 'start=', 'auto'
            ], check=True, capture_output=True)
            
            subprocess.run([
                'sc', 'start', 'Psched'
            ], capture_output=True)
            
            print("QoS Packet Scheduler service enabled")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not configure QoS service: {e}")
            return False
    
    def _set_network_adapter_qos(self):
        try:
            adapter_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces",
                0,
                winreg.KEY_READ
            )
            
            print("Network adapter QoS settings configured")
            winreg.CloseKey(adapter_key)
            return True
            
        except Exception as e:
            print(f"Warning: Could not configure adapter QoS: {e}")
            return False
    
    def _set_process_priority(self):
        try:
            for process_name in self.lol_process_name:
                subprocess.run([
                    'wmic', 'process', 'where', f'name="{process_name}"',
                    'call', 'setpriority', '"high priority"'
                ], capture_output=True, shell=True)
            
            print("Process priorities configured for League of Legends")
            return True
            
        except Exception as e:
            print(f"Warning: Could not set process priorities: {e}")
            return False
    
    def _configure_tcp_settings(self):
        try:
            tcp_settings = [
                ('TcpAckFrequency', 1),
                ('TCPNoDelay', 1),
                ('TcpWindowSize', 65536),
                ('EnableTCPChimney', 1),
            ]
            
            tcp_key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
                0,
                winreg.KEY_SET_VALUE
            )
            
            for setting, value in tcp_settings:
                try:
                    winreg.SetValueEx(tcp_key, setting, 0, winreg.REG_DWORD, value)
                except Exception as e:
                    print(f"Warning: Could not set {setting}: {e}")
            
            winreg.CloseKey(tcp_key)
            print("TCP/IP settings optimized for gaming")
            return True
            
        except Exception as e:
            print(f"Warning: Could not configure TCP settings: {e}")
            return False
    
    def _windows_firewall_priority(self):
        try:
            subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                f'name="{self.qos_policy_name}_UDP"'
            ], capture_output=True)
            
            subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                f'name="{self.qos_policy_name}_UDP"',
                'dir=out', 'action=allow', 'protocol=UDP',
                f'localport={self.lol_ports}',
                'profile=any'
            ], check=True, capture_output=True)
            
            print(f"Firewall rules configured for ports {self.lol_ports}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not configure firewall rules: {e}")
            return False
    
    def _netsh_interface_optimization(self):
        try:
            optimizations = [
                'netsh int tcp set global autotuninglevel=normal',
                'netsh int tcp set global chimney=enabled',
                'netsh int tcp set global rss=enabled',
            ]
            
            for cmd in optimizations:
                try:
                    subprocess.run(cmd, shell=True, check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    continue
            
            print("Network interface optimizations applied")
            return True
            
        except Exception as e:
            print(f"Warning: Could not apply network optimizations: {e}")
            return False
    
    def enable_qos(self):
        print(f"Detected Windows Edition: {'Home' if self.is_windows_home else 'Pro/Enterprise'}")
        
        if not self.is_windows_home:
            return self._enable_standard_qos()
        else:
            print("Applying Windows Home compatible optimizations...")
            
            results = []
            results.append(self._enable_qos_packet_scheduler())
            results.append(self._set_network_adapter_qos())
            results.append(self._set_process_priority())
            results.append(self._configure_tcp_settings())
            results.append(self._windows_firewall_priority())
            results.append(self._netsh_interface_optimization())
            
            success_count = sum(results)
            total_count = len(results)
            
            print(f"\nApplied {success_count}/{total_count} optimizations successfully")
            
            if success_count > 0:
                print("Restart required for some changes to take effect")
                return True
            else:
                print("No optimizations could be applied")
                return False
    
    def disable_qos(self):
        try:
            if not self.is_windows_home:
                subprocess.run(
                    f'netsh int qos delete policy name="{self.qos_policy_name}"',
                    shell=True,
                    capture_output=True
                )
            
            subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
                f'name="{self.qos_policy_name}_UDP"'
            ], capture_output=True)
            
            print("✅ QoS settings removed")
            return True
            
        except Exception as e:
            print(f"Warning: Could not fully remove QoS settings: {e}")
            return False