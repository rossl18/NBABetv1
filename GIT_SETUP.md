# Git Setup for Windows

## ✅ Git is Installed!

Git is installed on your system at: `C:\Program Files\Git\bin\git.exe`

However, it's not in your PATH, so PowerShell can't find it.

## Quick Fix (Current Session Only)

For this PowerShell session, run:
```powershell
$env:PATH += ";C:\Program Files\Git\bin"
```

Then verify:
```powershell
git --version
```

## Permanent Fix (Recommended)

To make Git available in all future PowerShell sessions:

### Option 1: Add to System PATH (Best)

1. Press `Win + X` → **System**
2. Click **Advanced system settings**
3. Click **Environment Variables**
4. Under **System variables**, find **Path**
5. Click **Edit**
6. Click **New**
7. Add: `C:\Program Files\Git\bin`
8. Click **OK** on all dialogs
9. **Restart PowerShell** for changes to take effect

### Option 2: Use Git Bash Instead

Git comes with Git Bash, which has git in PATH:
- Open **Git Bash** (search in Start menu)
- Navigate to your project: `cd /c/Users/rnl31/Desktop/NBABetv1`
- Use git commands normally

### Option 3: Use Full Path

You can use the full path to git:
```powershell
& "C:\Program Files\Git\bin\git.exe" --version
```

## For Deployment

I've already added Git to PATH for this session, so you can proceed with:

```powershell
cd c:\Users\rnl31\Desktop\NBABetv1
git init
git add .
git commit -m "Initial commit: NBA Betting Dashboard"
```

**Note**: If you close PowerShell and open a new one, you'll need to either:
- Add Git to PATH permanently (Option 1 above)
- Or run the `$env:PATH += ";C:\Program Files\Git\bin"` command again
