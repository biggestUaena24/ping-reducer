import subprocess
import sys
import threading
import importlib.util
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import queue

class NetworkOptimizerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("League of Legends Network Optimizer")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        self.log_queue = queue.Queue()
        self.ping_queue = queue.Queue()
        
        self.qos_enabled = tk.BooleanVar()
        self.ping_monitoring = tk.BooleanVar()
        self.current_ping = tk.StringVar(value="-- ms")
        self.packet_loss = tk.StringVar(value="0%")
        
        self.qos_thread = None
        self.ping_thread = None
        self.ping_monitor = None
        
        self.setup_gui()
        self.start_log_processor()
        
    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        title_label = ttk.Label(main_frame, text="League of Legends Network Optimizer", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        status_frame = ttk.LabelFrame(main_frame, text="Network Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        status_frame.columnconfigure(3, weight=1)
        
        ttk.Label(status_frame, text="Current Ping:").grid(row=0, column=0, sticky=tk.W)
        ping_label = ttk.Label(status_frame, textvariable=self.current_ping, 
                              font=('Arial', 12, 'bold'), foreground='green')
        ping_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 20))
        
        ttk.Label(status_frame, text="Packet Loss:").grid(row=0, column=2, sticky=tk.W)
        loss_label = ttk.Label(status_frame, textvariable=self.packet_loss, 
                              font=('Arial', 12, 'bold'), foreground='orange')
        loss_label.grid(row=0, column=3, sticky=tk.W, padx=(10, 0))
        
        stats_frame = ttk.Frame(status_frame)
        stats_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(3, weight=1)
        
        ttk.Label(stats_frame, text="Avg Ping:").grid(row=0, column=0, sticky=tk.W)
        self.avg_ping = tk.StringVar(value="-- ms")
        ttk.Label(stats_frame, textvariable=self.avg_ping, font=('Arial', 10)).grid(row=0, column=1, sticky=tk.W, padx=(10, 20))
        
        ttk.Label(stats_frame, text="Jitter:").grid(row=0, column=2, sticky=tk.W)
        self.jitter = tk.StringVar(value="-- ms")
        ttk.Label(stats_frame, textvariable=self.jitter, font=('Arial', 10)).grid(row=0, column=3, sticky=tk.W, padx=(10, 0))
        
        qos_status_label = ttk.Label(status_frame, text="QoS Status:")
        qos_status_label.grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        
        self.qos_status_indicator = ttk.Label(status_frame, text="Disabled", 
                                            foreground='red', font=('Arial', 10, 'bold'))
        self.qos_status_indicator.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        
        self.qos_button = ttk.Button(control_frame, text="Enable QoS Optimization", 
                                   command=self.toggle_qos, style='Accent.TButton')
        self.qos_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.ping_button = ttk.Button(control_frame, text="Start Ping Monitor", 
                                    command=self.toggle_ping_monitor)
        self.ping_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        advanced_frame = ttk.Frame(control_frame)
        advanced_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        advanced_frame.columnconfigure(1, weight=1)
        advanced_frame.columnconfigure(3, weight=1)
        
        ttk.Label(advanced_frame, text="Ping Interval:").grid(row=0, column=0, sticky=tk.W)
        self.ping_interval = tk.StringVar(value="5")
        interval_spinbox = ttk.Spinbox(advanced_frame, from_=1, to=30, width=10, 
                                     textvariable=self.ping_interval)
        interval_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(10, 20))
        ttk.Label(advanced_frame, text="seconds").grid(row=0, column=2, sticky=tk.W, padx=(5, 20))
        
        ttk.Label(advanced_frame, text="Region:").grid(row=0, column=3, sticky=tk.W)
        self.selected_region = tk.StringVar(value="NA")
        region_combo = ttk.Combobox(advanced_frame, textvariable=self.selected_region, 
                                   values=["NA", "EUW", "EUNE", "KR", "JP"], width=8, state="readonly")
        region_combo.grid(row=0, column=4, sticky=tk.W, padx=(10, 0))
        region_combo.bind('<<ComboboxSelected>>', self.on_region_change)
        
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        button_frame = ttk.Frame(log_frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)
        
        clear_button = ttk.Button(button_frame, text="Clear Log", command=self.clear_log)
        clear_button.grid(row=0, column=0, sticky=tk.W)
        
        export_button = ttk.Button(button_frame, text="Export Stats", command=self.export_stats)
        export_button.grid(row=0, column=1, sticky=tk.E, padx=(10, 0))
        
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def log_message(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        self.log_queue.put(formatted_message)
        
    def start_log_processor(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        self.root.after(100, self.start_log_processor)
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        
    def toggle_qos(self):
        if not self.qos_enabled.get():
            self.enable_qos()
        else:
            self.disable_qos()
            
    def enable_qos(self):
        if self.qos_thread and self.qos_thread.is_alive():
            self.log_message("QoS optimization already in progress", "WARNING")
            return
            
        self.qos_button.config(text="Enabling QoS...", state='disabled')
        self.log_message("Starting QoS optimization...")
        
        self.qos_thread = threading.Thread(target=self.qos_worker, daemon=True)
        self.qos_thread.start()
        
    def qos_worker(self):
        try:
            from qos_policy import QosPolicy
            qos = QosPolicy()
            success = qos.enable_qos()
            
            if success:
                self.root.after(0, self.qos_success)
                self.log_message("QoS optimization applied successfully", "SUCCESS")
            else:
                self.root.after(0, self.qos_failed)
                self.log_message("Some QoS optimizations failed", "ERROR")
                
        except ImportError:
            self.root.after(0, self.qos_failed)
            self.log_message("QoS policy module not found", "ERROR")
        except Exception as e:
            self.root.after(0, self.qos_failed)
            self.log_message(f"QoS initialization failed: {str(e)}", "ERROR")
            
    def qos_success(self):
        self.qos_enabled.set(True)
        self.qos_button.config(text="Disable QoS Optimization", state='normal')
        self.qos_status_indicator.config(text="Enabled", foreground='green')
        self.status_bar.config(text="QoS optimization enabled successfully")
        
    def qos_failed(self):
        self.qos_button.config(text="Enable QoS Optimization", state='normal')
        self.status_bar.config(text="QoS optimization failed")
        
    def disable_qos(self):
        try:
            from qos_policy import QosPolicy
            qos = QosPolicy()
            qos.disable_qos()
            
            self.qos_enabled.set(False)
            self.qos_button.config(text="Enable QoS Optimization")
            self.qos_status_indicator.config(text="Disabled", foreground='red')
            self.log_message("QoS optimization disabled", "INFO")
            self.status_bar.config(text="QoS optimization disabled")
            
        except Exception as e:
            self.log_message(f"Error disabling QoS: {str(e)}", "ERROR")
            
    def toggle_ping_monitor(self):
        if not self.ping_monitoring.get():
            self.start_ping_monitor()
        else:
            self.stop_ping_monitor()
            
    def start_ping_monitor(self):
        if self.ping_thread and self.ping_thread.is_alive():
            self.log_message("Ping monitor already running", "WARNING")
            return
            
        try:
            interval = float(self.ping_interval.get())
            if interval < 1 or interval > 10:
                raise ValueError("Interval must be between 1 and 10 seconds")
        except ValueError as e:
            messagebox.showerror("Invalid Interval", str(e))
            return
            
        self.ping_monitoring.set(True)
        self.ping_button.config(text="Stop Ping Monitor")
        self.log_message(f"Starting ping monitor with {interval}s interval...")
        
        self.ping_thread = threading.Thread(
            target=self.ping_worker, 
            args=(interval,), 
            daemon=True
        )
        self.ping_thread.start()
        
    def ping_worker(self, interval):
        try:
            from ping_monitor import PingMonitor
            
            # Create ping monitor with GUI callback
            self.ping_monitor = PingMonitor(callback=self.ping_callback)
            
            # Start the monitoring
            self.ping_monitor.start_monitor(interval)
            
        except ImportError:
            self.log_message("ping_monitor module not found", "ERROR")
            self.root.after(0, self.ping_monitor_stopped)
        except Exception as e:
            self.log_message(f"Ping monitor error: {str(e)}", "ERROR")
            self.root.after(0, self.ping_monitor_stopped)
            
    def on_region_change(self, event=None):
        if self.ping_monitor:
            new_region = self.selected_region.get()
            if self.ping_monitor.set_region(new_region):
                self.log_message(f"Region changed to {new_region}", "INFO")
            else:
                self.log_message(f"Failed to change region to {new_region}", "ERROR")
        
    def export_stats(self):
        if self.ping_monitor:
            try:
                filename = self.ping_monitor.export_stats()
                if filename:
                    messagebox.showinfo("Export Success", f"Statistics exported to:\n{filename}")
                else:
                    messagebox.showerror("Export Failed", "Failed to export statistics")
            except Exception as e:
                messagebox.showerror("Export Error", f"Error exporting stats: {str(e)}")
        else:
            messagebox.showwarning("No Data", "No ping monitor data available to export")
    
    def ping_callback(self, test_results, stats):
        try:
            successful_results = [r for r in test_results if r.get('success', False)]
            
            if successful_results:
                best_ping = min(r['latency'] for r in successful_results)
                self.root.after(0, lambda: self.update_ping_display(str(best_ping)))
                
                avg_ping = sum(r['latency'] for r in successful_results) / len(successful_results)
                self.log_message(f"Ping: {avg_ping:.1f}ms avg, {best_ping:.1f}ms best")
            else:
                self.log_message("All ping tests failed", "WARNING")
                self.root.after(0, lambda: self.update_ping_display("Timeout"))
            
            total_tests = len(test_results)
            failed_tests = len([r for r in test_results if not r.get('success', False)])
            loss_percent = (failed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            self.root.after(0, lambda: self.update_packet_loss(loss_percent))
            
            self.root.after(0, lambda: self.update_stats_display(stats))
            
            for result in test_results:
                if not result.get('success', False):
                    self.log_message(f"Failed to ping {result['url']}: {result.get('error', 'Unknown error')}", "WARNING")
                    
        except Exception as e:
            self.log_message(f"Error processing ping results: {str(e)}", "ERROR")
    
    def update_stats_display(self, stats):
        try:
            self.avg_ping.set(f"{stats.get('recent_average', 0):.1f} ms")
            self.jitter.set(f"{stats.get('jitter', 0):.1f} ms")
        except Exception as e:
            self.log_message(f"Error updating stats display: {str(e)}", "ERROR")
            
    def update_ping_display(self, ping_time):
        try:
            ping_value = float(ping_time)
            self.current_ping.set(f"{ping_value:.0f} ms")
            
            ping_label = None
            for widget in self.root.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if hasattr(child, 'winfo_children'):
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, ttk.Label) and grandchild.cget('textvariable') == str(self.current_ping):
                                    ping_label = grandchild
                                    break
            
            if ping_label:
                if ping_value < 50:
                    ping_label.config(foreground='green')
                elif ping_value < 100:
                    ping_label.config(foreground='orange')
                else:
                    ping_label.config(foreground='red')
                    
        except ValueError:
            pass
            
    def update_packet_loss(self, loss_percent):
        self.packet_loss.set(f"{loss_percent:.1f}%")
        
    def stop_ping_monitor(self):
        self.ping_monitoring.set(False)
        
        if self.ping_monitor:
            self.ping_monitor.stop_monitor()
            
        self.ping_button.config(text="Start Ping Monitor")
        self.log_message("Ping monitor stopped", "INFO")
        self.status_bar.config(text="Ping monitor stopped")
        
    def ping_monitor_stopped(self):
        self.ping_monitoring.set(False)
        self.ping_button.config(text="Start Ping Monitor")
        self.status_bar.config(text="Ping monitor stopped due to error")
        
    def run(self):
        self.log_message("Network Optimizer GUI started", "INFO")
        self.root.mainloop()

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
            print("All packages installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install packages: {e}")
            return None
    
    try:
        import pyuac
        import requests
        return pyuac
    except ImportError as e:
        print(f"Failed to import packages after installation: {e}")
        return None

def main():
    try:
        pyuac = check_and_install_packages()
        if not pyuac:
            input("Press Enter to exit...")
            return
        
        if not pyuac.isUserAdmin():
            print("Administrator privileges required. Re-launching as admin...")
            pyuac.runAsAdmin()
        else:
            print("Running with administrator privileges")
            
            app = NetworkOptimizerGUI()
            app.run()
            
    except Exception as e:
        print(f"Application failed to start: {e}")
        messagebox.showerror("Startup Error", f"Application failed to start: {e}")

if __name__ == "__main__":
    main()