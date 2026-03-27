import tkinter as tk
from tkinter import Menu, filedialog, messagebox
import customtkinter as ctk
import base64, re, os, math, urllib.parse, codecs, hashlib, binascii, html

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class CyberDevUtils(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CyberDev Utils - All Encoders & Smart AI Detector")
        self.geometry("1500x960")
        self.minsize(1450, 820)
        self.configure(fg_color="#1e1e2e")

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=300, fg_color="#25253a", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(self.sidebar, text="CyberDev Utils", font=("Arial", 24, "bold"), text_color="#FF9100").pack(pady=(40, 25))

        tools = [
            ("Base64 Encode/Decode", self.load_base64),
            ("Hex Studio", self.load_hex),
            ("URL Encode/Decode", self.load_url),
            ("HTML Entity", self.load_html_entity),
            ("ROT / Vigenère / XOR", self.load_rot_xor),
            ("Binary / Octal / Base58", self.load_binary),
            ("Smart AI Detector", self.load_detector)
        ]

        for name, cmd in tools:
            btn = ctk.CTkButton(self.sidebar, text=name, height=52, fg_color="transparent",
                                text_color="#e0e0ff", hover_color="#3a3a55", anchor="w", font=("Arial", 15),
                                command=cmd)
            btn.pack(pady=6, padx=20, fill="x")

        self.main_frame = ctk.CTkFrame(self, fg_color="#1e1e2e")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.load_base64()  # الافتراضي

    def clear_main(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

    def build_input_area(self, has_file=True, has_line=True):
        mv = ctk.StringVar(value="Text")
        fr = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        fr.pack(fill="x", padx=30, pady=10)
        ctk.CTkRadioButton(fr, text="Text", variable=mv, value="Text").pack(side="left", padx=15)
        if has_file:
            ctk.CTkRadioButton(fr, text="File", variable=mv, value="File").pack(side="left", padx=15)

        input_txt = ctk.CTkTextbox(self.main_frame, height=185, font=("Consolas", 13))
        input_txt.pack(fill="both", expand=True, padx=30, pady=8)

        file_var = tk.StringVar()
        if has_file:
            ctk.CTkButton(self.main_frame, text="📁 Browse File", fg_color="#FF9100", width=160,
                          command=lambda: self.browse_file(file_var)).pack(pady=6)

        line_check = None
        if has_line:
            line_check = ctk.CTkCheckBox(self.main_frame, text="Line by Line")
            line_check.pack(pady=8)

        return mv, input_txt, file_var, line_check

    def browse_file(self, var):
        p = filedialog.askopenfilename()
        if p:
            var.set(p)

    def get_data(self, mv, text_widget, file_var):
        if mv.get() == "File" and file_var.get():
            try:
                with open(file_var.get(), "rb") as f:
                    return f.read()
            except:
                return b""
        return text_widget.get("1.0", tk.END).strip().encode("utf-8", errors="ignore")

    def copy_text(self, widget):
        self.clipboard_clear()
        self.clipboard_append(widget.get("1.0", tk.END).strip())

    def paste_to_input(self, widget):
        try:
            widget.delete("1.0", tk.END)
            widget.insert("1.0", self.clipboard_get())
        except:
            pass

    # ====================== Base64 ======================
    def load_base64(self):
        self.clear_main()
        mv, input_txt, file_var, line_check = self.build_input_area()
        ctk.CTkLabel(self.main_frame, text="Base64 Encode / Decode", font=("Arial", 20, "bold")).pack(pady=12)

        self.base64_mode = ctk.StringVar(value="Encode")
        f = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        f.pack(pady=8)
        ctk.CTkRadioButton(f, text="Encode", variable=self.base64_mode, value="Encode").pack(side="left", padx=30)
        ctk.CTkRadioButton(f, text="Decode", variable=self.base64_mode, value="Decode").pack(side="left", padx=30)

        self.url_safe = ctk.CTkCheckBox(self.main_frame, text="URL-Safe")
        self.url_safe.pack(pady=5)

        output_txt = ctk.CTkTextbox(self.main_frame, height=200, font=("Consolas", 13))
        output_txt.pack(fill="both", expand=True, padx=30, pady=10)

        btnf = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btnf.pack(pady=15)
        ctk.CTkButton(btnf, text="Run", fg_color="#FF9100", width=160, height=45, font=("Arial", 16, "bold"),
                      command=lambda: self.run_base64(mv, input_txt, file_var, line_check, output_txt)).pack(side="left", padx=10)
        ctk.CTkButton(btnf, text="Copy", width=120, command=lambda: self.copy_text(output_txt)).pack(side="left", padx=8)
        ctk.CTkButton(btnf, text="Paste → Input", width=140, command=lambda: self.paste_to_input(input_txt)).pack(side="left", padx=8)

    def run_base64(self, mv, input_txt, file_var, line_check, output_txt):
        data = self.get_data(mv, input_txt, file_var)
        try:
            txt = data.decode("utf-8", errors="ignore")
            lines = txt.splitlines() if line_check and line_check.get() else [txt]
            result = []
            for line in lines:
                if self.base64_mode.get() == "Encode":
                    r = base64.urlsafe_b64encode(line.encode()).decode().rstrip("=") if self.url_safe.get() else base64.b64encode(line.encode()).decode()
                else:
                    padding = "=" * ((4 - len(line) % 4) % 4)
                    r = base64.b64decode(line + padding).decode(errors="ignore")
                result.append(r)
            output_txt.delete("1.0", tk.END)
            output_txt.insert("1.0", "\n".join(result))
        except Exception as e:
            messagebox.showerror("Base64 Error", str(e))

    # ====================== HTML Entity ======================
    def load_html_entity(self):
        self.clear_main()
        mv, input_txt, file_var, line_check = self.build_input_area()
        ctk.CTkLabel(self.main_frame, text="HTML Entity Encode / Decode", font=("Arial", 20, "bold")).pack(pady=15)

        self.html_mode = ctk.StringVar(value="Encode")
        f = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        f.pack(pady=8)
        ctk.CTkRadioButton(f, text="Encode", variable=self.html_mode, value="Encode").pack(side="left", padx=30)
        ctk.CTkRadioButton(f, text="Decode", variable=self.html_mode, value="Decode").pack(side="left", padx=30)

        self.html_full = ctk.CTkCheckBox(self.main_frame, text="Full Encode (all characters)")
        self.html_full.pack(pady=8)

        output_txt = ctk.CTkTextbox(self.main_frame, height=220, font=("Consolas", 13))
        output_txt.pack(fill="both", expand=True, padx=30, pady=10)

        btnf = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btnf.pack(pady=15)
        ctk.CTkButton(btnf, text="Run", fg_color="#FF9100", width=160, height=45, font=("Arial", 16, "bold"),
                      command=lambda: self.run_html_entity(mv, input_txt, file_var, line_check, output_txt)).pack(side="left", padx=10)
        ctk.CTkButton(btnf, text="Copy", width=120, command=lambda: self.copy_text(output_txt)).pack(side="left", padx=8)
        ctk.CTkButton(btnf, text="Paste → Input", width=140, command=lambda: self.paste_to_input(input_txt)).pack(side="left", padx=8)

    def run_html_entity(self, mv, input_txt, file_var, line_check, output_txt):
        data = self.get_data(mv, input_txt, file_var)
        try:
            txt = data.decode("utf-8", errors="ignore")
            lines = txt.splitlines() if line_check and line_check.get() else [txt]
            result = []
            for line in lines:
                if self.html_mode.get() == "Encode":
                    r = html.escape(line, quote=True) if self.html_full.get() else html.escape(line)
                else:
                    r = html.unescape(line)
                result.append(r)
            output_txt.delete("1.0", tk.END)
            output_txt.insert("1.0", "\n".join(result))
        except Exception as e:
            messagebox.showerror("HTML Entity Error", str(e))

    # ====================== ROT / Vigenère / XOR (مُفعّلة كاملة) ======================
    def load_rot_xor(self):
        self.clear_main()
        mv, input_txt, file_var, line_check = self.build_input_area()

        ctk.CTkLabel(self.main_frame, text="ROT-n / Vigenère / XOR", font=("Arial", 20, "bold")).pack(pady=15)

        self.rot_type = ctk.CTkComboBox(self.main_frame, values=["ROT-n", "Vigenère", "XOR"], width=200)
        self.rot_type.set("ROT-n")
        self.rot_type.pack(pady=8)

        self.key_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Shift (ROT-n) or Key", width=320)
        self.key_entry.pack(pady=8)

        self.rot_mode = ctk.StringVar(value="Encode")
        f = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        f.pack(pady=8)
        ctk.CTkRadioButton(f, text="Encode", variable=self.rot_mode, value="Encode").pack(side="left", padx=30)
        ctk.CTkRadioButton(f, text="Decode", variable=self.rot_mode, value="Decode").pack(side="left", padx=30)

        output_txt = ctk.CTkTextbox(self.main_frame, height=220, font=("Consolas", 13))
        output_txt.pack(fill="both", expand=True, padx=30, pady=10)

        btnf = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btnf.pack(pady=15)
        ctk.CTkButton(btnf, text="Run", fg_color="#FF9100", width=160, height=45, font=("Arial", 16, "bold"),
                      command=lambda: self.run_rot_xor(mv, input_txt, file_var, line_check, output_txt)).pack(side="left", padx=10)
        ctk.CTkButton(btnf, text="Copy", width=120, command=lambda: self.copy_text(output_txt)).pack(side="left", padx=8)
        ctk.CTkButton(btnf, text="Paste → Input", width=140, command=lambda: self.paste_to_input(input_txt)).pack(side="left", padx=8)

    def run_rot_xor(self, mv, input_txt, file_var, line_check, output_txt):
        data = self.get_data(mv, input_txt, file_var)
        typ = self.rot_type.get()
        key = self.key_entry.get().strip()
        try:
            txt = data.decode("utf-8", errors="ignore")
            lines = txt.splitlines() if line_check and line_check.get() else [txt]
            result = []
            for line in lines:
                if typ == "ROT-n" and key.isdigit():
                    n = int(key) % 26
                    r = line.translate(str.maketrans(
                        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"[n:] + "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"[:n]*2
                    ))
                elif typ == "Vigenère" and key:
                    r = self.vigenere(line, key, encrypt=(self.rot_mode.get() == "Encode"))
                elif typ == "XOR" and key:
                    kb = key.encode()
                    r = ''.join(chr(ord(c) ^ kb[i % len(kb)]) for i, c in enumerate(line))
                else:
                    r = line
                result.append(r)
            output_txt.delete("1.0", tk.END)
            output_txt.insert("1.0", "\n".join(result))
        except Exception as e:
            messagebox.showerror("ROT/Vigenère/XOR Error", str(e))

    def vigenere(self, text, key, encrypt=True):
        key = ''.join(c.upper() for c in key if c.isalpha())
        if not key: return text
        result = []
        k_idx = 0
        for char in text:
            if char.isalpha():
                shift = ord(key[k_idx % len(key)]) - ord('A')
                base = ord('A') if char.isupper() else ord('a')
                if encrypt:
                    result.append(chr((ord(char) - base + shift) % 26 + base))
                else:
                    result.append(chr((ord(char) - base - shift) % 26 + base))
                k_idx += 1
            else:
                result.append(char)
        return ''.join(result)

    # ====================== Binary / Octal / Base58 (مُفعّلة كاملة) ======================
    def load_binary(self):
        self.clear_main()
        mv, input_txt, file_var, line_check = self.build_input_area()

        ctk.CTkLabel(self.main_frame, text="Binary / Octal / Base58 / Ascii85", font=("Arial", 20, "bold")).pack(pady=15)

        self.binary_type = ctk.CTkComboBox(self.main_frame, values=["Binary", "Octal", "Base58", "Ascii85"], width=220)
        self.binary_type.set("Binary")
        self.binary_type.pack(pady=10)

        self.binary_sep = ctk.CTkCheckBox(self.main_frame, text="Add Space Separator")
        self.binary_sep.pack(pady=5)

        output_txt = ctk.CTkTextbox(self.main_frame, height=240, font=("Consolas", 13))
        output_txt.pack(fill="both", expand=True, padx=30, pady=15)

        ctk.CTkButton(self.main_frame, text="Convert", fg_color="#FF9100", width=180, height=45,
                      command=lambda: self.run_binary(mv, input_txt, file_var, line_check, output_txt)).pack(pady=15)

    def run_binary(self, mv, input_txt, file_var, line_check, output_txt):
        data = self.get_data(mv, input_txt, file_var)
        typ = self.binary_type.get()
        try:
            txt = data.decode("utf-8", errors="ignore")
            lines = txt.splitlines() if line_check and line_check.get() else [txt]
            result = []
            for line in lines:
                b = line.encode("utf-8")
                if typ == "Binary":
                    r = ' '.join(format(byte, '08b') for byte in b) if self.binary_sep.get() else ''.join(format(byte, '08b') for byte in b)
                elif typ == "Octal":
                    r = ' '.join(format(byte, '03o') for byte in b) if self.binary_sep.get() else ''.join(format(byte, '03o') for byte in b)
                elif typ == "Base58":
                    r = self.base58_encode(b)
                elif typ == "Ascii85":
                    r = base64.b85encode(b).decode()
                result.append(r)
            output_txt.delete("1.0", tk.END)
            output_txt.insert("1.0", "\n".join(result))
        except Exception as e:
            messagebox.showerror("Binary Error", str(e))

    def base58_encode(self, data: bytes) -> str:
        alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        n = int.from_bytes(data, 'big')
        res = []
        while n:
            n, r = divmod(n, 58)
            res.append(alphabet[r])
        return ''.join(reversed(res)) or '1'

    # ====================== Hex Studio ======================
    def load_hex(self):
        self.clear_main()
        mv, input_txt, file_var, _ = self.build_input_area(has_line=False)
        ctk.CTkLabel(self.main_frame, text="Hex Studio (Advanced)", font=("Arial", 20, "bold")).pack(pady=15)

        self.hex_direction = ctk.CTkComboBox(self.main_frame, values=["Text → Hex", "Hex → Text", "Hexdump Style"], width=220)
        self.hex_direction.set("Hexdump Style")
        self.hex_direction.pack(pady=8)

        self.hex_bpl = ctk.CTkComboBox(self.main_frame, values=["8", "16", "32"], width=100)
        self.hex_bpl.set("16")
        self.hex_bpl.pack(pady=5)

        self.hex_upper = ctk.CTkCheckBox(self.main_frame, text="Uppercase")
        self.hex_upper.pack(pady=5)

        output_txt = ctk.CTkTextbox(self.main_frame, height=260, font=("Consolas", 13))
        output_txt.pack(fill="both", expand=True, padx=30, pady=15)

        ctk.CTkButton(self.main_frame, text="Run Hex", fg_color="#FF9100", width=180, height=45,
                      command=lambda: self.run_hex(mv, input_txt, file_var, output_txt)).pack(pady=15)

    def run_hex(self, mv, input_txt, file_var, output_txt):
        data = self.get_data(mv, input_txt, file_var)
        direction = self.hex_direction.get()
        bpl = int(self.hex_bpl.get())
        upper = self.hex_upper.get()
        try:
            if direction == "Hexdump Style":
                lines = []
                for i in range(0, len(data), bpl):
                    chunk = data[i:i+bpl]
                    hexp = ' '.join(f"{b:02x}" for b in chunk)
                    if upper: hexp = hexp.upper()
                    asc = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                    lines.append(f"{i:08x}  {hexp.ljust(bpl*3)}  |{asc}|")
                checksums = f"MD5: {hashlib.md5(data).hexdigest()}\nSHA1: {hashlib.sha1(data).hexdigest()}\nSHA256: {hashlib.sha256(data).hexdigest()}\nCRC32: {binascii.crc32(data) & 0xFFFFFFFF:08x}"
                final = "\n".join(lines) + "\n\n=== Checksums ===\n" + checksums
            elif direction == "Text → Hex":
                final = data.hex().upper() if upper else data.hex()
            else:
                cleaned = re.sub(r'[^0-9a-fA-F]', '', data.decode(errors="ignore"))
                if len(cleaned) % 2: cleaned += "0"
                final = bytes.fromhex(cleaned).decode(errors="ignore")
            output_txt.delete("1.0", tk.END)
            output_txt.insert("1.0", final)
        except Exception as e:
            messagebox.showerror("Hex Error", str(e))

    # ====================== Smart AI Detector ======================
    def load_detector(self):
        self.clear_main()
        ctk.CTkLabel(self.main_frame, text="Smart AI Detector", font=("Arial", 22, "bold")).pack(pady=15)

        self.det_input = ctk.CTkTextbox(self.main_frame, height=200, font=("Consolas", 13))
        self.det_input.pack(fill="x", padx=40, pady=15)

        det_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        det_frame.pack(pady=10)
        self.det_depth = ctk.CTkComboBox(det_frame, values=["1 Layer", "2 Layers", "3 Layers"], width=140)
        self.det_depth.set("2 Layers")
        self.det_depth.pack(side="left", padx=10)
        self.try_decode = ctk.CTkCheckBox(det_frame, text="Try Auto Decode")
        self.try_decode.pack(side="left", padx=20)

        ctk.CTkButton(self.main_frame, text="🔍 Run Smart Detection", fg_color="#FF9100", height=48, font=("Arial", 16, "bold"),
                      command=self.run_smart_detector).pack(pady=15)

        self.det_result = ctk.CTkTextbox(self.main_frame, height=320, font=("Consolas", 13))
        self.det_result.pack(fill="both", expand=True, padx=40, pady=10)

    def run_smart_detector(self):
        data = self.det_input.get("1.0", tk.END).strip()
        if not data: return
        depth = int(self.det_depth.get()[0])
        try_auto = self.try_decode.get()

        result = "🔍 Smart AI Multi-Layer Detector\n"
        result += "=" * 55 + "\n\n"
        entropy = -sum(p * math.log2(p) for p in [data.count(c)/len(data) for c in set(data)] if p > 0) if data else 0
        result += f"Entropy: {entropy:.3f} bits/char\n\n"

        current = data
        for layer in range(1, depth + 1):
            detected = self.detect_single(current)
            result += f"Layer {layer}: {detected['type']}\n"
            if try_auto and detected.get('decoded'):
                result += f"   Decoded: {detected['decoded'][:250]}{'...' if len(detected['decoded']) > 250 else ''}\n\n"
                current = detected['decoded']
            else:
                result += "\n"

        self.det_result.delete("1.0", tk.END)
        self.det_result.insert("1.0", result)

    def detect_single(self, text):
        if re.fullmatch(r'^[A-Za-z0-9+/=]+$', text) and len(text) % 4 <= 2:
            try:
                padding = "=" * ((4 - len(text) % 4) % 4)
                decoded = base64.b64decode(text + padding).decode(errors="ignore")
                return {"type": "Base64", "decoded": decoded}
            except:
                return {"type": "Base64 (invalid)", "decoded": None}
        elif re.fullmatch(r'^[0-9a-fA-F\s:]+$', text):
            return {"type": "Hexadecimal", "decoded": None}
        elif re.search(r'&#?\w+;', text):
            try:
                decoded = html.unescape(text)
                return {"type": "HTML Entity", "decoded": decoded}
            except:
                return {"type": "HTML Entity", "decoded": None}
        elif "%" in text and re.search(r'%[0-9a-fA-F]{2}', text):
            try:
                decoded = urllib.parse.unquote(text)
                return {"type": "URL Encoded", "decoded": decoded}
            except:
                return {"type": "URL Encoded", "decoded": None}
        else:
            return {"type": "Unknown / Plain Text", "decoded": None}

    # ====================== URL (مختصرة) ======================
    def load_url(self):
        self.clear_main()
        mv, input_txt, file_var, line_check = self.build_input_area()
        ctk.CTkLabel(self.main_frame, text="URL Encode / Decode", font=("Arial", 20, "bold")).pack(pady=15)

        self.url_mode = ctk.StringVar(value="Encode")
        f = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        f.pack(pady=8)
        ctk.CTkRadioButton(f, text="Encode", variable=self.url_mode, value="Encode").pack(side="left", padx=30)
        ctk.CTkRadioButton(f, text="Decode", variable=self.url_mode, value="Decode").pack(side="left", padx=30)

        output_txt = ctk.CTkTextbox(self.main_frame, height=220, font=("Consolas", 13))
        output_txt.pack(fill="both", expand=True, padx=30, pady=15)

        ctk.CTkButton(self.main_frame, text="Run", fg_color="#FF9100", width=160, height=45,
                      command=lambda: self.run_url(mv, input_txt, file_var, line_check, output_txt)).pack(pady=15)

    def run_url(self, mv, input_txt, file_var, line_check, output_txt):
        data = self.get_data(mv, input_txt, file_var).decode("utf-8", errors="ignore")
        if self.url_mode.get() == "Encode":
            res = urllib.parse.quote(data)
        else:
            res = urllib.parse.unquote(data)
        output_txt.delete("1.0", tk.END)
        output_txt.insert("1.0", res)

if __name__ == "__main__":
    app = CyberDevUtils()
    app.mainloop()