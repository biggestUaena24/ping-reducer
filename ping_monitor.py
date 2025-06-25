import time
import concurrent.futures
from datetime import datetime, timedelta
import requests
import statistics
import threading
from collections import deque
import json

class PingMonitor:
    def __init__(self, callback=None):
        self.RIOT_ENDPOINTS = {
            "NA": [
                "https://clientconfig.rpg.riotgames.com/api/v1/config/public",
                "https://riot-geo.pas.si.riotgames.com/pas/v1/service/chat",
                "https://auth.riotgames.com/api/v1/authorization"
            ],
            "EUW": [
                "https://riot.nl",
                "https://euw1.api.riotgames.com",
                "https://europe.api.riotgames.com"
            ],
            "EUNE": [
                "https://eun1.api.riotgames.com",
                "https://europe.api.riotgames.com"
            ],
            "KR": [
                "https://kr.api.riotgames.com",
                "https://asia.api.riotgames.com"
            ],
            "JP": [
                "https://jp1.api.riotgames.com",
                "https://asia.api.riotgames.com"
            ]
        }
        
        self.current_region = "NA"
        self.current_endpoints = self.RIOT_ENDPOINTS[self.current_region]
        
        self.ping_history = deque(maxlen=100)
        self.packet_loss_history = deque(maxlen=20)
        
        self.is_monitoring = False
        self.monitor_thread = None
        self.callback = callback
        
        self.stats = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'average_ping': 0,
            'min_ping': float('inf'),
            'max_ping': 0,
            'packet_loss_rate': 0
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json,text/plain,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache'
        })
        
    def set_region(self, region):
        if region in self.RIOT_ENDPOINTS:
            self.current_region = region
            self.current_endpoints = self.RIOT_ENDPOINTS[region]
            self.log_message(f"Region set to {region}")
            return True
        return False
    
    def get_available_regions(self):
        return list(self.RIOT_ENDPOINTS.keys())
    
    def _http_ping(self, url, timeout=3):
        try:
            start_time = time.perf_counter()
            
            response = self.session.head(url, timeout=timeout)
            
            end_time = time.perf_counter()
            latency = (end_time - start_time) * 1000
            
            if response.ok:
                try:
                    start_time = time.perf_counter()
                    response = self.session.get(url, timeout=timeout, stream=True)
                    next(response.iter_content(chunk_size=1024), None)
                    response.close()
                    end_time = time.perf_counter()
                    latency = (end_time - start_time) * 1000
                except:
                    pass 
            
            return {
                "url": url,
                "latency": round(latency, 1),
                "status": response.status_code,
                "success": response.ok,
                "timestamp": datetime.now()
            }
            
        except requests.exceptions.Timeout:
            return {
                "url": url, 
                "error": "Request timeout", 
                "success": False,
                "timestamp": datetime.now()
            }
        except requests.exceptions.ConnectionError:
            return {
                "url": url, 
                "error": "Connection failed", 
                "success": False,
                "timestamp": datetime.now()
            }
        except requests.exceptions.TooManyRedirects:
            return {
                "url": url, 
                "error": "Too many redirects", 
                "success": False,
                "timestamp": datetime.now()
            }
        except Exception as e:
            return {
                "url": url, 
                "error": f"Unexpected error: {str(e)}", 
                "success": False,
                "timestamp": datetime.now()
            }
    
    def _run_http_ping_tests(self):
        test_results = []
        successful_pings = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.current_endpoints)) as executor:
            future_to_url = {
                executor.submit(self._http_ping, url): url 
                for url in self.current_endpoints
            }
            
            for future in concurrent.futures.as_completed(future_to_url, timeout=10):
                try:
                    result = future.result()
                    test_results.append(result)
                    
                    if result.get('success', False):
                        successful_pings.append(result['latency'])
                        
                except concurrent.futures.TimeoutError:
                    url = future_to_url[future]
                    test_results.append({
                        "url": url,
                        "error": "Future timeout",
                        "success": False,
                        "timestamp": datetime.now()
                    })
        
        self._update_stats(test_results, successful_pings)
        
        if self.callback:
            self.callback(test_results, self.get_current_stats())
        
        return test_results
    
    def _update_stats(self, test_results, successful_pings):
        self.stats['total_tests'] += len(test_results)
        self.stats['successful_tests'] += len(successful_pings)
        self.stats['failed_tests'] += len(test_results) - len(successful_pings)
        
        if successful_pings:
            avg_ping = statistics.mean(successful_pings)
            min_ping = min(successful_pings)
            max_ping = max(successful_pings)
            
            self.ping_history.extend(successful_pings)
            
            if self.ping_history:
                self.stats['average_ping'] = round(statistics.mean(self.ping_history), 1)
                self.stats['min_ping'] = min(self.stats['min_ping'], min_ping)
                self.stats['max_ping'] = max(self.stats['max_ping'], max_ping)
        
        if test_results:
            current_packet_loss = (len(test_results) - len(successful_pings)) / len(test_results) * 100
            self.packet_loss_history.append(current_packet_loss)
            
            if self.packet_loss_history:
                self.stats['packet_loss_rate'] = round(statistics.mean(self.packet_loss_history), 1)
    
    def get_current_stats(self):
        stats = self.stats.copy()
        
        if self.ping_history:
            recent_pings = list(self.ping_history)[-10:]  # Last 10 pings
            stats['recent_average'] = round(statistics.mean(recent_pings), 1)
            
            if len(recent_pings) > 1:
                stats['jitter'] = round(statistics.stdev(recent_pings), 1)
            else:
                stats['jitter'] = 0
        else:
            stats['recent_average'] = 0
            stats['jitter'] = 0
        
        stats['uptime'] = self._get_uptime()
        return stats
    
    def _get_uptime(self):
        if hasattr(self, 'start_time'):
            return str(timedelta(seconds=int(time.time() - self.start_time)))
        return "0:00:00"
    
    def get_ping_history(self, limit=50):
        return list(self.ping_history)[-limit:]
    
    def log_message(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def start_monitor(self, interval=5):
        if self.is_monitoring:
            self.log_message("Monitoring already active")
            return False
        
        self.is_monitoring = True
        self.start_time = time.time()
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
        self.log_message(f"Started monitoring {self.current_region} region with {interval}s interval")
        return True
    
    def stop_monitor(self):
        if not self.is_monitoring:
            return False
        
        self.is_monitoring = False
        self.log_message("Monitoring stopped")
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        
        return True
    
    def _monitor_loop(self, interval):
        self.log_message(f"League of Legends HTTP Ping Monitor ({self.current_region})")
        
        while self.is_monitoring:
            try:
                results = self._run_http_ping_tests()
                
                if not self.callback:
                    self._print_results(results)
                
                for _ in range(int(interval * 10)):
                    if not self.is_monitoring:
                        break
                    time.sleep(0.1)
                    
            except Exception as e:
                self.log_message(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _print_results(self, results):
        print(f"\n{' League HTTP Ping Test ':=^60}")
        print(f"Region: {self.current_region} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        for result in results:
            if result.get('success', False):
                status_color = "✓" if result['latency'] < 100 else "⚠" if result['latency'] < 200 else "✗"
                print(f"{status_color} {result['url'][:45]:45} | {result['latency']:6.1f} ms | HTTP {result['status']}")
            else:
                print(f"✗ {result['url'][:45]:45} | ERROR: {result.get('error', 'Unknown')}")
        
        stats = self.get_current_stats()
        print(f"\nStats: Avg: {stats['recent_average']}ms | Loss: {stats['packet_loss_rate']}% | Jitter: {stats['jitter']}ms")
    
    def run_single_test(self):
        return self._run_http_ping_tests()
    
    def export_stats(self, filename=None):
        if not filename:
            filename = f"ping_stats_{self.current_region}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'region': self.current_region,
            'endpoints': self.current_endpoints,
            'stats': self.get_current_stats(),
            'ping_history': list(self.ping_history),
            'export_time': datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            self.log_message(f"Stats exported to {filename}")
            return filename
        except Exception as e:
            self.log_message(f"Failed to export stats: {e}")
            return None