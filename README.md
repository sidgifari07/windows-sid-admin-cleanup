# ⚠️ Windows Orphaned SID & Administrative Share Cleaner ⚠️

**By Sid Gifari – Gifari Industries, BD Cyber Security Team**

> Windows Maintenance Utility – Orphaned SID Removal & Admin Share Hardening


---

## ⚠️ Warning – Use With Caution

🚨 This script modifies Windows system settings, including user profiles, registry keys, and administrative shares.

**Key Risks:**
- ❌ Irreversible deletion of orphaned SIDs and user profile folders.
- ⚠️ **The current user’s account and profile will never be deleted.**
- 🌐 Disabling admin shares may break network access or file sharing.
- 💾 Always backup your registry and important data before running.
- 👀 Use dry-run mode first to preview actions safely.
- 🛡️ Administrator privileges required.

**Use responsibly – the author is not liable for data loss or system issues.**

---

## ✨ Features

### 1. Clean Orphaned SIDs and Profiles
- Detects Windows user SIDs without associated accounts.
- Interactively deletes orphaned registry keys and profile folders.
- Supports dry-run mode for safe previews.
- **Never deletes the current user.**

### 2. Manage Administrative Shares
- Disables/removes default Windows admin shares (C$, D$, ADMIN$, etc.).
- Hardens the IPC$ share for Administrators only.
- Optionally blocks SMB ports via Windows Firewall for added security.
- Automatically backs up registry settings before changes.

### 3. Additional Features
- Automatic elevation to Administrator if not already running as admin.
- Interactive, easy-to-use menu.
- Detailed timestamped logs for auditing.
- Safety checks to prevent deleting folders outside `C:\Users`.

---

## 🎯 Use Cases
- Clean up orphaned user profiles on enterprise systems.
- Enhance Windows host security by removing unnecessary admin shares.
- Prepare machines for secure decommissioning or repurposing.

---

## 🛠 Requirements
- Windows 10/11 or Server 2016/2019/2022
- Python 3.x
- Administrator privileges

---

## 💻 Usage

```bash
python Windows-Maintenance.py
```

**Instructions:**
1. Follow the interactive menu.
2. Choose to clean orphaned SIDs, manage admin shares, or both.
3. Use dry-run mode to safely preview changes.

---

## 🚀 Getting Started

**Clone the repository:**
```bash
git clone https://github.com/sidgifari07/windows-sid-admin-cleanup.git
cd windows-sid-admin-cleanup
```

**Run the script:**
```bash
python Windows-Maintenance.py
```
> ⚠ Run as Administrator for full functionality.

**Interactive Menu Example:**
```
===============================================
Windows Maintenance Menu Script By Sid Gifari
From Gifari Industries - BD Cyber Security Team
===============================================
1: Orphaned SID Cleanup
2: Administrative Share Cleanup
3: Both (SID + Admin Share Cleanup)
4: Toggle Dry-Run Mode (currently OFF)
0: Exit
```

**Registry Backup:**
- Auto-created in `reg_backups` folder.
- To restore:
```bash
reg import "reg_backups\<backup-file>.reg"
```
- Restart the `Server` service or reboot.

---

## 📸 Screenshots

**Menu:**
![Menu Screenshot](https://github.com/user-attachments/assets/c49f3e9e-6cd6-4350-a244-004b5c3ba50b)

**SID Cleanup:**
![SID Cleanup Screenshot](https://github.com/user-attachments/assets/ed157f1b-50b7-4141-a6dd-cf73a9f5af92)

**Admin Share Cleanup:**
![Admin Share Cleanup Screenshot](https://github.com/user-attachments/assets/55c9ca24-ee78-4316-8f1b-efeb00349348)

---

## ⚠️ Disclaimer
Use this tool with caution. Always verify actions and backups before modifying system settings.
**The current user’s account and profile are never deleted.**

---

💡 **Tip:** Always start with dry-run mode to preview changes safely!
