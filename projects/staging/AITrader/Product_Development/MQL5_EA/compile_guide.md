# How to Compile FatalibuildersTrader.mq5 in MetaEditor — Step by Step

**Before you start:** `FatalibuildersTrader.mq5` requires **MetaTrader 5**, not MT4. They use different languages (MQL5 vs MQL4) and MT4 cannot open or run this file. If you only have MT4 installed (e.g., "FxPro MT4"), download MT5 separately — Exness offers both MT4 and MT5 installers on their site; make sure you get the MT5 one.

---

## Step 1: Install MetaTrader 5 (skip if already installed)

1. Go to your broker's MT5 download page (e.g., Exness's MT5 download).
2. Download and run the installer.
3. Log in with your MT5 account (a demo account is fine for compiling and backtesting — you don't need a funded live account for this step).

## Step 2: Locate the correct folder for the file

1. Open MetaTrader 5.
2. Go to **File → Open Data Folder**. This opens a Windows Explorer window.
3. Navigate to **MQL5 → Experts**.
4. Copy `FatalibuildersTrader.mq5` into this `Experts` folder. (You can drop it directly in the folder, or in a subfolder like `Experts\FatalibuildersTrader\` if you want to keep it organized — either works.)

## Step 3: Open MetaEditor

You can get to MetaEditor two ways:
- From MT5: **Tools → MetaQuotes Language Editor**, or press **F4**.
- Or launch it directly: it's usually installed alongside MT5 as a separate application ("MetaEditor").

## Step 4: Open the file

1. In MetaEditor, go to **File → Open**.
2. Navigate to the `Experts` folder from Step 2 and select `FatalibuildersTrader.mq5`.
3. It should open in the code editor with syntax highlighting.

## Step 5: Compile

1. Press **F7**, or click the **Compile** button in the toolbar (looks like a play button / gear icon depending on version).
2. Watch the **Toolbox** panel at the bottom of the screen — it has tabs for **Errors**, **Warnings**, etc.

## Step 6: Read the results

- **If you see "0 error(s), 0 warning(s)"** (or just 0 errors, warnings are usually fine) — you're done. A new file `FatalibuildersTrader.ex5` now sits in the same `Experts` folder. That's the compiled version MT5 actually runs, and what eventually goes to MQL5 Market.
- **If you see errors** — each one lists a line number and a message. **Copy the full error text and send it to me** — paste it directly in chat. I'll fix the corresponding lines in the code and send you an updated `.mq5` to try again.

## Step 7: Load it onto a chart (optional, to confirm it actually runs)

1. Back in MT5, open the **Navigator** panel (Ctrl+N if it's hidden).
2. Expand **Expert Advisors** — you should see `FatalibuildersTrader` listed.
3. Open a chart for a **forex pair or metal (e.g. XAUUSD)**, set to **M1 or M5**, then drag the EA onto it. It's restricted to forex/metals — dragging it onto anything else (indices, crypto, stocks) will fail to initialize by design.
4. A settings dialog opens showing all the inputs (trading mode, stop-loss values, etc.) — for now just click **OK** to accept the defaults. If you're on a metals symbol, consider raising `InpMaxSpreadPoints` from the 30-point default first, since metals commonly run wider spreads than that.
5. Make sure **AutoTrading** is enabled (toolbar button, should be green) if you want it to actually place trades — but for a first check, it's fine to leave AutoTrading off and just confirm the EA attaches without errors (a smiley face icon appears in the top-right of the chart if it loaded successfully).

**Important:** don't run this on a live funded account yet. Use a demo account until it's been through real backtesting (Strategy Tester) — nothing in this EA has been validated against real market data yet, per everything documented in `Product_Development/MQL5_EA/README.md`.

## If something goes wrong

Send me any of these and I'll help directly:
- Compile error messages (exact text + line numbers)
- A screenshot of the Errors tab if that's easier
- What happens when you drag it onto a chart (does the smiley face appear? any error in the "Experts" log tab at the bottom of MT5 itself?)
