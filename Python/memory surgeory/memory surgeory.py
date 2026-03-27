#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Surgeon Pro V10.3 - Professional Edition
مع تحسينات العرض: اسم العملية مع علامة PPL، نوع التهديد، درجة الخطورة
"""

import psutil
import yara
import os
import sys
import ctypes
import ctypes.wintypes
import hashlib
import time
import math
import struct
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import argparse
import traceback

# ============================================================================
# COLORS
# ============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'
    
    @staticmethod
    def red(text): return f"{Colors.RED}{text}{Colors.END}"
    @staticmethod
    def green(text): return f"{Colors.GREEN}{text}{Colors.END}"
    @staticmethod
    def yellow(text): return f"{Colors.YELLOW}{text}{Colors.END}"
    @staticmethod
    def blue(text): return f"{Colors.BLUE}{text}{Colors.END}"
    @staticmethod
    def bold(text): return f"{Colors.BOLD}{text}{Colors.END}"
    
    # إضافات للعلامات
    @staticmethod
    def ppl(text): return f"{Colors.CYAN}{text}{Colors.END}"
    @staticmethod
    def critical(text): return f"{Colors.RED}{Colors.BOLD}{text}{Colors.END}"
    @staticmethod
    def high(text): return f"{Colors.YELLOW}{Colors.BOLD}{text}{Colors.END}"

# ============================================================================
# CONSTANTS
# ============================================================================

PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE = 0x10
MEM_COMMIT = 0x1000
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

# حدود الأداء
MAX_REGIONS_PER_PROCESS = 200
MAX_SCAN_SIZE = 256 * 1024  # 256KB لكل منطقة
PROCESS_TIMEOUT_SECONDS = 15

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_uint32),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_uint32),
        ("Protect", ctypes.c_uint32),
        ("Type", ctypes.c_uint32),
    ]

# ============================================================================
# PRIVILEGE MANAGER
# ============================================================================

class PrivilegeManager:
    @staticmethod
    def is_admin() -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    @staticmethod
    def enable_debug_privilege() -> bool:
        if not PrivilegeManager.is_admin():
            return False
        
        try:
            kernel32 = ctypes.windll.kernel32
            advapi32 = ctypes.windll.advapi32
            
            TOKEN_ADJUST_PRIVILEGES = 0x0020
            TOKEN_QUERY = 0x0008
            
            class LUID(ctypes.Structure):
                _fields_ = [("LowPart", ctypes.c_uint32), ("HighPart", ctypes.c_int32)]
            
            class TOKEN_PRIVILEGES(ctypes.Structure):
                _fields_ = [("PrivilegeCount", ctypes.c_uint32), ("Privileges", LUID * 1)]
            
            hProcess = kernel32.GetCurrentProcess()
            hToken = ctypes.c_void_p()
            
            if not advapi32.OpenProcessToken(hProcess, TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, ctypes.byref(hToken)):
                return False
            
            luid = LUID()
            if not advapi32.LookupPrivilegeValueW(None, "SeDebugPrivilege", ctypes.byref(luid)):
                kernel32.CloseHandle(hToken)
                return False
            
            tp = TOKEN_PRIVILEGES()
            tp.PrivilegeCount = 1
            tp.Privileges[0] = luid
            
            advapi32.AdjustTokenPrivileges(hToken, False, ctypes.byref(tp), 0, None, None)
            kernel32.CloseHandle(hToken)
            return True
        except:
            return False
    
    @staticmethod
    def open_process_safe(pid: int, access: int) -> int:
        handle = ctypes.windll.kernel32.OpenProcess(access, False, pid)
        if not handle:
            PrivilegeManager.enable_debug_privilege()
            handle = ctypes.windll.kernel32.OpenProcess(access, False, pid)
        return handle

# ============================================================================
# PPL DETECTOR
# ============================================================================

class PPLDetector:
    PROTECTED_PROCESSES = {
        'MsMpEng.exe': 'Windows Defender',
        'lsass.exe': 'Local Security Authority',
        'csrss.exe': 'Client Server Runtime',
        'wininit.exe': 'Windows Init',
        'services.exe': 'Services Control',
        'winlogon.exe': 'Windows Logon',
        'smss.exe': 'Session Manager',
        'WmiPrvSE.exe': 'WMI Provider'
    }
    
    @staticmethod
    def is_protected(proc) -> Tuple[bool, str]:
        try:
            proc_name = proc.name()
            if proc_name in PPLDetector.PROTECTED_PROCESSES:
                return True, PPLDetector.PROTECTED_PROCESSES[proc_name]
            
            # محاولة قراءة مستوى الحماية
            ntdll = ctypes.windll.ntdll
            kernel32 = ctypes.windll.kernel32
            
            class PROCESS_PROTECTION_LEVEL_INFORMATION(ctypes.Structure):
                _fields_ = [("ProtectionLevel", ctypes.c_uint32)]
            
            info = PROCESS_PROTECTION_LEVEL_INFORMATION()
            return_length = ctypes.c_ulong()
            
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, proc.pid)
            if handle:
                result = ntdll.NtQueryInformationProcess(
                    handle, 0x41, ctypes.byref(info), ctypes.sizeof(info), ctypes.byref(return_length)
                )
                kernel32.CloseHandle(handle)
                if result == 0 and info.ProtectionLevel > 0:
                    level_names = {
                        1: "WinTcb", 2: "Windows", 3: "WinTcb Light",
                        4: "Windows Light", 5: "Anti-Malware", 6: "LSA"
                    }
                    return True, f"PPL ({level_names.get(info.ProtectionLevel, f'Level {info.ProtectionLevel}')})"
        except:
            pass
        return False, None

# ============================================================================
# MEMORY STRING CARVER
# ============================================================================

class MemoryStringCarver:
    PATTERNS = {
        'url': re.compile(r'https?://[^\s]+', re.IGNORECASE),
        'ip': re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'),
        'cmd': re.compile(r'(?:powershell|cmd\.exe|rundll32|wmic)[^\s]*', re.IGNORECASE),
        'dll': re.compile(r'\b[a-zA-Z0-9_]+\.dll\b', re.IGNORECASE),
        'domain': re.compile(r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'),
    }
    
    @staticmethod
    def carve(data: bytes) -> Dict:
        result = {'strings': [], 'indicators': []}
        
        if not data:
            return result
        
        # استخراج السلاسل
        current = []
        for byte in data:
            if 32 <= byte <= 126:
                current.append(chr(byte))
            else:
                if len(current) >= 4:
                    s = ''.join(current)
                    if not s.isdigit() and len(s) < 200 and s.count('.') < 10:
                        result['strings'].append(s)
                current = []
        
        # البحث عن أنماط
        full_text = ' '.join(result['strings'])
        for name, pattern in MemoryStringCarver.PATTERNS.items():
            for match in pattern.findall(full_text)[:5]:
                result['indicators'].append({'type': name, 'value': match[:80]})
        
        result['strings'] = result['strings'][:15]
        return result

# ============================================================================
# VAD SCANNER
# ============================================================================

class VADScanner:
    def __init__(self):
        self.string_carver = MemoryStringCarver()
    
    def scan(self, proc, is_ppl: bool = False) -> List[Dict]:
        threats = []
        regions_scanned = 0
        
        try:
            access = PROCESS_QUERY_LIMITED_INFORMATION if is_ppl else (PROCESS_VM_READ | PROCESS_QUERY_INFORMATION)
            handle = PrivilegeManager.open_process_safe(proc.pid, access)
            if not handle:
                return threats
            
            address = 0
            while regions_scanned < MAX_REGIONS_PER_PROCESS:
                mbi = MEMORY_BASIC_INFORMATION()
                result = ctypes.windll.kernel32.VirtualQueryEx(handle, address, ctypes.byref(mbi), ctypes.sizeof(mbi))
                
                if result == 0:
                    break
                
                if mbi.State == MEM_COMMIT:
                    protect = mbi.Protect
                    
                    # RWX Pages
                    if protect == PAGE_EXECUTE_READWRITE:
                        data = self._read_region(handle, mbi.BaseAddress, min(mbi.RegionSize, MAX_SCAN_SIZE))
                        strings = self.string_carver.carve(data) if data else {}
                        
                        threats.append({
                            'type': 'RWX Memory',
                            'severity': 'critical',
                            'score': 3.0,
                            'address': hex(mbi.BaseAddress),
                            'size_mb': mbi.RegionSize / (1024 * 1024),
                            'strings': strings.get('strings', [])[:5],
                            'indicators': strings.get('indicators', [])
                        })
                    
                    # Unbacked Executable
                    elif protect in [PAGE_EXECUTE, PAGE_EXECUTE_READ]:
                        if not self._is_file_backed(proc, mbi.BaseAddress):
                            data = self._read_region(handle, mbi.BaseAddress, min(mbi.RegionSize, MAX_SCAN_SIZE))
                            strings = self.string_carver.carve(data) if data else {}
                            
                            threats.append({
                                'type': 'Unbacked Executable',
                                'severity': 'high',
                                'score': 2.0,
                                'address': hex(mbi.BaseAddress),
                                'size_mb': mbi.RegionSize / (1024 * 1024),
                                'strings': strings.get('strings', [])[:5],
                                'indicators': strings.get('indicators', [])
                            })
                
                address = mbi.BaseAddress + mbi.RegionSize
                regions_scanned += 1
            
            ctypes.windll.kernel32.CloseHandle(handle)
        except:
            pass
        
        return threats
    
    def _read_region(self, handle, address, size):
        try:
            buffer = ctypes.create_string_buffer(size)
            bytes_read = ctypes.c_size_t()
            if ctypes.windll.kernel32.ReadProcessMemory(handle, address, buffer, size, ctypes.byref(bytes_read)):
                return buffer.raw[:bytes_read.value]
        except:
            pass
        return None
    
    def _is_file_backed(self, proc, address):
        try:
            addr_hex = hex(address)[:12]
            for mmap in proc.memory_maps(grouped=False)[:30]:
                if mmap.addr and mmap.addr.startswith(addr_hex):
                    return mmap.path and mmap.path != ''
        except:
            pass
        return False

# ============================================================================
# PROCESS HOLLOWING DETECTOR
# ============================================================================

class ProcessHollowingDetector:
    def _calculate_entropy(self, data: bytes) -> float:
        if not data:
            return 0.0
        counts = {}
        for b in data:
            counts[b] = counts.get(b, 0) + 1
        entropy = 0.0
        length = len(data)
        for count in counts.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy
    
    def _get_main_image_region(self, proc) -> Optional[bytes]:
        try:
            exe_path = proc.exe()
            if not exe_path:
                return None
            
            handle = PrivilegeManager.open_process_safe(proc.pid, PROCESS_VM_READ | PROCESS_QUERY_INFORMATION)
            if not handle:
                return None
            
            for mmap in proc.memory_maps(grouped=False):
                if mmap.path and mmap.path == exe_path:
                    try:
                        start = int(mmap.addr.split('-')[0], 16)
                        end = int(mmap.addr.split('-')[1], 16)
                        size = min(end - start, 2 * 1024 * 1024)
                        
                        buffer = ctypes.create_string_buffer(size)
                        bytes_read = ctypes.c_size_t()
                        
                        if ctypes.windll.kernel32.ReadProcessMemory(handle, start, buffer, size, ctypes.byref(bytes_read)):
                            ctypes.windll.kernel32.CloseHandle(handle)
                            return buffer.raw[:bytes_read.value]
                    except:
                        continue
            
            ctypes.windll.kernel32.CloseHandle(handle)
        except:
            pass
        return None
    
    def detect(self, proc) -> Dict:
        result = {
            'is_hollowed': False,
            'confidence': 0,
            'score': 0.0,
            'entropy': 0.0,
            'differences': []
        }
        
        try:
            exe_path = proc.exe()
            if not exe_path or not os.path.exists(exe_path):
                return result
            
            memory_data = self._get_main_image_region(proc)
            if not memory_data or len(memory_data) < 4096:
                return result
            
            memory_hash = hashlib.sha256(memory_data).hexdigest()
            
            with open(exe_path, 'rb') as f:
                disk_data = f.read()
            disk_hash = hashlib.sha256(disk_data).hexdigest()
            
            if disk_hash != memory_hash:
                result['is_hollowed'] = True
                result['confidence'] += 50
                result['score'] += 3.0
                result['differences'].append('Hash mismatch')
            
            entropy = self._calculate_entropy(memory_data)
            result['entropy'] = entropy
            if entropy > 7.0:
                result['is_hollowed'] = True
                result['confidence'] += 25
                result['score'] += 1.5
                result['differences'].append(f'High entropy: {entropy:.2f}')
            
            mz_pos = memory_data.find(b'MZ')
            if mz_pos > 0 and mz_pos < 1024:
                result['is_hollowed'] = True
                result['confidence'] += 15
                result['score'] += 1.0
                result['differences'].append(f'MZ at offset {mz_pos}')
            
            result['confidence'] = min(result['confidence'], 100)
            result['score'] = min(result['score'], 5.0)
            
        except Exception:
            pass
        
        return result

# ============================================================================
# YARA SCANNER
# ============================================================================

YARA_RULES = '''
rule Meterpreter_Shellcode {
    meta: severity = "critical"
    strings: $a = { fc e8 89 00 00 00 60 89 e5 31 d2 64 8b 52 30 }
    condition: $a
}

rule CobaltStrike_Beacon {
    meta: severity = "critical"
    strings: $a = "beacon_config" $b = "stager"
    condition: any of them
}

rule Reflective_DLL {
    meta: severity = "high"
    strings: $a = "ReflectiveLoader" $b = "VirtualAlloc"
    condition: $a and $b
}
'''

class YaraScanner:
    def __init__(self, rules):
        self.rules = rules
    
    def scan(self, proc, is_ppl: bool = False) -> List[Dict]:
        threats = []
        if not self.rules:
            return threats
        
        try:
            access = PROCESS_QUERY_LIMITED_INFORMATION if is_ppl else (PROCESS_VM_READ | PROCESS_QUERY_INFORMATION)
            handle = PrivilegeManager.open_process_safe(proc.pid, access)
            if not handle:
                return threats
            
            scanned = 0
            for mmap in proc.memory_maps(grouped=False):
                if scanned >= 60:
                    break
                
                if mmap.perms and 'x' in mmap.perms:
                    try:
                        start = int(mmap.addr.split('-')[0], 16)
                        end = int(mmap.addr.split('-')[1], 16)
                        size = min(end - start, MAX_SCAN_SIZE)
                        
                        buffer = ctypes.create_string_buffer(size)
                        bytes_read = ctypes.c_size_t()
                        
                        if ctypes.windll.kernel32.ReadProcessMemory(handle, start, buffer, size, ctypes.byref(bytes_read)):
                            data = buffer.raw[:bytes_read.value]
                            if len(data) > 256:
                                matches = self.rules.match(data=data)
                                for match in matches:
                                    score = 3.0 if 'critical' in str(match).lower() else 2.0
                                    threats.append({
                                        'type': 'YARA Match',
                                        'severity': 'critical' if 'critical' in str(match).lower() else 'high',
                                        'score': score,
                                        'rule': match.rule,
                                        'region': mmap.addr
                                    })
                        scanned += 1
                    except:
                        continue
            
            ctypes.windll.kernel32.CloseHandle(handle)
        except:
            pass
        return threats

# ============================================================================
# HEURISTIC SCORING
# ============================================================================

class HeuristicScoring:
    @staticmethod
    def calculate_total_score(threats: List[Dict], hollow_result: Dict) -> Tuple[float, str]:
        """حساب الدرجة الإجمالية وتصنيف الخطر"""
        total_score = 0.0
        
        # جمع درجات التهديدات
        for t in threats:
            total_score += t.get('score', 0)
        
        # إضافة درجة الـ Hollowing
        total_score += hollow_result.get('score', 0)
        
        # تحديد مستوى الخطر
        if total_score >= 7.0:
            level = 'CRITICAL'
        elif total_score >= 4.0:
            level = 'HIGH'
        elif total_score >= 2.0:
            level = 'MEDIUM'
        else:
            level = 'LOW'
        
        return min(total_score, 10.0), level

# ============================================================================
# MAIN SCANNER
# ============================================================================

class MemorySurgeonPro:
    def __init__(self):
        self.rules = None
        self.vad_scanner = VADScanner()
        self.hollowing_detector = ProcessHollowingDetector()
        self.yara_scanner = None
        self.threats = []
        self.stats = {
            'total': 0, 'protected': 0, 'rwx': 0, 
            'hollowed': 0, 'yara': 0, 'real_threats': 0
        }
        self.start_time = None
        self._initialize()
    
    def _initialize(self):
        print(Colors.bold(Colors.blue("\n" + "="*80)))
        print(Colors.bold(Colors.blue("MEMORY SURGEON PRO V10.3 - PROFESSIONAL EDITION")))
        print(Colors.bold(Colors.blue("="*80 + "\n")))
        
        if PrivilegeManager.is_admin():
            PrivilegeManager.enable_debug_privilege()
            print(Colors.green("[✓] Administrator privileges"))
        else:
            print(Colors.yellow("[!] Warning: Run as Administrator for better results"))
        
        try:
            self.rules = yara.compile(source=YARA_RULES)
            self.yara_scanner = YaraScanner(self.rules)
            print(Colors.green("[✓] YARA rules loaded"))
        except Exception as e:
            print(Colors.red(f"[✗] YARA error: {e}"))
            sys.exit(1)
        
        Path("Forensics_Reports").mkdir(exist_ok=True)
        print(Colors.green("[✓] Ready\n"))
    
    def scan_process(self, proc):
        threats = []
        
        try:
            name = proc.name()
            pid = proc.pid
            create_time = proc.create_time()
            age_minutes = (time.time() - create_time) / 60
            
            # PPL Detection
            is_ppl, ppl_type = PPLDetector.is_protected(proc)
            if is_ppl:
                self.stats['protected'] += 1
            
            # VAD Scanning (RWX + Unbacked)
            vad_threats = self.vad_scanner.scan(proc, is_ppl)
            for t in vad_threats:
                self.stats['rwx'] += 1
                threats.append(t)
            
            # Process Hollowing
            hollow = self.hollowing_detector.detect(proc)
            if hollow['is_hollowed']:
                self.stats['hollowed'] += 1
                hollow_threat = {
                    'type': 'Process Hollowing',
                    'severity': 'critical' if hollow['confidence'] >= 70 else 'high',
                    'score': hollow['score'],
                    'confidence': hollow['confidence'],
                    'entropy': hollow['entropy'],
                    'differences': hollow['differences']
                }
                threats.append(hollow_threat)
            
            # YARA Scan
            yara_threats = self.yara_scanner.scan(proc, is_ppl)
            for t in yara_threats:
                self.stats['yara'] += 1
                threats.append(t)
            
            # حساب الدرجة الإجمالية
            total_score, threat_level = HeuristicScoring.calculate_total_score(threats, hollow)
            
            if threats:
                self.stats['real_threats'] += 1
                self._display_result(name, pid, threats, total_score, threat_level, age_minutes, is_ppl, ppl_type)
            
            self.stats['total'] += 1
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except Exception:
            pass
        
        return threats
    
    def _display_result(self, name, pid, threats, total_score, threat_level, age_minutes, is_ppl, ppl_type):
        """عرض النتائج بشكل منظم مع اسم العملية ونوع التهديد والدرجة"""
        
        # تنسيق اسم العملية مع علامة PPL
        if is_ppl:
            process_display = f"🛡️ {Colors.bold(name)} {Colors.cyan('[PPL]')} (PID: {pid})"
            if ppl_type:
                process_display += f" {Colors.dim(f'- {ppl_type}')}"
        else:
            process_display = f"📊 {Colors.bold(name)} (PID: {pid})"
        
        # تنسيق مستوى الخطر والدرجة
        if threat_level == 'CRITICAL':
            level_display = Colors.critical(f"[CRITICAL]")
            score_display = Colors.red(f"{total_score:.1f}/10")
        elif threat_level == 'HIGH':
            level_display = Colors.high(f"[HIGH]")
            score_display = Colors.yellow(f"{total_score:.1f}/10")
        else:
            level_display = Colors.blue(f"[{threat_level}]")
            score_display = Colors.blue(f"{total_score:.1f}/10")
        
        print(f"\n{'='*80}")
        print(f"{process_display}")
        print(f"   Age: {age_minutes:.1f} min | Score: {score_display} {level_display}")
        print(f"   Threats: {len(threats)} detected")
        
        # عرض كل تهديد مع نوعه ودرجته
        print(f"\n   {Colors.bold('Threat Details:')}")
        for i, t in enumerate(threats[:5], 1):
            threat_type = t.get('type', 'Unknown')
            threat_score = t.get('score', 0)
            severity = t.get('severity', 'medium')
            
            # أيقونة حسب النوع
            if 'RWX' in threat_type:
                icon = "🔴"
                type_color = Colors.red
            elif 'Hollowing' in threat_type:
                icon = "🟠"
                type_color = Colors.yellow
            elif 'YARA' in threat_type:
                icon = "📜"
                type_color = Colors.cyan
            elif 'Unbacked' in threat_type:
                icon = "⚠️"
                type_color = Colors.yellow
            else:
                icon = "📌"
                type_color = Colors.blue
            
            print(f"   {i}. {icon} {type_color(threat_type)}")
            print(f"      Score: {Colors.yellow(f'{threat_score:.1f}')} | Severity: {severity.upper()}")
            
            if t.get('address'):
                print(f"      Address: {Colors.dim(t['address'])}")
            if t.get('confidence'):
                print(f"      Confidence: {t['confidence']}%")
            if t.get('rule'):
                print(f"      Rule: {t['rule']}")
            if t.get('indicators'):
                for ind in t['indicators'][:2]:
                    print(f"      {ind['type'].upper()}: {Colors.dim(ind['value'][:60])}")
        
        # عرض ملخص الدرجات
        if len(threats) > 5:
            print(f"   ... and {len(threats) - 5} more threats")
        
        print("="*80)
    
    def scan_system(self):
        print(Colors.blue("\n[*] Starting system scan..."))
        print(Colors.blue("[*] Detection: RWX Memory | Process Hollowing | YARA Rules\n"))
        self.start_time = time.time()
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['pid'] > 4:
                    processes.append(proc)
            except:
                continue
        
        total = len(processes)
        workers = max(2, (os.cpu_count() or 4) // 2)
        
        print(Colors.blue(f"[*] Processes: {total} | Workers: {workers}\n"))
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self.scan_process, proc): proc for proc in processes}
            for future in as_completed(futures):
                try:
                    future.result()
                except TimeoutError:
                    pass
                except:
                    pass
        
        duration = time.time() - self.start_time
        
        print("\n" + "="*80)
        print(Colors.green(Colors.bold("✅ SCAN COMPLETE")))
        print("="*80)
        print(f"Time: {duration:.2f}s")
        print(f"Real Threats: {Colors.red(self.stats['real_threats'])}")
        print(f"RWX Regions: {self.stats['rwx']}")
        print(f"Process Hollowing: {self.stats['hollowed']}")
        print(f"Protected Processes (PPL): {self.stats['protected']}")
        print(f"YARA Matches: {self.stats['yara']}")
        
        self._save_report()
    
    def _save_report(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = {
            'timestamp': datetime.now().isoformat(),
            'duration': time.time() - self.start_time,
            'statistics': self.stats,
            'threats': self.threats[:100]
        }
        
        report_path = Path("Forensics_Reports") / f"report_{timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(Colors.green(f"\n[✓] Report saved: {report_path}"))

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Memory Surgeon Pro V10.3')
    parser.add_argument('--scan', action='store_true', help='Full system scan')
    parser.add_argument('--pid', type=int, help='Scan specific process')
    
    args = parser.parse_args()
    
    scanner = MemorySurgeonPro()
    
    try:
        if args.pid:
            proc = psutil.Process(args.pid)
            scanner.scan_process(proc)
        else:
            scanner.scan_system()
    except KeyboardInterrupt:
        print(Colors.yellow("\n[!] Interrupted"))
    except Exception as e:
        print(Colors.red(f"\n[!] Error: {e}"))
        traceback.print_exc()
    
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main()
