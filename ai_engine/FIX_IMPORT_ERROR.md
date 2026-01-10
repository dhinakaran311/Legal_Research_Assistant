# Fix for "ModuleNotFoundError: No module named 'config'"

## Problem

When running `uvicorn src.main:app` from the `ai_engine` directory, you get:
```
ModuleNotFoundError: No module named 'config'
```

This happens because Python can't find the modules in the `src` directory.

## Solution

There are several ways to fix this:

### ✅ **Solution 1: Use the Startup Script (Easiest)**

**PowerShell:**
```powershell
.\start_server.ps1
```

**Windows Command Prompt:**
```cmd
start_server.bat
```

These scripts automatically set `PYTHONPATH` to include the `src` directory.

### ✅ **Solution 2: Set PYTHONPATH Manually (PowerShell)**

```powershell
$env:PYTHONPATH = "src"
uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
```

### ✅ **Solution 3: Set PYTHONPATH Manually (CMD)**

```cmd
set PYTHONPATH=src
uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
```

### ✅ **Solution 4: Run from src Directory**

```bash
cd src
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

### ✅ **Solution 5: Install as Package (For Development)**

```bash
pip install -e .
```

Then run:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
```

## Why This Happens

When you run `uvicorn src.main:app`, Python needs to:
1. Find the `src` directory
2. Import `main` from `src`
3. Import `config` from `src` (inside `main.py`)

Python looks for modules in:
- The current directory
- Directories in `PYTHONPATH`
- Installed packages

Since `src` is not in any of these by default, Python can't find `config`.

Setting `PYTHONPATH=src` tells Python to look in the `src` directory for modules.

## Quick Fix

**The fastest way is to use the startup script:**

```powershell
.\start_server.ps1
```

This script:
- Sets `PYTHONPATH` to `src`
- Activates virtual environment (if it exists)
- Runs uvicorn with correct settings

---

**Status:** ✅ **Fixed** - Use one of the solutions above to run the server!
