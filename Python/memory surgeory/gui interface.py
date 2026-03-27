#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHΔDØW CORE - Memory Surgeon Control Center v8.0
واجهة رسومية متوافقة مع الإصدار المدمج (PPL + Hollowing + Entropy + Context)
"""

import customtkinter as ctk
import subprocess
import threading
import sys
import os
import time
import psutil
import re
import traceback
from datetime import datetime
import queue
from typing import Optional, Tuple, List

# إعدادات المظهر العام
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ============================================================================
# أنماط Regex للتعرف على التهديدات (محدثة للإصدار V8.0)
# ============================================================================

THREAT_PATTERNS = {
    'critical': [
        re.compile(r'(?i)critical', re.IGNORECASE),
        re.compile(r'(?i)meterpreter', re.IGNORECASE),
        re.compile(r'(?i)cobalt\s*strike', re.IGNORECASE),
        re.compile(r'(?i)process\s*hollowing', re.IGNORECASE),
        re.compile(r'(?i)reflective', re.IGNORECASE),
        re.compile(r'🚨', re.IGNORECASE),
        re.compile(r'(?i)suspended', re.IGNORECASE),
        re.compile(r'(?i)entropy', re.IGNORECASE),  # جديد: كشف Entropy العالي
    ],
    'high': [
        re.compile(r'(?i)high\s*severity', re.IGNORECASE),
        re.compile(r'(?i)⚠️\s*high', re.IGNORECASE),
        re.compile(r'(?i)threat\s*detected', re.IGNORECASE),
        re.compile(r'(?i)shellcode', re.IGNORECASE),
        re.compile(r'(?i)malicious', re.IGNORECASE),
        re.compile(r'(?i)suspicious', re.IGNORECASE),
        re.compile(r'(?i)confidence', re.IGNORECASE),  # جديد: نسبة الثقة
    ],
    'warning': [
        re.compile(r'(?i)warning', re.IGNORECASE),
        re.compile(r'(?i)alert', re.IGNORECASE),
        re.compile(r'⚠️', re.IGNORECASE),
        re.compile(r'(?i)protected', re.IGNORECASE),  # جديد: عمليات محمية
        re.compile(r'(?i)ppl', re.IGNORECASE),
    ],
    'success': [
        re.compile(r'(?i)success', re.IGNORECASE),
        re.compile(r'(?i)completed', re.IGNORECASE),
        re.compile(r'✓', re.IGNORECASE),
        re.compile(r'(?i)terminated', re.IGNORECASE),
        re.compile(r'(?i)clean', re.IGNORECASE),
        re.compile(r'(?i)saved', re.IGNORECASE),
    ],
    'info': [
        re.compile(r'(?i)system', re.IGNORECASE),
        re.compile(r'(?i)initializing', re.IGNORECASE),
        re.compile(r'(?i)starting', re.IGNORECASE),
        re.compile(r'(?i)scan\s*complete', re.IGNORECASE),
        re.compile(r'(?i)process', re.IGNORECASE),
        re.compile(r'(?i)memory', re.IGNORECASE),
        re.compile(r'(?i)yara', re.IGNORECASE),  # جديد: YARA matches
    ],
    'important': [
        re.compile(r'(?i)found', re.IGNORECASE),
        re.compile(r'(?i)detected', re.IGNORECASE),
        re.compile(r'(?i)match', re.IGNORECASE),
        re.compile(r'(?i)indicator', re.IGNORECASE),
        re.compile(r'(?i)ip', re.IGNORECASE),
        re.compile(r'(?i)url', re.IGNORECASE),
        re.compile(r'(?i)strings', re.IGNORECASE),  # جديد: السلاسل المكتشفة
        re.compile(r'(?i)context', re.IGNORECASE),
    ],
}

# أنماط إضافية
IP_PATTERN = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
URL_PATTERN = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?::\d+)?(?:/[-\w$.+!*\'(),;:@&=?/~#%]*)?')
ENTROPY_PATTERN = re.compile(r'entropy:\s*([0-9.]+)', re.IGNORECASE)
CONFIDENCE_PATTERN = re.compile(r'confidence:\s*([0-9]+)%', re.IGNORECASE)

class ModernConsole(ctk.CTkTextbox):
    """كونسول مطور مع دعم الميزات الجديدة"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(font=("Consolas", 13), border_width=1, border_color="#1f538d")
        
        # ألوان مخصصة للميزات الجديدة
        self.tag_config("critical", foreground="#FF0000", font=("Consolas", 13, "bold"))
        self.tag_config("high", foreground="#FF4444", font=("Consolas", 13, "bold"))
        self.tag_config("warning", foreground="#FFFF00", font=("Consolas", 13))
        self.tag_config("success", foreground="#00FF00", font=("Consolas", 13))
        self.tag_config("info", foreground="#00FFFF", font=("Consolas", 13))
        self.tag_config("important", foreground="#FF00FF", font=("Consolas", 13))
        self.tag_config("ip", foreground="#FFA500", font=("Consolas", 13, "bold"))
        self.tag_config("url", foreground="#00FFAA", font=("Consolas", 13, "underline"))
        self.tag_config("entropy", foreground="#FF66CC", font=("Consolas", 13, "bold"))  # جديد
        self.tag_config("confidence", foreground="#FF9933", font=("Consolas", 13, "bold"))  # جديد
        self.tag_config("white", foreground="#FFFFFF", font=("Consolas", 13))
        self.tag_config("bold", font=("Consolas", 13, "bold"))
        self.tag_config("title", font=("Consolas", 14, "bold"), foreground="#1f538d")
        
        self.search_positions = []
        self.current_search_index = -1
        self.export_in_progress = False

    def log(self, message, tag="white", bold=False):
        """إضافة رسالة مع تنسيق متقدم"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # معالجة خاصة للأنماط الجديدة
        formatted_message = self._highlight_special_patterns(message)
        
        formatted_msg = f"[{timestamp}] {formatted_message}\n"
        
        if bold:
            self.insert("end", formatted_msg, (tag, "bold"))
        else:
            self.insert("end", formatted_msg, tag)
        
        self.see("end")
        self.update_idletasks()
    
    def _highlight_special_patterns(self, text: str) -> str:
        """تمييز الأنماط الخاصة مثل Entropy و Confidence"""
        # تمييز Entropy
        text = ENTROPY_PATTERN.sub(lambda m: f"entropy: {self._create_tagged_text(m.group(1), 'entropy')}", text)
        
        # تمييز Confidence
        text = CONFIDENCE_PATTERN.sub(lambda m: f"confidence: {self._create_tagged_text(m.group(1) + '%', 'confidence')}", text)
        
        # تمييز IPs
        text = IP_PATTERN.sub(lambda m: self._create_tagged_text(m.group(0), "ip"), text)
        
        # تمييز URLs
        text = URL_PATTERN.sub(lambda m: self._create_tagged_text(m.group(0), "url"), text)
        
        return text
    
    def _create_tagged_text(self, text: str, tag: str) -> str:
        """إنشاء نص مع علامات التلوين"""
        return f"<{tag}>{text}</{tag}>"

    def log_raw(self, message, tag="white"):
        self.insert("end", message + "\n", tag)
        self.see("end")

    def clear(self):
        self.delete("1.0", "end")
        self.search_positions = []
        self.current_search_index = -1

    def search(self, query):
        if not query:
            return 0
        
        self.tag_remove("search", "1.0", "end")
        start = "1.0"
        count = 0
        self.search_positions = []
        
        while True:
            pos = self.search(query, start, stopindex="end", nocase=True)
            if not pos:
                break
            self.search_positions.append(pos)
            end = f"{pos}+{len(query)}c"
            self.tag_add("search", pos, end)
            start = end
            count += 1
        
        self.tag_config("search", background="#ffff00", foreground="#000000")
        
        if count > 0:
            self.current_search_index = 0
            self.see(self.search_positions[0])
        
        return count

    def search_next(self):
        if self.search_positions and self.current_search_index < len(self.search_positions) - 1:
            self.current_search_index += 1
            self.see(self.search_positions[self.current_search_index])
            return True
        return False

    def search_prev(self):
        if self.search_positions and self.current_search_index > 0:
            self.current_search_index -= 1
            self.see(self.search_positions[self.current_search_index])
            return True
        return False

    def export_to_file(self, filename):
        if self.export_in_progress:
            return False
        
        try:
            self.export_in_progress = True
            content = self.get("1.0", "end-1c")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False
        finally:
            self.export_in_progress = False

class SystemMonitor(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#1a1a2e", corner_radius=10)
        
        self.title = ctk.CTkLabel(self, text="SYSTEM MONITOR", font=("Segoe UI", 11, "bold"), text_color="#888")
        self.title.pack(pady=(10, 5))
        
        self.cpu_label = ctk.CTkLabel(self, text="CPU: 0%", font=("Consolas", 11))
        self.cpu_label.pack(pady=2)
        
        self.ram_label = ctk.CTkLabel(self, text="RAM: 0 MB", font=("Consolas", 11))
        self.ram_label.pack(pady=2)
        
        self.proc_label = ctk.CTkLabel(self, text="Processes: 0", font=("Consolas", 11))
        self.proc_label.pack(pady=2)
        
        self.progress = ctk.CTkProgressBar(self, width=150, height=8)
        self.progress.pack(pady=10)
        self.progress.set(0)
        
        self.update_stats()
    
    def update_stats(self):
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            processes = len(psutil.pids())
            
            self.cpu_label.configure(text=f"CPU: {cpu_percent:.1f}%")
            self.ram_label.configure(text=f"RAM: {memory.used // (1024*1024)} MB / {memory.total // (1024*1024)} MB")
            self.proc_label.configure(text=f"Processes: {processes}")
            self.progress.set(cpu_percent / 100)
        except:
            pass
        
        self.after(1000, self.update_stats)

class ShadowCoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SHΔDØW CORE - Memory Surgeon Control Center v8.0")
        self.geometry("1400x900")
        self.minsize(1200, 700)
        
        self.is_running = False
        self.process = None
        self.output_queue = queue.Queue()
        self.scan_start_time = None
        self.threat_count = 0
        self.scan_thread = None
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        self._create_main_view()
        self._create_status_bar()
        
        self.after(100, self._process_queue)
        self._print_welcome_banner()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        self.logo = ctk.CTkLabel(self.sidebar, text="SHΔDØW\nCORE", font=("Courier New", 28, "bold"), text_color="#1f538d")
        self.logo.pack(pady=30)
        
        self.btn_fire = ctk.CTkButton(self.sidebar, text="🔥 FIRE SCAN", fg_color="#cc0000", hover_color="#800000", height=50, font=("Segoe UI", 14, "bold"), command=self.start_scan)
        self.btn_fire.pack(pady=10, padx=20, fill="x")
        
        self.btn_stop = ctk.CTkButton(self.sidebar, text="⏹️ STOP SCAN", state="disabled", fg_color="#333", hover_color="#cc0000", height=45, font=("Segoe UI", 12), command=self.stop_scan)
        self.btn_stop.pack(pady=5, padx=20, fill="x")
        
        separator = ctk.CTkFrame(self.sidebar, height=2, fg_color="#333")
        separator.pack(pady=15, padx=20, fill="x")
        
        self.label_opts = ctk.CTkLabel(self.sidebar, text="⚙️ SCAN OPTIONS", font=("Segoe UI", 12, "bold"), text_color="#888")
        self.label_opts.pack(pady=(15, 10))
        
        self.check_advanced = ctk.CTkCheckBox(self.sidebar, text="Deep Memory Analysis", font=("Segoe UI", 11))
        self.check_advanced.pack(pady=5, padx=20, anchor="w")
        self.check_advanced.select()  # مفعل افتراضياً
        
        self.check_dump = ctk.CTkCheckBox(self.sidebar, text="Create Memory Dump", font=("Segoe UI", 11))
        self.check_dump.pack(pady=5, padx=20, anchor="w")
        
        self.check_suspend = ctk.CTkCheckBox(self.sidebar, text="Auto-Suspend Threats", font=("Segoe UI", 11))
        self.check_suspend.pack(pady=5, padx=20, anchor="w")
        
        # خيار جديد لفحص Hollowing
        self.check_hollowing = ctk.CTkCheckBox(self.sidebar, text="Deep Hollowing Analysis (Entropy)", font=("Segoe UI", 11))
        self.check_hollowing.pack(pady=5, padx=20, anchor="w")
        self.check_hollowing.select()
        
        separator2 = ctk.CTkFrame(self.sidebar, height=2, fg_color="#333")
        separator2.pack(pady=15, padx=20, fill="x")
        
        self.btn_export = ctk.CTkButton(self.sidebar, text="💾 EXPORT LOGS", fg_color="#1f538d", hover_color="#0f3a5d", height=40, font=("Segoe UI", 12), command=self._export_logs_dialog)
        self.btn_export.pack(pady=5, padx=20, fill="x")
        
        self.btn_clear = ctk.CTkButton(self.sidebar, text="🗑️ CLEAR CONSOLE", fg_color="#333", hover_color="#555", height=40, font=("Segoe UI", 12), command=self._clear_console)
        self.btn_clear.pack(pady=5, padx=20, fill="x")
        
        self.stats_frame = ctk.CTkFrame(self.sidebar, fg_color="#1a1a2e", corner_radius=10)
        self.stats_frame.pack(pady=20, padx=15, fill="x")
        
        self.stats_title = ctk.CTkLabel(self.stats_frame, text="📊 SCAN STATS", font=("Segoe UI", 11, "bold"))
        self.stats_title.pack(pady=(10, 5))
        
        self.threat_count_label = ctk.CTkLabel(self.stats_frame, text="Threats: 0", font=("Consolas", 11))
        self.threat_count_label.pack(pady=2)
        
        self.hollowing_count_label = ctk.CTkLabel(self.stats_frame, text="Hollowed: 0", font=("Consolas", 11), text_color="#FF4444")
        self.hollowing_count_label.pack(pady=2)
        
        self.scan_time_label = ctk.CTkLabel(self.stats_frame, text="Duration: --:--", font=("Consolas", 11))
        self.scan_time_label.pack(pady=2)
        
        self.system_monitor = SystemMonitor(self.sidebar)
        self.system_monitor.pack(side="bottom", pady=20, padx=15, fill="x")

    def _create_main_view(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        
        self.tabs = ctk.CTkTabview(self.main_container)
        self.tabs.pack(fill="both", expand=True)
        
        self.tab_console = self.tabs.add("📜 TERMINAL LOG")
        self.tab_analysis = self.tabs.add("🔍 ANALYSIS")
        self.tab_help = self.tabs.add("📖 HELP")
        
        self._create_console_tab()
        self._create_analysis_tab()
        self._create_help_tab()

    def _create_console_tab(self):
        search_frame = ctk.CTkFrame(self.tab_console, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 Search logs...", width=350, font=("Segoe UI", 11))
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self._search_logs())
        
        self.btn_search = ctk.CTkButton(search_frame, text="Search", width=80, fg_color="#1f538d", command=self._search_logs)
        self.btn_search.pack(side="left", padx=5)
        
        self.btn_next = ctk.CTkButton(search_frame, text="▼ Next", width=70, fg_color="#333", command=self._search_next)
        self.btn_next.pack(side="left", padx=2)
        
        self.btn_prev = ctk.CTkButton(search_frame, text="▲ Prev", width=70, fg_color="#333", command=self._search_prev)
        self.btn_prev.pack(side="left", padx=2)
        
        self.search_count_label = ctk.CTkLabel(search_frame, text="", font=("Segoe UI", 10), text_color="#888")
        self.search_count_label.pack(side="left", padx=10)
        
        self.console = ModernConsole(self.tab_console)
        self.console.pack(fill="both", expand=True)

    def _create_analysis_tab(self):
        analysis_frame = ctk.CTkFrame(self.tab_analysis)
        analysis_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        title = ctk.CTkLabel(analysis_frame, text="ANALYSIS RESULTS", font=("Segoe UI", 18, "bold"), text_color="#1f538d")
        title.pack(pady=20)
        
        self.analysis_text = ctk.CTkTextbox(analysis_frame, font=("Consolas", 12))
        self.analysis_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.analysis_text.insert("1.0", "No analysis results yet.\nRun a scan to see detailed results.\n\n")
        self.analysis_text.insert("end", "V8.0 New Features:\n")
        self.analysis_text.insert("end", "• PPL Detection (Protected Processes)\n")
        self.analysis_text.insert("end", "• Process Hollowing with Entropy Analysis\n")
        self.analysis_text.insert("end", "• YARA with Context Extraction\n")
        self.analysis_text.insert("end", "• Network Indicators (IPs, URLs)\n")

    def _create_help_tab(self):
        help_frame = ctk.CTkFrame(self.tab_help)
        help_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        help_text = ctk.CTkTextbox(help_frame, font=("Segoe UI", 12))
        help_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        help_content = """╔══════════════════════════════════════════════════════════════════════╗
║         MEMORY SURGEON PRO V8.0 - ULTIMATE EDITION                ║
║         Advanced Memory Forensics & Threat Detection              ║
╚══════════════════════════════════════════════════════════════════════╝

📌 NEW FEATURES IN V8.0
───────────────────────────────────────────────────────────────────────
• PPL Detection - Detects protected processes (Windows Defender, LSA)
• Process Hollowing with Entropy Analysis - High entropy = injected code
• Context Extraction - Shows surrounding strings around threats
• Network Indicators - Automatically highlights IPs and URLs

🎯 THREAT LEVELS
───────────────────────────────────────────────────────────────────────
🔴 CRITICAL - Meterpreter, Cobalt Strike, Process Hollowing (Entropy >7)
🟠 HIGH     - Shellcode, Malicious activity, High confidence
🟡 WARNING  - Protected processes, Suspicious behavior
🟢 SUCCESS  - Clean operations, Reports saved
🔵 INFO     - System information, YARA matches
🟣 IMPORTANT- Findings, Strings, Context data

📊 NEW METRICS
───────────────────────────────────────────────────────────────────────
• Entropy Score - Measures randomness (high = likely injected code)
• Confidence % - Hollowing detection confidence
• Context Strings - Readable text around threat location
• Network Indicators - IP addresses, URLs, Domains

⚙️ SCAN OPTIONS
───────────────────────────────────────────────────────────────────────
• Deep Memory Analysis - Full YARA scanning
• Create Memory Dump - Forensic dumps for analysis
• Auto-Suspend Threats - Freeze critical processes
• Deep Hollowing Analysis - Entropy-based detection

⚠️ Run as Administrator for full functionality"""
        help_text.insert("1.0", help_content)
        help_text.configure(state="disabled")

    def _create_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=35, corner_radius=0)
        self.status_bar.grid(row=1, column=1, sticky="ew")
        
        self.status_text = ctk.CTkLabel(self.status_bar, text="● SYSTEM READY", font=("Segoe UI", 11), text_color="#00FF00")
        self.status_text.pack(side="left", padx=20)
        
        self.scan_status = ctk.CTkLabel(self.status_bar, text="No active scan", font=("Segoe UI", 11), text_color="#888")
        self.scan_status.pack(side="left", padx=20)
        
        self.time_label = ctk.CTkLabel(self.status_bar, text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), font=("Consolas", 11))
        self.time_label.pack(side="right", padx=20)
        
        self._update_time()

    def _update_time(self):
        self.time_label.configure(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.after(1000, self._update_time)

    def _print_welcome_banner(self):
        banner = """╔══════════════════════════════════════════════════════════════════════╗
║     MEMORY SURGEON PRO V8.0 - ULTIMATE EDITION                      ║
║     PPL Detection | Hollowing (Entropy) | Context Extraction       ║
╚══════════════════════════════════════════════════════════════════════╝"""
        self.console.log_raw(banner, "title")
        self.console.log("System ready. Click FIRE SCAN to start.", "success")
        self.console.log("New in V8.0: Entropy Analysis & Context Extraction", "info")

    def _search_logs(self):
        query = self.search_entry.get()
        if query:
            count = self.console.search(query)
            if count > 0:
                self.search_count_label.configure(text=f"Found {count} matches")

    def _search_next(self):
        self.console.search_next()

    def _search_prev(self):
        self.console.search_prev()

    def _clear_console(self):
        self.console.clear()
        self._print_welcome_banner()

    def _export_logs_dialog(self):
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(defaultextension=".log", filetypes=[("Log files", "*.log"), ("Text files", "*.txt")])
        if filename and self.console.export_to_file(filename):
            self.console.log(f"✓ Logs exported to: {filename}", "success")

    def _detect_threat_level(self, line):
        line_lower = line.lower()
        for pattern in THREAT_PATTERNS['critical']:
            if pattern.search(line):
                return "critical"
        for pattern in THREAT_PATTERNS['high']:
            if pattern.search(line):
                return "high"
        for pattern in THREAT_PATTERNS['warning']:
            if pattern.search(line):
                return "warning"
        for pattern in THREAT_PATTERNS['success']:
            if pattern.search(line):
                return "success"
        for pattern in THREAT_PATTERNS['important']:
            if pattern.search(line):
                return "important"
        for pattern in THREAT_PATTERNS['info']:
            if pattern.search(line):
                return "info"
        return None

    def _process_queue(self):
        try:
            while True:
                try:
                    line = self.output_queue.get_nowait()
                    if isinstance(line, tuple) and len(line) >= 2:
                        msg, tag = line[0], line[1]
                    else:
                        msg = str(line)
                        tag = self._detect_threat_level(msg) or "white"
                    
                    # تحديث الإحصائيات
                    if "hollowed" in msg.lower() or "hollowing" in msg.lower():
                        self.after(0, lambda: self.hollowing_count_label.configure(text=f"Hollowed: +1"))
                    
                    self.console.log(msg, tag)
                except queue.Empty:
                    break
        except Exception:
            pass
        
        self.after(50, self._process_queue)

    def start_scan(self):
        if self.is_running:
            self.console.log("Scan already in progress!", "warning")
            return
        
        self.is_running = True
        self.scan_start_time = time.time()
        self.threat_count = 0
        
        self.btn_fire.configure(state="disabled", text="🔥 SCANNING...")
        self.btn_stop.configure(state="normal", fg_color="#cc0000")
        self.status_text.configure(text="● SCANNING ACTIVE", text_color="#FF4444")
        self.scan_status.configure(text="Analyzing system memory...", text_color="#FFA500")
        
        self.console.clear()
        self._print_welcome_banner()
        
        self.console.log("", "white")
        self.console.log("="*80, "info")
        self.console.log("INITIATING MEMORY SCAN (V8.0)", "info", bold=True)
        self.console.log("="*80, "info")
        
        self.console.log("\nSelected Options:", "success")
        if self.check_advanced.get():
            self.console.log("  • Deep Memory Analysis: ENABLED", "success")
        if self.check_dump.get():
            self.console.log("  • Memory Dump Creation: ENABLED", "success")
        if self.check_suspend.get():
            self.console.log("  • Auto-Suspend Threats: ENABLED", "success")
        if self.check_hollowing.get():
            self.console.log("  • Deep Hollowing Analysis (Entropy): ENABLED", "success")
        
        self.console.log("", "white")
        
        # بناء أمر التشغيل للإصدار V8.0
        cmd = [sys.executable, "memory_surgeon_v80.py", "--scan"]
        
        if self.check_advanced.get():
            cmd.append("--advanced")
        if self.check_dump.get():
            cmd.append("--dump")
        if self.check_suspend.get():
            cmd.append("--auto-suspend")
        
        self.console.log(f"Command: {' '.join(cmd)}", "info")
        self.console.log(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "info")
        self.console.log("", "white")
        self.console.log("Waiting for scan results...", "cyan")
        self.console.log("")
        
        def run_scan():
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=creationflags,
                    errors='replace'  # معالجة الترميز
                )
                
                for line in iter(self.process.stdout.readline, ''):
                    if not line:
                        break
                    
                    line = line.strip()
                    if line:
                        tag = self._detect_threat_level(line)
                        self.output_queue.put((line, tag))
                        
                        # تحديث عدد التهديدات
                        if tag in ["critical", "high"]:
                            self.threat_count += 1
                            self.after(0, lambda: self.threat_count_label.configure(text=f"Threats: {self.threat_count}"))
                
                self.process.stdout.close()
                self.process.wait()
                
                self.output_queue.put(("", "white"))
                self.output_queue.put(("="*80, "info"))
                self.output_queue.put((f"SCAN COMPLETED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "success"))
                self.output_queue.put(("="*80, "info"))
                
                self.after(0, self._scan_finished)
                
            except Exception as e:
                self.output_queue.put((f"ERROR: {str(e)}", "critical"))
                self.after(0, self._scan_finished)
        
        self.scan_thread = threading.Thread(target=run_scan, daemon=True)
        self.scan_thread.start()
        
        self._update_scan_stats()

    def _update_scan_stats(self):
        if self.is_running and self.scan_start_time:
            elapsed = time.time() - self.scan_start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.scan_time_label.configure(text=f"Duration: {minutes:02d}:{seconds:02d}")
        
        self.after(1000, self._update_scan_stats)

    def _scan_finished(self):
        self.is_running = False
        self.process = None
        
        self.btn_fire.configure(state="normal", text="🔥 FIRE SCAN")
        self.btn_stop.configure(state="disabled", fg_color="#333")
        self.status_text.configure(text="● SCAN COMPLETE", text_color="#00FF00")
        self.scan_status.configure(text="Ready for next scan", text_color="#00FF00")
        
        elapsed = time.time() - self.scan_start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("1.0", "="*60 + "\n")
        self.analysis_text.insert("end", "SCAN SUMMARY (V8.0)\n")
        self.analysis_text.insert("end", "="*60 + "\n\n")
        self.analysis_text.insert("end", f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.analysis_text.insert("end", f"Duration: {minutes:02d}:{seconds:02d}\n")
        self.analysis_text.insert("end", f"Total Threats: {self.threat_count}\n\n")
        
        self.console.log("", "white")
        self.console.log("🔍 POST-SCAN INSTRUCTIONS:", "success", bold=True)
        self.console.log("  • Check 'Forensics_Reports' folder for detailed JSON report", "white")
        self.console.log
