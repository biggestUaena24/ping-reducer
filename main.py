import subprocess
import sys
import threading
import time
import importlib.util

def check_and_install_packages():
    required_packages = {
        'requests': 'requests',
        'pyuac': 'pyuac', 
        'pywin32': 'pywin32'
    }
    
    missing_packages = []
    
    for package_name, pip_name in required_packages.items():
        if importlib.util.find_spec(package_name) is None:
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages)
            print("✅ All packages installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            sys.exit(1)
    
    try:
        import pyuac
        import requests
        return pyuac
    except ImportError as e:
        print(f"❌ Failed to import packages after installation: {e}")
        sys.exit(1)

def qos_worker():
    print("Initializing QoS optimizations in background...")
    try:
        from qos_policy import QosPolicy
        qos = QosPolicy()
        success = qos.enable_qos()
        
        if success:
            print("QoS optimizations applied successfully")
        else:
            print("Some QoS optimizations failed - check output above")
            
    except Exception as e:
        print(f"QoS initialization failed: {e}")

def main():
    print("Starting League of Legends Network Optimizer")
    print("=" * 50)
    
    qos_thread = threading.Thread(
        target=qos_worker,
        daemon=True,
        name="QoS-Worker"
    )
    qos_thread.start()
    
    time.sleep(1)
    
    print("Starting ping monitor in main thread...")
    try:
        from ping_monitor import PingMonitor
        ping_monitor = PingMonitor()
        ping_monitor.start_monitor(interval=2)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Ping monitor failed: {e}")

if __name__ == "__main__":
    try:
        pyuac = check_and_install_packages()
        if not pyuac.isUserAdmin():
            print("Administrator privileges required. Re-launching as admin...")
            pyuac.runAsAdmin()
        else:
            print("Running with administrator privileges")
            main()
            
    except Exception as e:
        print(f"❌ Application failed to start: {e}")
        input("Press Enter to exit...")
        sys.exit(1)