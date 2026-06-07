# Running the SOL Sniper Bot 24/7 on a Windows PC

This guide gets the bot trading live on an always-on Windows PC. The **backend
does all the trading** — the dashboard is optional, just for watching.

> ⚠️ Real money, real risk. Use a dedicated burner wallet with only what you can
> afford to lose. No bot can guarantee profit — "95% every time" does not exist.
> With safety filters ON the bot intentionally skips almost all brand-new tokens
> (they are mostly rugs/honeypots), so it may buy rarely or not at all.

---

## 1. Install prerequisites (one time)

1. **Python 3.12** — https://www.python.org/downloads/
   - During install, CHECK **"Add python.exe to PATH"**.
2. **Node.js LTS** (only if you want the dashboard) — https://nodejs.org
3. Verify in a new Command Prompt:
   ```
   python --version
   node --version
   ```

## 2. Get the project

Unzip `sol-sniper-bot.zip` somewhere permanent, e.g. `C:\sol-sniper`.
(You should end up with `C:\sol-sniper\backend`, `C:\sol-sniper\frontend`, etc.)

## 3. Configure your wallet + RPC

1. In `C:\sol-sniper\backend`, copy `.env.example` to `.env`.
2. Open `.env` in Notepad and fill in:
   - `SOLANA_RPC_URL` — your **Helius** (or other paid) RPC URL.
     Free tier from https://dashboard.helius.dev works to start, but the free
     **public** RPC will get rate-limited under constant scanning.
   - `SOLANA_WALLET_PRIVATE_KEY` — your **burner** wallet's base58 private key
     (Phantom: create a NEW account → ⋮ → Account Details → Show Private Key).
   - Leave `LIVE_MODE=true`, `AUTO_BUY_ENABLED=true`, `SCANNER_AUTOSTART=true`.
   - `BUY_AMOUNT_SOL=0.02` is your risk per trade — keep it small.
3. Fund the burner wallet with a small amount of SOL (e.g. 0.05–0.2).

## 4. Start the bot

Double-click **`start-bot.bat`** (in `C:\sol-sniper`).

- First run creates the Python venv and installs dependencies (takes a minute).
- Then it launches the backend on http://localhost:8001 and — because
  `SCANNER_AUTOSTART=true` — immediately begins scanning + auto-buying.
- Leave this window open. Closing it (or Ctrl+C) stops the bot.

You'll see log lines like:
```
Scanner auto-started (SCANNER_AUTOSTART=true)
[JUPITER] New token: ...
Auto-buy skip XYZ: Top holder 100.0% > max 30.0%   <- safety filter protecting you
```

### Watch the dashboard (optional)
Double-click **`start-dashboard.bat`**, then open http://localhost:5173.
Verify the header shows your wallet connected and **LIVE** (not Dry-Run).
Confirm it's truly live by checking http://localhost:8001/api/wallet shows
`"is_live": true` and your real `sol_balance`.

## 5. Keep it running 24/7

So the bot survives reboots and stays on:

1. **Disable sleep:** Settings → System → Power → Screen and sleep → set
   "When plugged in, put my device to sleep" to **Never**.
2. **Auto-start on login** (simplest): press `Win+R`, type `shell:startup`,
   Enter, and put a **shortcut to `start-bot.bat`** in that folder. It now
   launches automatically whenever Windows starts.
   - (Advanced: use Task Scheduler → "Run whether user is logged on or not" if
     you want it to start before login.)
3. Make sure your internet connection stays up.

## 6. Stopping / changing settings

- **Stop:** close the `start-bot.bat` window (or Ctrl+C).
- **Change risk/filters:** edit `backend\.env` and restart, or use the
  Settings tab in the dashboard while it runs.
- **Go safe (dry-run):** set `LIVE_MODE=false` in `.env` and restart — it will
  simulate without spending funds.

## Troubleshooting

| Symptom | Fix |
|--------|-----|
| `python is not recognized` | Reinstall Python with "Add to PATH" checked, open a NEW terminal. |
| Balance shows 0 intermittently | Your RPC is rate-limited — use a dedicated Helius/QuickNode key. |
| Header says "No Wallet" / can't go LIVE | `SOLANA_WALLET_PRIVATE_KEY` in `.env` is missing/invalid. |
| Bot never buys anything | Expected with strict filters. Loosening them increases rug risk — there is no safe way to force constant buys. |
| Dashboard can't connect | Make sure `start-bot.bat` (backend on :8001) is running first. |

## Security

- Your `.env` holds your private key — never share it or commit it to git.
- Rotate the Helius API key and burner wallet key if they were ever pasted in chat.
- Use a burner wallet, not your main Phantom.
