import psutil
import datetime
import platform
import socket
import time
import requests
import sys
import os
import winreg
import json
import tkinter as tk
from tkinter import simpledialog

# ==========================================
# Config (Entry ID เดิม)
# ==========================================
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSe0R69OiAmvmW8g3injk6KqMHEe5p8g5MJhZuiKnoyGh3koug/formResponse"

FORM_DATA = {
    "timestamp": "entry.2132674211",
    "asset_id":  "entry.665082357", 
    "hostname":  "entry.145730339",
    "ip":        "entry.591022999",
    "os":        "entry.496466144",
    "cpu":       "entry.320153514",
    "ram":       "entry.1874055240",
    "c_used":    "entry.1064799824",
    "c_free":    "entry.1346164153",
    "d_used":    "entry.380997161",
    "d_free":    "entry.1405734931",
    "e_used":    "entry.1727260328", 
    "e_free":    "entry.1419489167"
}

INTERVAL = 10
CONFIG_FILE = "monitor_config.json"

# ==========================================
# ฟังก์ชันดึง Windows Version แบบเจาะลึก
# ==========================================
def get_detailed_os():
    try:
        # ถ้าไม่ใช่ Windows ให้ใช้คำสั่งเดิม
        if platform.system() != "Windows":
            return f"{platform.system()} {platform.release()}"

        # เปิด Registry: HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            
            # 1. ชื่อ Product (เช่น Windows 10 Pro)
            product_name = winreg.QueryValueEx(key, "ProductName")[0]
            
            # 2. รุ่น Version (เช่น 22H2, 23H2, 24H2)
            try:
                display_version = winreg.QueryValueEx(key, "DisplayVersion")[0]
            except FileNotFoundError:
                # เผื่อเป็น Windows 10 รุ่นเก่ามาก
                display_version = winreg.QueryValueEx(key, "ReleaseId")[0]

            # 3. แก้บั๊ก: บางที Windows 11 ยังเก็บชื่อตัวเองว่า Windows 10 ใน Registry
            current_build = int(winreg.QueryValueEx(key, "CurrentBuild")[0])
            if "Windows 10" in product_name and current_build >= 22000:
                product_name = product_name.replace("Windows 10", "Windows 11")

            return f"{product_name} {display_version}"

    except Exception as e:
        # ถ้าดึงไม่ได้จริงๆ ให้ใช้ค่า Default
        return f"{platform.system()} {platform.release()}"

# ==========================================
#  ฟังก์ชันจัดการ Asset ID
# ==========================================
def get_asset_id():
    base_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    config_path = os.path.join(base_path, CONFIG_FILE)

    # 1. ลองอ่านไฟล์ Config 
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("asset_id", "Unknown")
        except:
            pass

    # 2. ถ้าไม่มีไฟล์ ให้เด้ง Popup ถาม
    root = tk.Tk()
    root.withdraw() 
    root.attributes('-topmost', True) 
    
    asset_id = None
    while not asset_id:
        # เพิ่ม initialvalue
        asset_id = simpledialog.askstring(
            "IT Support Setup", 
            "กรุณากรอกเลขครุภัณฑ์: \n(Asset ID / Hostname)",
            initialvalue="7440-001-0001/"  # <--- ค่าเริ่มต้นที่จะโชว์ในกล่อง
        )
        
        if asset_id is None: # กดยกเลิก
             sys.exit() 
    
    # 3. บันทึกลงไฟล์
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({"asset_id": asset_id}, f)
    except Exception as e:
        print(f"Error saving config: {e}")

    return asset_id

def add_to_startup():
    try:
        file_path = os.path.realpath(sys.argv[0])
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "IT_Monitor_Agent", 0, winreg.REG_SZ, file_path)
        key.Close()
    except: pass

def get_drive_info(drive_letter):
    try:
        path = f"{drive_letter}:\\"
        partitions = [p.mountpoint for p in psutil.disk_partitions()]
        if path not in partitions: return 0, 0 
        usage = psutil.disk_usage(path)
        return usage.percent, round(usage.free / (1024**3), 1)
    except: return 0, 0

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: return "127.0.0.1"

def main():
    my_asset_id = get_asset_id()
    add_to_startup()
    
    while True:
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            c_used, c_free = get_drive_info('C')
            d_used, d_free = get_drive_info('D')
            e_used, e_free = get_drive_info('E')
            
            # เรียกฟังก์ชัน OS
            detailed_os = get_detailed_os()

            payload = {
                FORM_DATA["asset_id"]:  my_asset_id,
                FORM_DATA["timestamp"]: str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                FORM_DATA["hostname"]:  platform.node(),
                FORM_DATA["ip"]:        get_ip(),
                
                # ส่งค่า OS ใหม่ไปแทนที่เดิม
                FORM_DATA["os"]:        detailed_os, 
                
                FORM_DATA["cpu"]:       str(cpu),
                FORM_DATA["ram"]:       str(ram),
                FORM_DATA["c_used"]:    str(c_used),
                FORM_DATA["c_free"]:    str(c_free),
                FORM_DATA["d_used"]:    str(d_used) if d_used > 0 else "-",
                FORM_DATA["d_free"]:    str(d_free) if d_free > 0 else "-",
                FORM_DATA["e_used"]:    str(e_used) if e_used > 0 else "-",
                FORM_DATA["e_free"]:    str(e_free) if e_free > 0 else "-"
            }
            
            requests.post(FORM_URL, data=payload)
                
        except Exception:
            pass
            
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()