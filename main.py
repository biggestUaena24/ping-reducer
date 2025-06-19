import subprocess
import sys
from ping_monitor import PingMonitor

if __name__ == "__main__":
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"]) # Make sure that the user had requests package
    ping_monitor = PingMonitor()
    ping_monitor.start_monitor(interval=2)