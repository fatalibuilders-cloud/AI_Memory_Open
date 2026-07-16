# Deploying the Pocket Option bot on Oracle Cloud (free forever)

Oracle's Always Free tier gives you a Linux VM that never expires and never
charges (the card at sign-up is for identity verification only). Total setup
time: ~30 minutes, most of it waiting for the VM.

## 1. Create the free VM (once)

1. Sign up at https://signup.cloud.oracle.com (pick your **home region**
   carefully — you can't change it later; a region near you is fine).
2. Console → **Compute → Instances → Create instance**.
3. Image: **Ubuntu 24.04** (or 22.04).
4. Shape: click *Change shape* → **Ampere / VM.Standard.A1.Flex** —
   anything up to 4 OCPU / 24 GB is free. 1 OCPU / 6 GB is plenty for this bot.
   - If A1 capacity is "out of host capacity", retry later or use the
     always-free **VM.Standard.E2.1.Micro** (x86, 1 GB — still enough).
5. Under *Add SSH keys*, download/generate the private key — you need it to log in.
6. Create, wait for the instance to be **Running**, note its **public IP**.

## 2. Install the bot

From your computer (or phone with an SSH app like Termius):

```bash
ssh -i /path/to/private-key ubuntu@<PUBLIC_IP>

# on the VM:
sudo apt-get install -y git
git clone https://github.com/fatalibuilders-cloud/AI_Memory_Open.git
cd AI_Memory_Open/pocket-option-bot
bash deploy/setup-vps.sh
```

## 3. Configure and start

```bash
nano .env          # paste your PO_SSID (README step 2), keep PO_DEMO=1
.venv/bin/python main.py    # foreground test — Ctrl+C once you see it connect
sudo systemctl start pocket-bot
journalctl -u pocket-bot -f    # live logs
```

The systemd service starts the bot on every boot and restarts it if it
crashes. Update to a newer version later with:

```bash
cd ~/AI_Memory_Open && git pull && sudo systemctl restart pocket-bot
```

## Notes & gotchas

- **SSID + different IP**: Pocket Option sessions are sometimes invalidated
  when reused from a datacenter IP. If you see repeated "Auth timed out",
  re-capture a fresh SSID from your browser and update `.env`. If it keeps
  happening, run this particular bot on a home machine instead.
- **Keep PO_DEMO=1** until the bot has traded demo for at least 1–2 weeks and
  you like what the logs show.
- The VM's firewall: outbound WebSocket needs no extra rules; you don't need
  to open any inbound ports beyond SSH (22), which Oracle opens by default.
