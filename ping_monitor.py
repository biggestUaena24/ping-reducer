import time
import concurrent.futures
from datetime import datetime
import subprocess
import sys
import requests

class PingMonitor:
    def __init__(self):
        self.RIOT_ENDPOINTS = [
    "https://clientconfig.rpg.riotgames.com/api/v1/config/public", # Main endpoint being used for consistency
    "https://riot.nl" # Alternative endpoint being used
        ]

    def _http_ping(self, url, timeout=2):
        try:
            start_time = time.perf_counter()
            response = requests.head(
                url,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            latency = (time.perf_counter() - start_time) * 1000
            
            return {
                "url": url,
                "latency": latency,
                "status": response.status_code,
                "success": response.ok
            }
        except (requests.exceptions.Timeout, 
                requests.exceptions.ConnectionError,
                requests.exceptions.TooManyRedirects):
            return {"url": url, "error": "Connection failed"}
        except Exception as e:
            return {"url": url, "error": str(e)}

    def _run_http_ping_tests(self):
        print(f"\n{' League HTTP Ping Test ':=^60}")
        print(f"Testing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self._http_ping, url) for url in self.RIOT_ENDPOINTS]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                
                if 'error' in result:
                    print(f"X {result['url']:50.50} | ERROR: {result['error']}")
                else:
                    print(f"{result['url']:50.50} | {result['latency']:6.1f} ms | HTTP {result['status']}")

    def start_monitor(self, interval=10):
        print("League of Legends HTTP Ping Monitor")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self._run_http_ping_tests()
                print(f"\nNext test in {interval} seconds...\n")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")