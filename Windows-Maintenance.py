#!/usr/bin/env python3
"""
==========================================================
  Windows Orphaned SID Cleaner & Administrative Share Manager
==========================================================
This script allows you to:

1. Interactively delete orphaned Windows user SIDs and profiles.
2. Disable/remove Windows administrative shares (C$, D$, ADMIN$, IPC$, etc.)
   and harden IPC$ access.

You can choose which operation to perform from the menu.
Dry-run mode previews actions without making changes.
Automatic elevation to Administrator privileges is handled.
"""

import os
import sys
import ctypes
import shutil
import subprocess
import logging
import datetime
import argparse
import winreg

# -------------------- Constants --------------------
PROFILE_LIST_REG = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"
ADMIN_SHARES = ["C$", "D$", "E$", "F$", "ADMIN$"]
REG_PATH = r"HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
BACKUP_DIR = os.path.join(os.getcwd(), "reg_backups")
LOG_DIR = os.path.join(os.getcwd(), "logs")
LOG_FILE = None  # Global log file handle

# -------------------- Logging --------------------
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "delete_sid_log.txt")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log(msg):
    print(msg)
    logging.info(msg)

def init_logging():
    global LOG_FILE
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logfile = os.path.join(LOG_DIR, f"admin_share_log_{ts}.log")
    LOG_FILE = open(logfile, "w", encoding="utf-8")
    print_safe(f"Logging enabled. Log file: {logfile}")

def print_safe(msg):
    try:
        print(msg)
    except Exception:
        pass
    log(msg)
    if LOG_FILE:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        LOG_FILE.write(f"[{ts}] {msg}\n")
        LOG_FILE.flush()

# -------------------- Admin Check --------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    try:
        python_exe = sys.executable
        script = os.path.abspath(sys.argv[0])
        args = []
        for a in sys.argv[1:]:
            if any(ch.isspace() for ch in a) or '"' in a:
                safe = a.replace('"', '\\"')
                args.append(f'"{safe}"')
            else:
                args.append(a)
        params = " ".join(args)
        lpParameters = f'"{script}" {params}'.strip()
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", python_exe, lpParameters, None, 1)
        return int(ret) > 32
    except Exception as e:
        print(f"[ERROR] Failed to elevate privileges: {e}")
        return False

# -------------------- Helper Functions (SID) --------------------
def get_current_user_sid():
    try:
        result = subprocess.run(['wmic', 'useraccount', 'where', f'name="{os.getlogin()}"', 'get', 'sid'], capture_output=True, text=True)
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip() and 'SID' not in line]
        if lines:
            return lines[0]
    except Exception as e:
        log(f"Error getting current user SID: {e}")
    return None

def list_profile_sids():
    sids = []
    try:
        hive = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        key = winreg.OpenKey(hive, PROFILE_LIST_REG, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        i = 0
        while True:
            try:
                sids.append(winreg.EnumKey(key, i))
                i += 1
            except OSError:
                break
        key.Close()
        hive.Close()
    except Exception as e:
        log(f"Error reading ProfileList: {e}")
    return sids

def get_profile_path(sid):
    try:
        hive = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        key = winreg.OpenKey(hive, PROFILE_LIST_REG, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        subkey = winreg.OpenKey(key, sid)
        path, _ = winreg.QueryValueEx(subkey, "ProfileImagePath")
        subkey.Close()
        key.Close()
        hive.Close()
        return path
    except FileNotFoundError:
        return None

def account_exists(sid):
    try:
        result = subprocess.run(['wmic', 'useraccount', 'get', 'name,sid'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if sid in line:
                return True
    except Exception as e:
        log(f"Error checking account existence: {e}")
    return False

def delete_registry_sid(sid, dry_run=False, current_user_sid=None):
    if sid == current_user_sid:
        log("Refusing to delete the current user's SID from registry!")
        return
    if dry_run:
        log(f"[dry-run] Would delete registry key: HKLM\\{PROFILE_LIST_REG}\\{sid}")
        return
    try:
        hive = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        key = winreg.OpenKey(hive, PROFILE_LIST_REG, 0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.DeleteKey(key, sid)
        log(f"Deleted registry key: HKLM\\{PROFILE_LIST_REG}\\{sid}")
    except FileNotFoundError:
        log("SID registry key not found.")
    except PermissionError as e:
        log(f"PermissionError deleting registry key: {e}")
    finally:
        try: key.Close()
        except: pass
        try: hive.Close()
        except: pass

def delete_profile_folder(path, dry_run=False, current_user_sid=None):
    if not path:
        log("No profile path provided.")
        return
    expanded = os.path.expandvars(path)
    if not os.path.exists(expanded):
        log(f"Profile folder does not exist: {expanded}")
        return
    allowed_base = os.path.join(os.path.abspath(os.sep), "Users")
    if not os.path.abspath(expanded).lower().startswith(allowed_base.lower()):
        log(f"Refusing to delete folder outside C:\\Users: {expanded}")
        return
    # Prevent deleting current user's folder
    current_sid_path = get_profile_path(current_user_sid)
    if current_sid_path and os.path.abspath(expanded).lower() == os.path.abspath(current_sid_path).lower():
        log("Refusing to delete current user's profile folder!")
        return
    if dry_run:
        log(f"[dry-run] Would delete profile folder: {expanded}")
        return
    try:
        shutil.rmtree(expanded)
        log(f"Deleted profile folder: {expanded}")
    except Exception as e:
        log(f"Error deleting profile folder {expanded}: {e}")

# -------------------- Helper Functions (Admin Shares) --------------------
def run(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    except Exception as e:
        class Dummy:
            def __init__(self, rc, out, err):
                self.returncode = rc
                self.stdout = out
                self.stderr = err
        return Dummy(1, "", str(e))
    return res

def export_registry_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(BACKUP_DIR, f"LanmanServer_Parameters_{ts}.reg")
    cmd = f'reg export "{REG_PATH}" "{out_file}" /y'
    res = run(cmd)
    if res.returncode == 0:
        return out_file
    else:
        raise RuntimeError(f"Failed to export registry: {res.stderr.strip() or res.stdout.strip()}")

def add_registry_value(name, value):
    cmd = f'reg add "{REG_PATH}" /v {name} /t REG_DWORD /d {value} /f'
    return run(cmd)

def delete_share(share):
    cmd = f'net share {share} /delete'
    return run(cmd)

def list_shares():
    return run("net share")

def restart_lanmanserver():
    stop = run("sc stop lanmanserver")
    start = run("sc start lanmanserver")
    return stop, start

def restrict_ipc_permissions():
    cmd = 'net share IPC$ /grant:Administrators,FULL /REMARK:"Restricted to Admins only"'
    res = run(cmd)
    if res.returncode == 0:
        print_safe("IPC$ share permissions restricted to Administrators.")
    else:
        print_safe(f"Failed to restrict IPC$: {res.stderr.strip() or res.stdout.strip()}")

def block_ipc_smb():
    rules = [
        ('Block SMB TCP 445', '445', 'TCP'),
        ('Block SMB TCP 139', '139', 'TCP'),
        ('Block SMB UDP 445', '445', 'UDP'),
        ('Block SMB UDP 139', '139', 'UDP')
    ]
    for name, port, proto in rules:
        cmd = f'netsh advfirewall firewall add rule name="{name}" dir=in action=block protocol={proto} localport={port}'
        res = run(cmd)
        if res.returncode == 0:
            print_safe(f"Firewall rule applied: {name}")
        else:
            print_safe(f"Failed to apply firewall rule {name}: {res.stderr.strip() or res.stdout.strip()}")

# -------------------- Orphaned SID Cleanup --------------------
def orphaned_sid_cleanup(dry_run=False):
    current_sid = get_current_user_sid()
    print_safe("\n=== Orphaned SID Cleanup ===")
    log(f"Current user SID: {current_sid}")

    sids = list_profile_sids()
    log(f"Found {len(sids)} SIDs in ProfileList.")

    orphaned_sids = []
    for sid in sids:
        if sid == current_sid:
            log(f"Skipping current user SID: {sid}")
            continue
        if not account_exists(sid):
            orphaned_sids.append(sid)

    log(f"Detected {len(orphaned_sids)} orphaned SIDs (excluding current user).")

    for sid in orphaned_sids:
        profile_path = get_profile_path(sid)
        log(f"\nOrphaned SID: {sid}")
        log(f"Profile folder: {profile_path}")
        while True:
            choice = input("Delete this SID and its profile? (yes/NO/skip all remaining) ").strip().lower()
            if choice == "yes":
                delete_registry_sid(sid, dry_run=dry_run, current_user_sid=current_sid)
                delete_profile_folder(profile_path, dry_run=dry_run, current_user_sid=current_sid)
                break
            elif choice == "no":
                log(f"Skipped deletion of SID: {sid}")
                break
            elif choice == "skip all remaining":
                log("User chose to skip all remaining orphaned SIDs.")
                return
            else:
                print("Please enter 'yes', 'no', or 'skip all remaining'.")

    log("Orphaned SID interactive cleanup completed.")

# -------------------- Admin Share Cleanup --------------------
def admin_share_cleanup(dry_run=False, force=False):
    print_safe("\n=== Administrative Share Cleanup ===")
    print_safe("Dry-run mode is " + ("enabled" if dry_run else "disabled"))

    print_safe("=== Backup registry (LanmanServer Parameters) ===")
    try:
        backup_file = export_registry_backup()
        print_safe(f"Registry exported to: {backup_file}")
    except Exception as e:
        print_safe(f"Failed to export registry: {e}")
        if not force:
            print_safe("Aborting.")
            return

    print_safe("\n=== Current shares (before) ===")
    cur = list_shares()
    print_safe(cur.stdout.strip() if cur.returncode == 0 else cur.stderr.strip() or cur.stdout.strip())

    if dry_run:
        print_safe("\nDry-run enabled. No changes will be made. Exiting.")
        return

    if not force:
        confirm = input("\nProceed to permanently disable admin shares and delete them now? (yes/no): ").strip().lower()
        if confirm not in ("y", "yes"):
            print_safe("Aborted by user.")
            return

    print_safe("\n=== Setting registry values to prevent auto-creation of admin shares ===")
    for name in ("AutoShareWks", "AutoShareServer"):
        res = add_registry_value(name, 0)
        if res.returncode == 0:
            print_safe(f"Set {name} = 0")
        else:
            print_safe(f"Failed to set {name}: {res.stderr.strip() or res.stdout.strip()}")

    print_safe("\n=== Removing administrative shares now ===")
    for share in ADMIN_SHARES:
        res = delete_share(share)
        if res.returncode == 0:
            print_safe(f"Removed share: {share}")
        else:
            out = (res.stdout or "") + (res.stderr or "")
            print_safe(f"{share}: {out.strip() or '(no output, maybe not present)'}")

    print_safe("\n=== Restarting LanmanServer (Server service) to apply registry changes ===")
    stop_res, start_res = restart_lanmanserver()
    print_safe(f"sc stop output:\n{stop_res.stdout or stop_res.stderr}")
    print_safe(f"sc start output:\n{start_res.stdout or start_res.stderr}")

    print_safe("\n=== Hardening IPC$ share ===")
    restrict_ipc_permissions()
    block_ipc_smb()

    print_safe("\n=== Current shares (after) ===")
    cur2 = list_shares()
    print_safe(cur2.stdout.strip() if cur2.returncode == 0 else cur2.stderr.strip() or cur2.stdout.strip())

    print_safe("\n=== Finished ===")
    try:
        print_safe(f"A registry backup was saved at: {backup_file}")
        print_safe("To restore previous registry settings, run:")
        print_safe(f'  reg import "{backup_file}"')
        print_safe("Then restart the 'Server' service (LanmanServer) or reboot the machine.")
    except UnboundLocalError:
        print_safe("No registry backup path available (export may have failed earlier).")

# -------------------- Startup Banner --------------------
def startup_banner(current_sid):
    print("===================================================")
    print("Windows Maintenance Script by Sid Gifari")
    print("From Gifari Industries - BD Cyber Security Team")
    print("===================================================")
    print(f"Current logged-in user SID: {current_sid}")
    print("⚠ WARNING: Your current account cannot be deleted!")
    print("All deletion operations will skip this user automatically.")
    print("===================================================\n")

# -------------------- Interactive Menu --------------------
def interactive_menu(current_sid):
    dry_run = False
    while True:
        print(f"Current logged-in user SID: {current_sid}")
        print("1: Orphaned SID Cleanup")
        print("2: Administrative Share Cleanup")
        print("3: Both (SID + Admin Share Cleanup)")
        print("4: Toggle Dry-Run Mode (currently {})".format("ON" if dry_run else "OFF"))
        print("0: Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            orphaned_sid_cleanup(dry_run=dry_run)
        elif choice == "2":
            admin_share_cleanup(dry_run=dry_run, force=False)
        elif choice == "3":
            orphaned_sid_cleanup(dry_run=dry_run)
            admin_share_cleanup(dry_run=dry_run, force=False)
        elif choice == "4":
            dry_run = not dry_run
            print_safe("Dry-run mode is now " + ("ENABLED" if dry_run else "DISABLED"))
        elif choice == "0":
            print_safe("Exiting.")
            break
        else:
            print("Invalid choice. Please enter 0-4.")

# -------------------- Main --------------------
if __name__ == "__main__":
    if not is_admin():
        print("[INFO] Attempting to restart script with Administrator privileges...")
        elevated_started = run_as_admin()
        if elevated_started:
            sys.exit(0)
        else:
            print("[ERROR] Could not elevate to Administrator. Exiting.")
            sys.exit(1)

    init_logging()

    # Get current user SID
    current_sid = get_current_user_sid()
    startup_banner(current_sid)  # Display the warning banner

    try:
        interactive_menu(current_sid)
    except Exception as exc:
        print_safe("ERROR: " + str(exc))
        sys.exit(1)
    finally:
        if LOG_FILE:
            try:
                LOG_FILE.close()
            except Exception:
                pass
