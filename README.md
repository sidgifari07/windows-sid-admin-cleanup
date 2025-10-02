# ⚠️ Windows Orphaned SID & Administrative Share Cleaner ⚠️

**By Sid Gifari – Gifari Industries, BD Cyber Security Team**

> Windows Maintenance Utility – Orphaned SID Removal & Admin Share Hardening

---

## 📌 Table of Contents
- [⚠️ Warning – Use With Caution](#-warning--use-with-caution)
- [✨ Features](#-features)
- [🎯 Use Cases](#-use-cases)
- [🛠 Requirements](#-requirements)
- [💻 Usage](#-usage)
- [🚀 Getting Started](#-getting-started)
- [⚠️ Disclaimer](#-disclaimer)

---

## ⚠️ Warning – Use With Caution

🚨 This tool modifies Windows system settings, including user profiles, registry keys, and administrative shares.

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
- Interactively deletes orphaned registry keys and user profile folders.
- Supports dry-run mode for safe previews.
- **Current user is never deleted.**

### 2. Manage Administrative Shares
- Disables and removes default Windows admin shares (C$, D$, ADMIN$, etc.).
- Hardens the IPC$ share by restricting access to Administrators.
- Optionally blocks SMB ports via Windows Firewall for added security.
- Creates a backup of registry settings before making changes.

### 3. Additional Features
- Automatic elevation to Administrator privileges if not already running as admin.
- Interactive menu for easy navigation between tasks.
- Detailed logging with timestamped files for auditing.
- Safe operations with checks to prevent accidental deletion outside `C:\Users`.

---

## 🎯 Use Cases
- Cleaning up user profiles on enterprise systems.
- Enhancing Windows host security by removing unnecessary administrative shares.
- Preparing machines for secure decommissioning or repurposing.

---

## 🛠 Requirements
- Windows 10/11, Server 2016/2019/2022
- Python 3.x
- Administrator privileges

---

## 💻 Usage

```bash
python Windows-Maintenance.py
```

Follow the interactive prompts to:
1. Clean orphaned SIDs.
2. Manage administrative shares.
3. Preview changes with dry-run mode before applying.

---

## 🚀 Getting Started

1. **Clone the Repository**
```bash
git clone https://github.com/sidgifari07/windows-sid-admin-cleanup.git
cd windows-sid-admin-cleanup
```

2. **Run the Script**
```bash
python Windows-Maintenance.py
```
- Use an **elevated Command Prompt** (Run as Administrator) for full functionality.

3. **Interactive Menu**
- Example menu:
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
- Select your desired operation and follow on-screen prompts.
- Dry-run mode previews all changes without modifying the system.

4. **Registry Backup**
- A backup is automatically created in the `reg_backups` folder before removing admin shares.
- To restore:
```bash
reg import "reg_backups\<backup-file>.reg"
```
- Then restart the `Server` service (LanmanServer) or reboot.

**Screenshots:**

![Menu Screenshot](https://github.com/user-attachments/assets/55d3600a-169e-471a-92ef-5cc31e1c48bb)

![SID Cleanup Screenshot](https://github.com/user-attachments/assets/0c85b036-082a-413c-9367-ee1acb2162bd)

![Admin Share Cleanup Screenshot](https://github.com/user-attachments/assets/bf2ef8dc-121d-4fda-b376-a0997bb6161c)

---

## ⚠️ Disclaimer
Use this tool with caution. Always verify actions and backups before modifying system settings.
**The current user’s account and profile are never deleted.**
