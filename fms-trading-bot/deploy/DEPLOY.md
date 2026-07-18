# Deploying the FMS bot on a free VPS

## Option A — OANDA mode on Linux (free forever, simplest)

No Windows, no MT5. Create the Oracle Cloud Always-Free Ubuntu VM exactly as
described in `pocket-option-bot/deploy/DEPLOY.md` (section 1), then:

```bash
ssh -i /path/to/key ubuntu@<PUBLIC_IP>
sudo apt-get install -y git
git clone https://github.com/fatalibuilders-cloud/AI_Memory_Open.git
cd AI_Memory_Open/fms-trading-bot
bash deploy/setup-vps.sh
nano .env      # TG_BOT_TOKEN, TG_PASSWORD, OANDA_* — keep OANDA_ENV=practice
.venv/bin/python main.py            # foreground test; /login from your phone
sudo systemctl start fms-bot
journalctl -u fms-bot -f            # live logs
```

Both bots (this one and pocket-option-bot) fit comfortably on one free VM.
Limitation: OANDA has forex + metals but no stocks — for stocks use Option B.

## Option B — MT5 mode on a free Windows VPS

The MetaTrader 5 Python API only runs on Windows, next to an installed MT5
terminal. Two free routes:

| Route | Free for | Best when |
|---|---|---|
| **AWS free tier** (`t3.micro` Windows Server) | 12 months | Starting today, no broker commitment |
| **Broker free VPS** (Exness, IC Markets, XM, ...) | As long as you meet their deposit/volume condition | You've picked a broker and funded a live account |

Broker VPSes are pre-tuned for MT5 — once you're live, ask your broker's
support for their free VPS terms and just run `setup-windows.ps1` there.
Below is the AWS route, which works with a demo account.

## 1. Launch the free Windows instance (once)

1. Sign up at https://aws.amazon.com/free (card required; free tier isn't charged).
2. Console → **EC2 → Launch instance**:
   - AMI: **Microsoft Windows Server 2022 Base**
   - Instance type: **t3.micro** (free-tier eligible)
   - Key pair: create one and download the `.pem` (needed to decrypt the password)
   - Storage: 30 GB gp3 (free-tier limit)
3. When it's running: **Connect → RDP client → Get password** (upload the
   `.pem`), then connect with any RDP app — *Microsoft Remote Desktop* works
   from your phone too.

> t3.micro has 1 GB RAM — snug. Keep MT5 lean: close all charts, remove
> unused symbols from Market Watch (right-click → Hide All), and don't run
> anything else on the box.

## 2. Install MT5 + the bot (inside the RDP session)

1. Install MetaTrader 5 from https://www.metatrader5.com, log into your
   **demo account**, and click the **Algo Trading** toolbar button so it's ON.
2. Install git from https://git-scm.com/download/win (defaults are fine).
3. Open **PowerShell as Administrator**:

```powershell
cd $HOME
git clone https://github.com/fatalibuilders-cloud/AI_Memory_Open.git
cd AI_Memory_Open\fms-trading-bot
Set-ExecutionPolicy -Scope Process Bypass -Force
.\deploy\setup-windows.ps1
```

## 3. Configure and start

```powershell
notepad .env     # TG_BOT_TOKEN, TG_PASSWORD, MT5_LOGIN/PASSWORD/SERVER
.\.venv\Scripts\python.exe main.py        # foreground test
```

On your phone, open your Telegram bot: `/login <password>` → `/status`.
If that works, Ctrl+C the foreground run and start it for good:

```powershell
Start-ScheduledTask -TaskName FMSTradingBot
Get-Content .\bot.log -Tail 50 -Wait       # live logs
```

From here on you shouldn't need RDP — everything day-to-day (arm/disarm,
positions, closing trades, risk) happens from your phone via Telegram.
Send `/resume` when you're ready for it to trade.

## Maintenance

- **Update the bot**: `git pull` in the repo, then
  `Stop-ScheduledTask -TaskName FMSTradingBot; Start-ScheduledTask -TaskName FMSTradingBot`
- **After the 12 free months**, either move to your broker's free VPS or a
  ~$10/mo Windows VPS — the same setup script works anywhere.
- **AWS billing alarm**: set one up (Billing → Budgets → $1 budget) so you're
  emailed if anything ever starts costing money.
