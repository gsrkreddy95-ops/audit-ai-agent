## 🔄 Automatic Conflict Prevention

This repo has **automatic sync** enabled via git hooks. When you push a feature branch, it will:
- Auto-detect if your branch is behind `main`
- Auto-rebase on latest `main`
- Prevent conflicts before they happen

**You don't need to do anything manually!** Just work on your branch and push—git handles the sync automatically.

If auto-rebase fails (rare), you'll see instructions on how to resolve manually.

---

## ⚡ Quick Commands

```bash
# Start the agent
auditmate start

# Stop the agent
auditmate stop

# Restart the agent
auditmate restart

# Check status
auditmate status

# Run in background (daemon mode)
auditmate daemon
```

---

[Rest of README content follows...]
