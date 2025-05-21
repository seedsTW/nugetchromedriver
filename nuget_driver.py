#!/usr/bin/env python3
import os, zipfile, io, requests, winreg, ctypes
#from packaging.version import Version
from pathlib import Path
import ctypes, shutil
import subprocess

def normalize_version(ver: str, parts: int = 3) -> tuple[int, ...]:
    """
    把「major.minor.build.patch…」格式的字串，轉成只保留前三段的整數 tuple。
    """
    nums = ver.split(".")
    # 只取前 parts 段，若不夠則補 0
    nums = [int(x) for x in nums[:parts]] + [0] * max(0, parts - len(nums))
    return tuple(nums)

def version_ge(v1: str, v2: str) -> bool:
    """
    返回 True 如果 v1 >= v2（以前三段版本號比較）。
    """
    return normalize_version(v1) >= normalize_version(v2)

def get_chrome_version():
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            key = winreg.OpenKey(hive, r"SOFTWARE\Google\Chrome\BLBeacon")
            return winreg.QueryValueEx(key, "version")[0]
        except FileNotFoundError:
            continue
    raise FileNotFoundError("無法從 Registry 找到 Chrome")

def get_version_via_cli(path="chromedriver.exe"):
    out = subprocess.check_output([path, "--version"], stderr=subprocess.DEVNULL)
    # e.g. "ChromeDriver 134.0.6998.9000"
    return out.decode().strip().split()[-1]

def find_chromedriver_exe():
    # 1️⃣ cwd
    cwd = Path.cwd() / "chromedriver.exe"
    if cwd.exists():
        print(cwd )
        print(f"->cwd found!")
        return cwd

    # 2️⃣ 腳本目錄
    script_dir = Path(__file__).resolve().parent / "chromedriver.exe"
    if script_dir.exists():
        print(f"->script dir found!")
        return script_dir

    # 3️⃣ PATH
    exe = shutil.which("chromedriver")
    if exe:
        print(f"->ｐａｔｈ found!")
        return Path(exe)
    else:
        return None

def get_file_version():
    exe_path = find_chromedriver_exe()
    if not exe_path:
        return None

    out = subprocess.check_output([exe_path, "--version"], stderr=subprocess.STDOUT)
    return out.decode().strip().split()[1]
    size = ctypes.windll.version.GetFileVersionInfoSizeW(str(exe_path), None)
 
    if not size:
        return None

    buf = ctypes.create_string_buffer(size)
    ctypes.windll.version.GetFileVersionInfoW(str(exe_path), 0, size, buf)
    lptr, lsize = ctypes.c_void_p(), ctypes.c_uint()
    ctypes.windll.version.VerQueryValueW(buf, r"\\StringFileInfo\\040904b0\\FileVersion",
                                         ctypes.byref(lptr), ctypes.byref(lsize))
    return ctypes.wstring_at(lptr, lsize.value).strip().rstrip('\x00')


def fetch_latest_nuget_version(major):
    url = "https://api.nuget.org/v3-flatcontainer/selenium.webdriver.chromedriver/index.json"
    versions = requests.get(url).json().get("versions", [])
    valid = [v for v in versions if v.startswith(f"{major}.") and "beta" not in v.lower()]
    if not valid:
        raise RuntimeError(f"No ChromeDriver for Chrome {major}")
    #return sorted(valid, key=Version, reverse=True)[0]
    return sorted(valid, key=lambda v: normalize_version(v), reverse=True)[0]

import datetime

def download_and_replace(version, dest="chromedriver.exe"):
    # 如果已經存在舊版，先備份
    if Path(dest).exists():
        old_ver = get_file_version() or "unknown"
        backup_dir = Path("backup")
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"chromedriver_{old_ver}_{timestamp}.exe"
        backup_path = backup_dir / backup_name
        shutil.copy2(dest, backup_path)
        print(f"🔄 Backed up old ChromeDriver → {backup_path}")

    # 下載並解壓新版
    pkg_url = f"https://www.nuget.org/api/v2/package/Selenium.WebDriver.ChromeDriver/{version}"
    resp = requests.get(pkg_url); resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        for member in z.namelist():
            if member.lower().endswith("chromedriver.exe"):
                with open(dest, "wb") as out:
                    out.write(z.read(member))
                print(f"✅ Downloaded and replaced ChromeDriver → {dest}")
                return dest

    raise FileNotFoundError("chromedriver.exe not found inside NuGet package")


def normalize(ver):
    return ".".join(ver.split(".")[:3])

def main():
    print(f"---------------------------------------------------")
    print(f"自動更新 Selenium 的Chrome Driver程式")
    print(f"2025/03/21 V1.0 by 豐翊科技")
    print(f"防火牆打開 *nuget.org   [i.e. trust nuget.org 連線]")
    print(f"---------------------------------------------------")
    chrome_ver = get_chrome_version()
    major = chrome_ver.split(".")[0]
    print(f"偵測本機瀏覽器版本 Detected Chrome {chrome_ver}")

    local_ver = get_file_version()
    print(f"偵測 Local ChromeDriver: {local_ver or 'none'}")

    target_ver = fetch_latest_nuget_version(major)
    print(f"偵測 nuget最新版  Latest compatible ChromeDriver: {target_ver}")

    if local_ver and version_ge(local_ver ,target_ver):
        print("✅ ChromeDriver is up-to-date — no action needed.")
    else:
        print(f"⬇️ Updating ChromeDriver → {target_ver}")
        download_and_replace(target_ver)
        print("✅ chromedriver.exe updated.")

if __name__ == "__main__":
    main()
