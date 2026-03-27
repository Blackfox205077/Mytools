import ctypes
import sys
import argparse
import os
from datetime import datetime

# Windows API Constants
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_TERMINATE = 0x0001
PROCESS_SUSPEND_RESUME = 0x0800

class ShadowExcision:
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32

    def get_admin_privileges(self):
        return ctypes.windll.shell32.IsUserAnAdmin()

    def dump_memory_region(self, pid, address, size, output_dir="dumps"):
        """سحب محتوى منطقة ذاكرة محددة وحفظها في ملف bin"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # فتح العملية بصلاحيات القراءة
        handle = self.kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
        if not handle:
            return False, "Could not open process for reading."

        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()
        
        # تحويل العنوان من نص (Hex) إلى رقم إذا لزم الأمر
        addr_int = int(address, 16) if isinstance(address, str) else address

        if self.kernel32.ReadProcessMemory(handle, addr_int, buffer, size, ctypes.byref(bytes_read)):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{output_dir}/dump_PID{pid}_{hex(addr_int)}_{timestamp}.bin"
            
            with open(filename, "wb") as f:
                f.write(buffer.raw[:bytes_read.value])
            
            self.kernel32.CloseHandle(handle)
            return True, filename
        
        self.kernel32.CloseHandle(handle)
        return False, "ReadProcessMemory failed."

    def suspend_process(self, pid):
        handle = self.kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
        if handle:
            result = ctypes.windll.ntdll.NtSuspendProcess(handle)
            self.kernel32.CloseHandle(handle)
            return result == 0
        return False

    def terminate_process(self, pid):
        handle = self.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        if handle:
            result = self.kernel32.TerminateProcess(handle, 1)
            self.kernel32.CloseHandle(handle)
            return result
        return False

def main():
    parser = argparse.ArgumentParser(description="SHΔDØW-EXCISION: Memory Surgeon Tool")
    parser.add_argument("--pid", type=int, required=True, help="Target Process ID")
    parser.add_argument("--action", choices=["suspend", "terminate", "dump"], required=True)
    parser.add_argument("--addr", type=str, help="Memory address for dump (e.g. 0x7ffa12340000)")
    parser.add_argument("--size", type=int, default=4096, help="Size to dump in bytes (default 4KB)")
    
    args = parser.parse_args()
    excision = ShadowExcision()

    if not excision.get_admin_privileges():
        print("[-] Access Denied: Admin privileges required.")
        sys.exit(1)

    if args.action == "dump":
        if not args.addr:
            print("[-] Error: Address is required for memory dump.")
            return
        success, result = excision.dump_memory_region(args.pid, args.addr, args.size)
        if success:
            print(f"[+] Memory extracted successfully: {result}")
        else:
            print(f"[-] Extraction failed: {result}")

    elif args.action == "suspend":
        if excision.suspend_process(args.pid):
            print(f"[+] Process {args.pid} FROZEN.")
        else: print(f"[-] Suspend failed.")

    elif args.action == "terminate":
        if excision.terminate_process(args.pid):
            print(f"[+] Process {args.pid} ELIMINATED.")
        else: print(f"[-] Termination failed.")

if __name__ == "__main__":
    main()
