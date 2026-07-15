//+------------------------------------------------------------------+
//| FatalibuildersTraderScalper1.mq5                                    |
//| Draft v0.90 (Market tag 1.60) -- implements the risk-management,   |
//| dual-mode, daily-control, and entry-filter decisions from          |
//| Master-Context.md as of 2026-07-14, a volume-filter bug fix and    |
//| diagnostic logging (2026-07-14s), a v2 short-timeframe scalping     |
//| signal (Bollinger Bands + RSI + Stochastic mean-reversion)          |
//| restricted to forex/metals (2026-07-14u), a more aggressive default |
//| configuration (2026-07-14v), (2026-07-14w) a pre-trade margin       |
//| sufficiency check, (2026-07-14x) plain-English input names/groups   |
//| plus a manual SIGNALS_ONLY operation mode alongside AUTO_TRADE,      |
//| (2026-07-14y) the "Scalper 1" name plus a much more aggressive,      |
//| equity-percentage-based risk/reward specifically for Aggressive      |
//| Mode -- Safe Mode's fixed-dollar tiered risk is untouched -- and      |
//| (2026-07-14z) NARROWED to trade XAUUSD and GBPUSD only, ENFORCED to   |
//| the M1 (1-minute) chart, and a new session-open delay filter that     |
//| waits a configurable number of minutes after each of the 3 major      |
//| session opens (Asia/London/New York, server time) before allowing     |
//| a new trade. See the big comment above                                |
//| AggressiveMode_RiskPerTrade_PercentOfEquity below for the honest      |
//| math behind Aggressive Mode's risk before using it.                   |
//|                                                                    |
//| NOT PRODUCTION READY. See the "OPEN ITEMS / PLACEHOLDERS" block   |
//| below and Product_Development/MQL5_EA/README.md before trusting   |
//| any part of this for real trading. Compiles (per founder), still  |
//| not backtested.                                                    |
//+------------------------------------------------------------------+
#property copyright "FatalibuildersTrader Scalper 1"
#property version   "1.60"
#property strict

#include <Trade\Trade.mqh>
CTrade trade;

// MqlDateTime.day_of_week is 0=Sunday..6=Saturday; MQL5 has no named
// weekday constants, so these are defined explicitly to keep the
// weekend-protection logic below readable.
#define DOW_MONDAY 1
#define DOW_FRIDAY 5

//+------------------------------------------------------------------+
//| OPEN ITEMS / PLACEHOLDERS -- read before using this file          |
//|                                                                    |
//| 1. ENTRY SIGNAL LOGIC (GetEntrySignal, below) is now a REAL v2    |
//|    HYPOTHESIS, not a throwaway placeholder: a short-timeframe       |
//|    (M1-M5) scalping entry -- Bollinger Band mean-reversion,         |
//|    confirmed by RSI oversold/overbought and a Stochastic turn       |
//|    trigger. Grounded in published/widely-taught 1-minute scalping   |
//|    methodology (see decisions-learnings/2026-07-14u). Replaces the  |
//|    v1 multi-timeframe trend+pullback swing entry (2026-07-14q).     |
//|    IMPORTANT: "grounded in published methodology" is NOT the same   |
//|    as "proven to work" -- this specific parameter set has never     |
//|    been backtested. Treat it as a serious starting point            |
//|    to validate, not a finished strategy. Restricted to forex and    |
//|    metals only -- see IsAllowedInstrument().                        |
//|                                                                    |
//| 2. GetSignalConfidence() (Safe Mode's 65-75% win-probability       |
//|    filter) is a rule-based heuristic re-derived for v2 (RSI         |
//|    extremity + low ADX/ranging conditions, the opposite of v1's     |
//|    trend-strength version). It is EXPLICITLY NOT a calibrated       |
//|    probability -- it has never been checked against real win-rate   |
//|    outcomes. Needs real backtest validation before Safe Mode's       |
//|    filter threshold means anything statistically.                  |
//|                                                                    |
//| 3. Stop-loss DISTANCE (in points, not dollars) uses a basic ATR    |
//|    multiple as a reasonable default. The volatility/news-adaptive  |
//|    module's exact adaptation rules (Master-Context Open Questions) |
//|    are not fully designed -- IsHighImpactNewsWindow() below is a   |
//|    working first pass using MT5's native economic calendar, with   |
//|    a simple "widen stop, skip new entries" reaction, not the full  |
//|    parameter-adaptation system described in the docs.              |
//|                                                                    |
//| 4. Lot-size scaling on WINNING streaks (equity-based upsizing) is  |
//|    NOT implemented here -- gating rules for that were flagged as   |
//|    still open in NextSteps.md. This draft only implements the      |
//|    downside protections (tiered stop-loss, daily loss limit).      |
//|                                                                    |
//| 5. v0.20 adds named entry-condition filters (volume/volatility/     |
//|    range/data-feed/weekend), inspired by filter *names* seen on a  |
//|    third-party commercial EA's settings panel (screenshot, not     |
//|    source code). These are honest, well-established retail-EA      |
//|    concepts (see Product_Development/MQL5_EA/README.md for what    |
//|    each one actually does and the research behind it) -- they are  |
//|    NOT a reproduction of that EA's real logic, which was never     |
//|    visible, only its input names. "AI Filter" in that reference EA |
//|    is left unreplicated here: labeling a rule-based filter "AI"    |
//|    without a real trained model would repeat the exact kind of     |
//|    unsubstantiated claim already flagged as a marketing/legal risk |
//|    elsewhere in this project (see decisions-learnings 2026-07-14j).|
//|    That reference account's result (+533% equity in ~2 days on a   |
//|    3.1 fixed lot size) is NOT something this file targets or       |
//|    should be benchmarked against -- see README for why.            |
//|                                                                    |
//| 6. IsAllowedInstrument() (2026-07-14z) is a HEURISTIC, not a         |
//|    guaranteed-correct classification -- it checks the symbol name    |
//|    for an XAUUSD or GBPUSD prefix. Some brokers may name symbols      |
//|    unusually (unexpected prefixes rather than suffixes); verify it   |
//|    matches your broker's actual symbol names before relying on it.   |
//|    MaxAllowedSpread_Points (default 30) is tuned for major forex     |
//|    pairs and is almost certainly too tight for XAUUSD -- raise it    |
//|    manually, the code does not auto-detect a sane per-symbol         |
//|    default. The chart timeframe is now ENFORCED as M1 (2026-07-14z,  |
//|    OnInit refuses to run on anything else) -- this used to be only   |
//|    a recommendation.                                                 |
//+------------------------------------------------------------------+

//=== Trading mode / exit mode / operation mode ========================
enum ENUM_TRADING_MODE   { MODE_SAFE, MODE_AGGRESSIVE };
enum ENUM_EXIT_MODE      { EXIT_OUTRIGHT_CLOSE, EXIT_BREAKEVEN_AND_RUN };
// (2026-07-14x) NEW: lets someone keep full control instead of handing
// the bot the trade button. AUTO_TRADE = the bot finds a setup and
// places the trade itself, no action needed from you. SIGNALS_ONLY =
// the bot never places a trade -- it just tells you (on-screen arrow +
// popup + optional phone notification) "this looks like a BUY" or
// "this looks like a SELL," and you decide whether to actually trade
// it yourself, by hand, in MT5.
enum ENUM_OPERATION_MODE { AUTO_TRADE, SIGNALS_ONLY };

//+------------------------------------------------------------------+
//| PLAIN-ENGLISH GUIDE TO THE SETTINGS BELOW (2026-07-14x)            |
//| You do not need to understand trading jargon to use this. Every    |
//| setting below is named to say what it does. If you're not sure     |
//| what something does, leave it on the default value it ships with   |
//| -- the defaults are reasonable starting points, not requirements.  |
//| The settings are grouped into sections in MT5's input panel so you |
//| can find what you're looking for.                                  |
//+------------------------------------------------------------------+

input group "=== 1. HOW SHOULD THE BOT OPERATE? ==="
// This is the most important choice. Read the two options above under
// ENUM_OPERATION_MODE before picking.
input ENUM_OPERATION_MODE AutoTrade_Or_SignalsOnly = AUTO_TRADE;
// SAFE = the bot is picky, takes fewer trades, aims to be more careful.
// AGGRESSIVE = the bot takes more trades, accepts more risk per trade.
input ENUM_TRADING_MODE TradingStyle_SafeOrAggressive = MODE_AGGRESSIVE;
// What happens once a trade is in profit: OUTRIGHT_CLOSE banks the
// profit immediately and closes the trade. BREAKEVEN_AND_RUN moves the
// stop-loss to your entry price (so the trade can no longer lose money)
// and lets it keep running in case there's more profit to be had.
input ENUM_EXIT_MODE    HowProfitsAreLocked = EXIT_OUTRIGHT_CLOSE;

input group "=== 2. HOW MUCH CAN BE LOST ON ONE TRADE? ==="
// Accounts smaller than this dollar amount use the "small account" risk
// limit below; accounts at or above it use the "larger account" limit.
// (SAFE mode only -- Aggressive Mode uses its own percentage-based
// setting further down, not this dollar tier.)
input double AccountSizeThreshold_Dollars           = 50.0;   // 2026-07-14f
// SAFE mode: the most this bot will risk on a single trade if your
// account balance is BELOW the threshold above.
input double MaxLossPerTrade_SmallAccount_Dollars   = 1.0;    // 2026-07-14f
// SAFE mode: the most this bot will risk on a single trade if your
// account balance is AT OR ABOVE the threshold above.
input double MaxLossPerTrade_LargerAccount_Dollars  = 3.0;    // 2026-07-14f
//
// (2026-07-14y) VERY AGGRESSIVE SETTING -- READ THIS BEFORE CHANGING IT.
// AGGRESSIVE mode does NOT use the small/large dollar tiers above at
// all. Instead it risks a PERCENTAGE OF YOUR CURRENT ACCOUNT BALANCE on
// every single trade. This was requested explicitly as "very very
// aggressive," accepting real risk of losing most of the account in
// exchange for the chance to grow it much faster.
// HONEST MATH (computed via Monte Carlo simulation, not a guarantee --
// see Product_Development/simulations/aggressive_mode_ruin_probability_
// simulation.py and decisions-learnings/2026-07-14y): "ruin" here means
// $100 falling to $10 or below.
//   - At the HOPED-FOR 80% win rate, ruin probability is close to 0% at
//     this risk level (and every other risk level tested) -- a genuine
//     80% edge with a 1:1 payout is very safe no matter how hard it's
//     pushed. The danger below is NOT about this setting in isolation.
//   - If the strategy's REAL win rate turns out to be 50-55% (plausible
//     for a strategy that has never been backtested, i.e. the 80% is a
//     hope, not a measured result), simulated ruin probability at this
//     15%/15% setting ranges from roughly 2% (55% win rate, 50 trades)
//     up to roughly 32% (50% win rate, 100 trades) -- a wide and
//     genuinely risky band, not a precise number. It gets worse the more
//     trades are taken at a mediocre win rate, and much worse if the
//     real win rate is closer to a coin flip than to 80%.
// The risk is the GAP between "hoped for" and "actual, unproven" win
// rate -- not this number by itself. Lower this to reduce that risk; 0
// disables Aggressive Mode's percentage risk (falls back to the Safe
// Mode dollar tiers above).
input double AggressiveMode_RiskPerTrade_PercentOfEquity = 15.0; // 2026-07-14y

input group "=== 3. HOW MUCH PROFIT DOES EACH TRADE AIM FOR? ==="
input double SafeMode_ProfitTarget_SmallAccount_Dollars   = 1.50;  // 2026-07-14m
input double SafeMode_ProfitTarget_LargerAccount_Dollars  = 3.00;  // 2026-07-14m
// SAFE mode only takes a trade if the bot's own confidence score for
// that setup is at or above this percentage (0-100). Higher = pickier.
input double SafeMode_MinimumConfidence_Percent     = 65.0;   // 2026-07-14m (65-75% range; floor used here)
// (2026-07-14y) AGGRESSIVE mode's profit target, as a percentage of
// current account balance, matching AggressiveMode_RiskPerTrade above
// (1:1 risk:reward -- this exact 1:1 pairing is what the honest-math
// note above was simulated with). Replaces the old fixed $0.50 target,
// which was too small to matter once risk is a large percentage of
// equity instead of a few dollars.
input double AggressiveMode_RewardPerTrade_PercentOfEquity = 15.0; // 2026-07-14y
// AGGRESSIVE mode's confidence bar -- lower than Safe Mode's, on
// purpose, so it takes more trades. 50 means "just barely better than a
// coin flip." (2026-07-14v: previously Aggressive Mode had no
// confidence check at all and took every signal regardless of quality.)
input double AggressiveMode_MinimumConfidence_Percent = 50.0; // 2026-07-14v

input group "=== 4. DAILY LIMITS (WHEN THE BOT STOPS FOR THE DAY) ==="
// SAFE mode: if the account loses this percentage in a single day, the
// bot stops trading until the next day. This protects you from one bad
// day turning into a very bad day.
input double StopForDay_IfLossReaches_Percent                  = 3.0;    // 2026-07-14i
// If the account gains this percentage in a day while in Safe Mode, the
// bot stops trading for the rest of the day and locks in the gain.
input double StopForDay_SafeMode_IfProfitReaches_Percent       = 5.0;    // 2026-07-14l
// Same idea, but the target used when in Aggressive Mode.
input double StopForDay_AggressiveMode_IfProfitReaches_Percent = 20.0;   // 2026-07-14k
// (2026-07-14y) AGGRESSIVE mode's OWN daily loss limit -- deliberately
// much higher than the 3% Safe Mode limit above. A single Aggressive
// Mode trade already risks 15% of the account by design (see the note
// above); if this stayed capped at 3%, the daily-loss-budget logic
// would silently shrink every Aggressive trade down to near nothing
// after the first loss, quietly undoing the "very aggressive" setting.
// This is the real lever controlling how many losing Aggressive trades
// can happen in one day before the bot stops -- at 15% risk/trade and a
// 50% ceiling, that's roughly 3 full losses before the day halts.
input double StopForDay_AggressiveMode_IfLossReaches_Percent   = 50.0;   // 2026-07-14y

input group "=== 5. BASIC TRADE SETTINGS ==="
// The bot will never have more than this many trades open at the same
// time, regardless of how many good setups it sees.
input int    MaxTradesOpenAtOnce           = 2;      // 2026-07-14h
// The smallest trade size the bot will use (in "lots," MT5's unit for
// position size). 0.01 is the smallest size most brokers allow.
input double StartingTradeSize_Lots        = 0.01;   // 2026-07-14e
// Advanced: how many recent price bars the bot uses to judge current
// market volatility. Leave on default unless you know what this means.
input int    VolatilityMeasure_Period               = 14;     // advanced -- stop-distance basis
input double StopLossDistance_VolatilityMultiplier  = 1.0;    // advanced
// The bot avoids opening new trades in the minutes just before a
// major scheduled news release for the currency being traded.
input int    AvoidTradingBeforeNews_Minutes = 30;
// A unique ID number MT5 uses to tell this bot's trades apart from any
// other bot or your own manual trades on the same account. You don't
// need to change this unless you're running more than one copy.
input int    BotID_Number                  = 20260714;

input group "=== 6. STRATEGY SETTINGS (ADVANCED -- SAFE TO LEAVE ALONE) ==="
// (2026-07-14u) The bot looks for the price bouncing off a statistical
// extreme (a "Bollinger Band"), confirmed by two other indicators
// (RSI and Stochastic) agreeing the bounce is real. This is a
// widely-used, widely-taught short-term trading approach -- see
// decisions-learnings/2026-07-14u_scalping_signal_v2.md for the
// research behind it. Still unproven for THIS exact setup until
// backtested -- see the OPEN ITEMS notes at the top of this file.
input int    PriceRangeBands_Period       = 20;    // how many bars the price-extreme measurement looks back over
input double PriceRangeBands_Width        = 2.0;   // how far price has to stretch to count as "extreme"
input int    MomentumIndicator_Period     = 14;    // RSI lookback period
input double MomentumIndicator_BuyLevel   = 30.0;  // RSI level that signals "oversold" (potential buy)
input double MomentumIndicator_SellLevel  = 70.0;  // RSI level that signals "overbought" (potential sell)
input int    TurnConfirmation_Period      = 14;    // Stochastic indicator settings (research: 14,1,3)
input int    TurnConfirmation_Signal      = 1;
input int    TurnConfirmation_Smoothing   = 3;
input double TurnConfirmation_BuyLevel    = 20.0;  // Stochastic level confirming a buy turn
input double TurnConfirmation_SellLevel   = 80.0;  // Stochastic level confirming a sell turn

input group "=== 7. WHEN SHOULD THE BOT AVOID TRADING? ==="
// Skips trading when there isn't enough recent buying/selling activity
// -- quiet markets tend to have worse trade execution.
input bool   AvoidQuietMarkets_Enabled         = true;
input int    AvoidQuietMarkets_LookbackPeriod  = 20;

// Skips trading when the market is unusually calm (poor profit
// potential) OR unusually wild (often a news spike, risky to trade).
input bool   AvoidBadVolatility_Enabled  = true;
input double AvoidBadVolatility_MinLevel = 0.5;
input double AvoidBadVolatility_MaxLevel = 2.5;

// This bot's strategy works best when price is bouncing around in a
// range, not when it's strongly trending in one direction (a strong
// trend can blow straight through the "extreme" level the bot is
// watching for, without bouncing back). This setting skips trading when
// the market is trending too strongly.
// (2026-07-14v) Raised from 25 to 30 to let more setups qualify --
// trades more often, but more of those trades happen while a real
// trend is starting to build, which is a real tradeoff, not free.
input bool   AvoidStrongTrends_Enabled          = true;
input int    TrendStrength_Period               = 14;
input double AvoidStrongTrends_MaxTrendStrength = 30.0;  // higher = allows stronger trends through

// Refuses to trade if the buy/sell price gap (the "spread") is
// unusually wide, or if the price feed looks stale/frozen -- both are
// signs of a bad moment to trade, not a real opportunity.
// NOTE: metals (like gold) commonly have a much wider normal spread
// than forex pairs. If you're trading gold/silver and the bot seems to
// never trade, this setting is the first thing to check and raise.
input bool   AvoidBadPriceData_Enabled    = true;
input double MaxAllowedSpread_Points      = 30.0;
input int    MaxAllowedPriceDelay_Seconds = 60;

// (2026-07-14z) Many traders avoid the first stretch of a trading
// session right after it opens, because spreads often widen and price
// can whip around sharply before settling into a real trend/range. This
// makes the bot wait a set number of minutes after EACH of the 3 major
// session opens (Asia/Tokyo, London, New York) before it's allowed to
// open a NEW trade -- it keeps watching every 1-minute candle the whole
// time, it just won't act on a signal until the delay has passed.
input bool   AvoidSessionOpens_Enabled          = true;
// How many minutes to wait after a session opens before new trades are
// allowed again.
input int    AvoidSessionOpens_DelayMinutes     = 60;
// IMPORTANT: these 3 hours are in SERVER time -- the clock shown on
// your MT5 charts, which is set by your broker and is usually NOT the
// same as your local time or UTC. The defaults below assume server time
// is close to UTC (Asia/Tokyo opens ~00:00 UTC, London ~08:00 UTC, New
// York ~13:00 UTC), which is a common approximation but NOT universal --
// many brokers (Exness included, depending on time of year) run their
// server clock 2-3 hours ahead of UTC. CHECK YOUR BROKER'S ACTUAL
// SERVER TIME (visible on any MT5 chart) and adjust these 3 values to
// match, or the "wait after session open" window will fire at the wrong
// time.
input int    AsiaSession_OpenHour_ServerTime    = 0;
input int    LondonSession_OpenHour_ServerTime  = 8;
input int    NewYorkSession_OpenHour_ServerTime = 13;

input group "=== 8. WEEKEND SAFETY ==="
// Markets close for the weekend and can "gap" (jump) to a very
// different price when they reopen Monday. This closes open trades
// before that happens and pauses new trades around the close/reopen.
input bool   WeekendProtection_Enabled           = true;
input int    CloseAllTradesBeforeWeekend_Hour    = 20;  // server time, Friday
input int    StopNewTradesBeforeWeekend_Hour     = 16;  // server time, Friday
input int    WaitBeforeTradingMonday_UntilHour   = 2;   // server time, Monday

input group "=== 9. LOGGING ==="
// When on, the bot writes a note in MT5's "Experts" log tab explaining
// why it did or didn't trade on each new price bar -- useful for
// understanding what it's doing. Turn off once you're confident it's
// working correctly, to keep the log less cluttered.
input bool   ShowDetailedLog_Enabled = true;

//=== Global state ======================================================
double   g_dayStartEquity = 0;
datetime g_lastLogBarTime = 0;
datetime g_lastSignalAlertBarTime = 0;   // 2026-07-14x -- throttles SIGNALS_ONLY alerts to once per new bar
MqlDateTime g_dayKey;
int      g_handleBands, g_handleStoch, g_handleRsi, g_handleAtr, g_handleAdx;
bool     g_dailyHalted = false;

//+------------------------------------------------------------------+
//| Instrument restriction (2026-07-14z) -- NARROWED from "any forex   |
//| or metals symbol" (2026-07-14u) to EXACTLY GOLD (XAUUSD) and       |
//| GBPUSD, per explicit founder request. Uses a PREFIX match (not     |
//| exact-equals) so broker suffixes like "XAUUSDm" or "GBPUSD.a" still |
//| qualify, but nothing else does -- e.g. EURUSD, XAGUSD, GBPJPY all   |
//| correctly fail this check. This is a heuristic, not a perfect       |
//| classification across every broker's symbol-naming convention --    |
//| verify it matches your actual broker's symbol names.                |
//+------------------------------------------------------------------+
bool IsAllowedInstrument()
{
   string name = _Symbol;
   StringToUpper(name);
   bool isGold   = (StringFind(name, "XAUUSD") == 0);
   bool isGbpUsd = (StringFind(name, "GBPUSD") == 0);

   return (isGold || isGbpUsd);
}

//+------------------------------------------------------------------+
int OnInit()
{
   if(!IsAllowedInstrument())
   {
      PrintFormat("FatalibuildersTrader Scalper 1: %s is not XAUUSD or GBPUSD. This EA is restricted to those two symbols only (2026-07-14z) -- refusing to initialize.", _Symbol);
      return(INIT_FAILED);
   }

   // (2026-07-14z) Founder asked for 1-minute-candle analysis
   // specifically, not just "a short timeframe" -- enforced here rather
   // than left as a recommendation, since the strategy's entry logic
   // (GetEntrySignal, below) is only meaningful on the timeframe it was
   // designed and reasoned about.
   if(_Period != PERIOD_M1)
   {
      PrintFormat("FatalibuildersTrader Scalper 1: attached to a %s chart, but this build requires the M1 (1-minute) chart -- refusing to initialize. Change the chart timeframe to M1 and re-attach.", EnumToString(_Period));
      return(INIT_FAILED);
   }

   g_handleBands   = iBands(_Symbol, PERIOD_CURRENT, PriceRangeBands_Period, 0, PriceRangeBands_Width, PRICE_CLOSE);
   g_handleStoch   = iStochastic(_Symbol, PERIOD_CURRENT, TurnConfirmation_Period, TurnConfirmation_Signal, TurnConfirmation_Smoothing, MODE_SMA, STO_LOWHIGH);
   g_handleRsi     = iRSI(_Symbol, PERIOD_CURRENT, MomentumIndicator_Period, PRICE_CLOSE);
   g_handleAtr     = iATR(_Symbol, PERIOD_CURRENT, VolatilityMeasure_Period);
   g_handleAdx     = iADX(_Symbol, PERIOD_CURRENT, TrendStrength_Period);

   if(g_handleBands == INVALID_HANDLE || g_handleStoch == INVALID_HANDLE ||
      g_handleRsi == INVALID_HANDLE || g_handleAtr == INVALID_HANDLE ||
      g_handleAdx == INVALID_HANDLE)
   {
      Print("FatalibuildersTrader Scalper 1: failed to create indicator handles");
      return(INIT_FAILED);
   }

   trade.SetExpertMagicNumber(BotID_Number);
   ResetDailyTracking();
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   IndicatorRelease(g_handleBands);
   IndicatorRelease(g_handleStoch);
   IndicatorRelease(g_handleAdx);
   IndicatorRelease(g_handleRsi);
   IndicatorRelease(g_handleAtr);
}

//+------------------------------------------------------------------+
//| Daily tracking -- profit target / loss limit (2026-07-14h/i/k/l)  |
//+------------------------------------------------------------------+
void ResetDailyTracking()
{
   g_dayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   TimeToStruct(TimeCurrent(), g_dayKey);
   g_dailyHalted = false;
}

bool IsNewDay()
{
   MqlDateTime now;
   TimeToStruct(TimeCurrent(), now);
   return (now.day != g_dayKey.day || now.mon != g_dayKey.mon || now.year != g_dayKey.year);
}

// (2026-07-14y) Aggressive Mode has its own, much higher daily loss
// ceiling than Safe Mode -- see the note above
// StopForDay_AggressiveMode_IfLossReaches_Percent for why the two must
// not share one limit.
double GetDailyLossLimitPercent()
{
   return (TradingStyle_SafeOrAggressive == MODE_SAFE)
           ? StopForDay_IfLossReaches_Percent                    // 3%, 2026-07-14i
           : StopForDay_AggressiveMode_IfLossReaches_Percent;    // 50%, 2026-07-14y
}

// Returns true if trading should be halted for the rest of the day.
bool CheckDailyLimits()
{
   if(IsNewDay())
      ResetDailyTracking();

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double changePct = (equity - g_dayStartEquity) / g_dayStartEquity * 100.0;

   double lossLimitPct = GetDailyLossLimitPercent();
   double profitTargetPct = (TradingStyle_SafeOrAggressive == MODE_SAFE)
                              ? StopForDay_SafeMode_IfProfitReaches_Percent          // 5%, 2026-07-14l
                              : StopForDay_AggressiveMode_IfProfitReaches_Percent;   // 20%, 2026-07-14k

   if(changePct <= -lossLimitPct || changePct >= profitTargetPct)
   {
      if(!g_dailyHalted)
         PrintFormat("FatalibuildersTrader Scalper 1: daily limit reached (%.2f%%), halting until next day", changePct);
      g_dailyHalted = true;
   }
   return g_dailyHalted;
}

// Remaining daily loss budget in dollars, given today's equity so far.
// Resolves the tier-boundary interaction flagged 2026-07-14i: a single
// trade's risk must never exceed what's left of the day's loss budget.
// (2026-07-14y) Uses the mode-specific daily loss limit, not always
// Safe Mode's 3% -- see GetDailyLossLimitPercent().
double RemainingDailyLossBudget()
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double lossSoFar = MathMax(0.0, g_dayStartEquity - equity);
   double totalBudget = g_dayStartEquity * (GetDailyLossLimitPercent() / 100.0);
   return MathMax(0.0, totalBudget - lossSoFar);
}

//+------------------------------------------------------------------+
//| Risk parameters by equity tier + mode (2026-07-14f, 2026-07-14m). |
//| (2026-07-14y) Aggressive Mode now risks/targets a PERCENTAGE OF   |
//| CURRENT EQUITY per trade instead of the small fixed-dollar amounts |
//| below -- Safe Mode's fixed-dollar tiered logic is unchanged.       |
//+------------------------------------------------------------------+
double GetStopLossDollars()
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double tierRisk;

   if(TradingStyle_SafeOrAggressive == MODE_AGGRESSIVE && AggressiveMode_RiskPerTrade_PercentOfEquity > 0)
      tierRisk = equity * (AggressiveMode_RiskPerTrade_PercentOfEquity / 100.0);   // 2026-07-14y, default 15%
   else
      tierRisk = (equity < AccountSizeThreshold_Dollars) ? MaxLossPerTrade_SmallAccount_Dollars : MaxLossPerTrade_LargerAccount_Dollars;

   // Tier-boundary fix: never risk more on one trade than remains of the daily loss budget.
   double remaining = RemainingDailyLossBudget();
   return MathMin(tierRisk, remaining);
}

double GetProfitTargetDollars()
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);

   if(TradingStyle_SafeOrAggressive == MODE_AGGRESSIVE)
      return equity * (AggressiveMode_RewardPerTrade_PercentOfEquity / 100.0); // 2026-07-14y, default 15% (1:1 with risk)

   return (equity < AccountSizeThreshold_Dollars)
           ? SafeMode_ProfitTarget_SmallAccount_Dollars                        // $1.50, 2026-07-14m
           : SafeMode_ProfitTarget_LargerAccount_Dollars;                      // $3.00, 2026-07-14m
}

//+------------------------------------------------------------------+
//| Lot sizing -- dollar risk -> lot size given stop distance          |
//| (2026-07-14e: dynamic, risk-based; derived from stop-loss tier    |
//| and current stop distance, not a fixed manual table)              |
//+------------------------------------------------------------------+
double CalculateLotSize(double stopDistancePoints, double riskDollars)
{
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double point     = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

   if(tickSize <= 0 || stopDistancePoints <= 0)
      return StartingTradeSize_Lots;

   double moneyPerPointPerLot = (tickValue / tickSize) * point;
   double rawLots = riskDollars / (stopDistancePoints * moneyPerPointPerLot);

   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   rawLots = MathFloor(rawLots / lotStep) * lotStep;
   rawLots = MathMax(minLot, MathMin(maxLot, rawLots));
   if(rawLots < minLot) rawLots = minLot;
   return rawLots;
}

//+------------------------------------------------------------------+
//| Stop distance -- PLACEHOLDER (ATR-based). Real volatility-adaptive |
//| design from Master-Context Open Questions is not yet specified.    |
//+------------------------------------------------------------------+
double GetStopDistancePoints()
{
   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(g_handleAtr, 0, 0, 1, atr) <= 0)
      return 100 * SymbolInfoDouble(_Symbol, SYMBOL_POINT); // fallback

   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   return (atr[0] * StopLossDistance_VolatilityMultiplier) / point;
}

//+------------------------------------------------------------------+
//| News/volatility awareness -- FIRST PASS, not the full adaptive     |
//| module described in Master-Context.md. Uses MT5's native calendar  |
//| (2026-07-14d chose "no external bridge"; this picks the built-in   |
//| calendar over a third-party API as the simpler default -- still    |
//| flagged as an open confirmation item in NextSteps.md).             |
//+------------------------------------------------------------------+
bool IsHighImpactNewsWindow()
{
   MqlCalendarValue values[];
   datetime from = TimeCurrent();
   datetime to   = TimeCurrent() + AvoidTradingBeforeNews_Minutes * 60;

   string baseCurrency  = SymbolInfoString(_Symbol, SYMBOL_CURRENCY_BASE);
   string quoteCurrency = SymbolInfoString(_Symbol, SYMBOL_CURRENCY_PROFIT);

   if(!CalendarValueHistory(values, from, to, NULL, NULL))
      return false; // fail open -- do not block trading on a calendar-lookup failure

   for(int i = 0; i < ArraySize(values); i++)
   {
      MqlCalendarEvent event;
      if(!CalendarEventById(values[i].event_id, event))
         continue;

      MqlCalendarCountry country;
      if(!CalendarCountryById(event.country_id, country))
         continue;

      bool relevant = (country.currency == baseCurrency || country.currency == quoteCurrency);
      if(relevant && event.importance == CALENDAR_IMPORTANCE_HIGH)
         return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Entry-condition filters (v0.20) -- see header note. Each is an     |
//| honest, well-established retail-EA concept, not a reproduction of  |
//| any specific third-party product's internal logic.                 |
//+------------------------------------------------------------------+

// "Volume Filter": only trade when the last COMPLETED bar's tick volume
// is at or above its recent average -- avoids illiquid periods (poor
// execution, wider spreads).
// BUG FIX (2026-07-14s): originally compared the still-forming bar's
// volume (index 0) to the average of completed bars -- a forming bar
// has accumulated only a few ticks for most of its life, so this almost
// always evaluated false except right before the bar closed, silently
// blocking nearly every trade. Now compares the last completed bar
// (index 1) against the average of the completed bars before it.
bool PassesVolumeFilter()
{
   if(!AvoidQuietMarkets_Enabled) return true;

   long vol[];
   ArraySetAsSeries(vol, true);
   if(CopyTickVolume(_Symbol, PERIOD_CURRENT, 0, AvoidQuietMarkets_LookbackPeriod + 2, vol) <= 0)
      return true; // fail open -- don't block trading on a data hiccup

   long sum = 0;
   for(int i = 2; i <= AvoidQuietMarkets_LookbackPeriod + 1; i++)
      sum += vol[i];
   double avgVol = (double)sum / AvoidQuietMarkets_LookbackPeriod;

   return (double)vol[1] >= avgVol;
}

// "Volatility Filter": reject both dead markets (ATR far below its own
// recent average -- poor risk:reward, spread dominates) and abnormal
// spikes (ATR far above average -- often a news/gap event, not a clean
// trend the placeholder signal is designed for).
bool PassesVolatilityFilter()
{
   if(!AvoidBadVolatility_Enabled) return true;

   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(g_handleAtr, 0, 0, 20, atr) <= 0)
      return true;

   double sum = 0;
   for(int i = 1; i < 20; i++)
      sum += atr[i];
   double avg = sum / 19.0;
   if(avg <= 0) return true;

   double ratio = atr[0] / avg;
   return (ratio >= AvoidBadVolatility_MinLevel && ratio <= AvoidBadVolatility_MaxLevel);
}

// "Range Filter" -- FLIPPED for v2 (2026-07-14u). The v1 signal was
// trend-following and wanted HIGH ADX; this v2 signal is MEAN-REVERSION
// and wants the OPPOSITE -- strong trends are dangerous for mean
// reversion (price can "walk the band" through a Bollinger extreme
// without reverting), so this now REJECTS entries when ADX is too high.
bool PassesRangeFilter()
{
   if(!AvoidStrongTrends_Enabled) return true;

   double adx[];
   ArraySetAsSeries(adx, true);
   if(CopyBuffer(g_handleAdx, MAIN_LINE, 0, 1, adx) <= 0)
      return true;

   return adx[0] <= AvoidStrongTrends_MaxTrendStrength;
}

// "Information Feed Filter": interpreted as a data-sanity check --
// reject trading on stale quotes or an abnormally wide spread, both
// signs of a bad/thin data feed moment rather than a real setup.
bool PassesDataFeedSanityCheck()
{
   if(!AvoidBadPriceData_Enabled) return true;

   double spread = (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID))
                     / SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(spread > MaxAllowedSpread_Points)
      return false;

   datetime lastTick = (datetime)SymbolInfoInteger(_Symbol, SYMBOL_TIME);
   if(TimeCurrent() - lastTick > MaxAllowedPriceDelay_Seconds)
      return false;

   return true;
}

// Margin sufficiency check (2026-07-14w) -- small accounts may not have
// enough free margin to open even the minimum lot size, especially on
// metals (which require more margin per lot than most forex pairs).
// This checks BEFORE sending an order instead of letting the broker
// silently reject it, and logs a clear reason. Margin required depends
// on the account's leverage setting, which this code has no control
// over -- it can only check what MT5 reports, not guarantee a specific
// balance is "enough" in the abstract.
bool HasSufficientMargin(ENUM_ORDER_TYPE orderType, double lots, double price)
{
   double marginRequired = 0;
   if(!OrderCalcMargin(orderType, _Symbol, lots, price, marginRequired))
      return true; // fail open -- can't calculate, don't block on that alone

   double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   return freeMargin >= marginRequired;
}

// "Session-Open Delay" (2026-07-14z): blocks new trades for a set number
// of minutes after each of the 3 major session opens (Asia/Tokyo,
// London, New York), server time -- see the input-group comment above
// AvoidSessionOpens_Enabled for why, and the server-time caveat. Works
// in total minutes-since-midnight so a window that crosses midnight
// (e.g. a session opening at 23:xx server time) is still handled
// correctly.
bool IsWithinSessionOpenDelay()
{
   if(!AvoidSessionOpens_Enabled) return false;

   MqlDateTime t;
   TimeToStruct(TimeCurrent(), t);
   int nowMinutes = t.hour * 60 + t.min;

   int sessionOpenMinutes[3];
   sessionOpenMinutes[0] = AsiaSession_OpenHour_ServerTime    * 60;
   sessionOpenMinutes[1] = LondonSession_OpenHour_ServerTime  * 60;
   sessionOpenMinutes[2] = NewYorkSession_OpenHour_ServerTime * 60;

   for(int i = 0; i < 3; i++)
   {
      int windowStart = sessionOpenMinutes[i];
      int windowEnd   = sessionOpenMinutes[i] + AvoidSessionOpens_DelayMinutes;

      if(windowEnd <= 1440)
      {
         if(nowMinutes >= windowStart && nowMinutes < windowEnd)
            return true;
      }
      else // window wraps past midnight
      {
         if(nowMinutes >= windowStart || nowMinutes < (windowEnd - 1440))
            return true;
      }
   }
   return false;
}

// "Weekend Protection": avoid opening new risk into a weekend gap, and
// block new entries approaching Friday close / just after Monday open.
bool IsWeekendEntryBlocked()
{
   if(!WeekendProtection_Enabled) return false;

   MqlDateTime t;
   TimeToStruct(TimeCurrent(), t);

   if(t.day_of_week == DOW_FRIDAY && t.hour >= StopNewTradesBeforeWeekend_Hour) return true;
   if(t.day_of_week == DOW_MONDAY && t.hour < WaitBeforeTradingMonday_UntilHour)       return true;
   return false;
}

// Force-close all FatalibuildersTrader Scalper 1 positions ahead of the weekend close.
void ApplyWeekendCloseAll()
{
   if(!WeekendProtection_Enabled) return;

   MqlDateTime t;
   TimeToStruct(TimeCurrent(), t);
   if(t.day_of_week != DOW_FRIDAY || t.hour < CloseAllTradesBeforeWeekend_Hour)
      return;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket) && PositionGetInteger(POSITION_MAGIC) == BotID_Number)
         trade.PositionClose(ticket);
   }
}

//+------------------------------------------------------------------+
//| SIGNAL v2 -- Bollinger Bands + RSI + Stochastic scalping.          |
//| (2026-07-14u, replaces the v1 multi-timeframe trend+pullback swing |
//| entry.) This is a widely-documented, widely-taught 1-minute        |
//| scalping methodology, not something invented for this project --   |
//| see decisions-learnings/2026-07-14u_scalping_signal_v2.md for       |
//| sourcing. Still a HYPOTHESIS: real research backs the general       |
//| approach, not a backtest of THIS specific parameter set on real     |
//| data. Designed for short timeframes (M1-M5) on forex/metals only.  |
//|                                                                    |
//| Logic:                                                             |
//|  1. Price touched/pierced a Bollinger Band on the last completed   |
//|     bar (default 20-period, 2.0 std-dev) -- a potential mean-      |
//|     reversion extreme.                                             |
//|  2. RSI confirms oversold (<=30) / overbought (>=70) on that same   |
//|     bar -- momentum agrees the move is extended.                    |
//|  3. Stochastic TURN-confirmation trigger: was oversold/overbought   |
//|     and is now turning back -- not just a static extreme reading,   |
//|     which avoids entering while price is still falling/rising      |
//|     ("catching a falling knife").                                  |
//| Paired with the flipped Range Filter (v2 wants LOW ADX / ranging    |
//| conditions, the opposite of v1's trend-following pairing) and the   |
//| existing volume/volatility/news/weekend filters.                    |
//+------------------------------------------------------------------+
enum ENUM_SIGNAL { SIGNAL_NONE, SIGNAL_BUY, SIGNAL_SELL };

ENUM_SIGNAL GetEntrySignal()
{
   double upper[], lower[];
   ArraySetAsSeries(upper, true);
   ArraySetAsSeries(lower, true);
   if(CopyBuffer(g_handleBands, UPPER_BAND, 0, 2, upper) <= 0) return SIGNAL_NONE;
   if(CopyBuffer(g_handleBands, LOWER_BAND, 0, 2, lower) <= 0) return SIGNAL_NONE;

   double close[];
   ArraySetAsSeries(close, true);
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 2, close) <= 0) return SIGNAL_NONE;

   double rsi[];
   ArraySetAsSeries(rsi, true);
   if(CopyBuffer(g_handleRsi, 0, 0, 2, rsi) <= 0) return SIGNAL_NONE;

   double stochMain[];
   ArraySetAsSeries(stochMain, true);
   if(CopyBuffer(g_handleStoch, MAIN_LINE, 0, 2, stochMain) <= 0) return SIGNAL_NONE;

   // 1. Price touched/pierced the band on the last completed bar
   bool touchedLower = (close[1] <= lower[1]);
   bool touchedUpper = (close[1] >= upper[1]);

   // 2. RSI confirms oversold/overbought at that same bar
   bool rsiOversold   = (rsi[1] <= MomentumIndicator_BuyLevel);
   bool rsiOverbought = (rsi[1] >= MomentumIndicator_SellLevel);

   // 3. Stochastic turn-confirmation: was in extreme territory, now
   //    turning back -- the actual entry trigger, not a static state
   bool stochTurningUp   = (stochMain[1] <= TurnConfirmation_BuyLevel   && stochMain[0] > stochMain[1]);
   bool stochTurningDown = (stochMain[1] >= TurnConfirmation_SellLevel && stochMain[0] < stochMain[1]);

   if(touchedLower && rsiOversold   && stochTurningUp)   return SIGNAL_BUY;
   if(touchedUpper && rsiOverbought && stochTurningDown) return SIGNAL_SELL;
   return SIGNAL_NONE;
}

//+------------------------------------------------------------------+
//| Confidence score -- Safe Mode's 65-75% win-probability filter      |
//| (2026-07-14m). Re-derived (2026-07-14u) for the mean-reversion v2   |
//| signal: rewards a DEEPER RSI extreme (stronger reversion pressure)  |
//| and a LOWER ADX (more contained/ranging, safer for mean reversion   |
//| -- the opposite of the v1 trend-following version, which rewarded   |
//| high ADX). This is EXPLICITLY NOT a calibrated probability -- it    |
//| has not been checked against real win-rate outcomes. It's an        |
//| honest, explainable scoring rule, not the reference EA's "AI        |
//| Filter" -- deliberately not labeled "AI" since no model has been    |
//| trained or validated (see header note). Must be validated against   |
//| real backtest win rates before Safe Mode's filter threshold means   |
//| anything statistically.                                            |
//+------------------------------------------------------------------+
double GetSignalConfidence(ENUM_SIGNAL signal)
{
   double rsi[];
   ArraySetAsSeries(rsi, true);
   double rsiScore = 50.0;
   if(CopyBuffer(g_handleRsi, 0, 0, 1, rsi) > 0)
   {
      double extremity = (signal == SIGNAL_BUY) ? (MomentumIndicator_BuyLevel - rsi[0]) : (rsi[0] - MomentumIndicator_SellLevel);
      rsiScore = MathMax(0.0, MathMin(100.0, 50.0 + extremity * 2.0));
   }

   double adx[];
   ArraySetAsSeries(adx, true);
   double adxScore = 50.0; // neutral default if data unavailable
   if(CopyBuffer(g_handleAdx, MAIN_LINE, 0, 1, adx) > 0)
      adxScore = MathMax(0.0, 100.0 - adx[0] * 2.0); // LOW ADX -> higher score for mean reversion

   return (rsiScore + adxScore) / 2.0;
}

//+------------------------------------------------------------------+
//| Position management                                                |
//+------------------------------------------------------------------+
int CountOpenPositions()
{
   int count = 0;
   for(int i = 0; i < PositionsTotal(); i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket) && PositionGetInteger(POSITION_MAGIC) == BotID_Number)
         count++;
   }
   return count;
}

// EXIT_BREAKEVEN_AND_RUN: once floating profit reaches the target, move
// SL to entry (lock breakeven) instead of closing outright, and let the
// position run without a hard TP (2026-07-14, dual-mode exit decision).
void ManageOpenPositions()
{
   if(HowProfitsAreLocked != EXIT_BREAKEVEN_AND_RUN)
      return;

   for(int i = 0; i < PositionsTotal(); i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket) || PositionGetInteger(POSITION_MAGIC) != BotID_Number)
         continue;

      double profit = PositionGetDouble(POSITION_PROFIT);
      double target = GetProfitTargetDollars();
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double currentSl = PositionGetDouble(POSITION_SL);

      bool alreadyBreakeven = (MathAbs(currentSl - openPrice) < SymbolInfoDouble(_Symbol, SYMBOL_POINT));
      if(profit >= target && !alreadyBreakeven)
      {
         trade.PositionModify(ticket, openPrice, PositionGetDouble(POSITION_TP));
         PrintFormat("FatalibuildersTrader Scalper 1: moved position #%I64u to breakeven at $%.2f profit", ticket, profit);
      }
   }
}

//+------------------------------------------------------------------+
//| Diagnostic logging (2026-07-14s) -- prints once per new bar, not   |
//| every tick, so the log stays readable instead of flooding.         |
//+------------------------------------------------------------------+
void LogBlockReason(string reason)
{
   if(!ShowDetailedLog_Enabled) return;

   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(barTime == g_lastLogBarTime) return; // already logged this bar

   g_lastLogBarTime = barTime;
   PrintFormat("FatalibuildersTrader Scalper 1 [%s]: no trade -- %s", TimeToString(TimeCurrent(), TIME_SECONDS), reason);
}

//+------------------------------------------------------------------+
//| Manual mode (2026-07-14x) -- SIGNALS_ONLY never calls trade.Buy()/ |
//| trade.Sell(). This is the only place a suggestion reaches the      |
//| user: an on-chart popup (Alert), an on-chart text note (Comment),   |
//| and a phone push notification (SendNotification, if the user has   |
//| set up a MetaQuotes ID under MT5 Options -> Notifications -- if     |
//| not configured, SendNotification simply does nothing, it does not   |
//| error). Throttled to once per new bar so it doesn't repeat every    |
//| tick while conditions remain true.                                  |
//+------------------------------------------------------------------+
void SendSignalAlert(ENUM_SIGNAL signal, double suggestedLots, double suggestedSl, double suggestedTp)
{
   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(barTime == g_lastSignalAlertBarTime) return;
   g_lastSignalAlertBarTime = barTime;

   string action = (signal == SIGNAL_BUY) ? "BUY" : "SELL";
   string msg = StringFormat(
      "FatalibuildersTrader Scalper 1 SIGNAL: %s %s -- suggested size %.2f lots, stop-loss %.5f, take-profit %.5f. Manual mode: no trade was placed. Decide and place it yourself in MT5 if you want it.",
      action, _Symbol, suggestedLots, suggestedSl, suggestedTp);

   Alert(msg);
   Comment(msg);
   SendNotification(msg);
   PrintFormat("FatalibuildersTrader Scalper 1: %s", msg);
}

//+------------------------------------------------------------------+
void OnTick()
{
   ManageOpenPositions();
   ApplyWeekendCloseAll();

   if(CheckDailyLimits())
   {
      LogBlockReason("daily profit target or loss limit already reached today");
      return;
   }

   if(CountOpenPositions() >= MaxTradesOpenAtOnce)
   {
      LogBlockReason(StringFormat("max concurrent trades reached (%d)", MaxTradesOpenAtOnce));
      return; // 2026-07-14h: max 2 concurrent trades
   }

   if(IsWeekendEntryBlocked())
   {
      LogBlockReason("weekend protection window (near Friday close / Monday open)");
      return;
   }

   if(IsWithinSessionOpenDelay())
   {
      LogBlockReason(StringFormat("within %d minutes of a session open (Asia/London/New York server time) -- waiting for the market to settle", AvoidSessionOpens_DelayMinutes));
      return;
   }

   if(!PassesDataFeedSanityCheck())
   {
      double spreadNow = (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID))
                          / SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      LogBlockReason(StringFormat("data feed check failed (spread=%.1f pts, max=%.1f, or stale quote)",
                     spreadNow, MaxAllowedSpread_Points));
      return;
   }

   if(IsHighImpactNewsWindow())
   {
      LogBlockReason("high-impact news window active");
      return;
   }

   if(!PassesVolumeFilter())
   {
      LogBlockReason("volume filter -- last completed bar's volume below its recent average");
      return;
   }
   if(!PassesVolatilityFilter())
   {
      LogBlockReason("volatility filter -- ATR ratio outside acceptable band (too dead or too spiky)");
      return;
   }
   if(!PassesRangeFilter())
   {
      LogBlockReason(StringFormat("range filter -- ADX too high for mean reversion (max=%.1f)", AvoidStrongTrends_MaxTrendStrength));
      return;
   }

   ENUM_SIGNAL signal = GetEntrySignal();
   if(signal == SIGNAL_NONE)
   {
      LogBlockReason("no entry signal -- Bollinger/RSI/Stochastic conditions not aligned this bar");
      return;
   }

   // (2026-07-14v) Both modes now gate on confidence, not just Safe Mode
   // -- previously Aggressive Mode took every raw signal with no filter
   // at all. Founder asked it to take any opportunity rated above 50%
   // (barely better than a coin flip) rather than literally everything,
   // so it's "as aggressive as possible" while still applying a floor.
   {
      double confidence = GetSignalConfidence(signal);
      double requiredConfidence = (TradingStyle_SafeOrAggressive == MODE_SAFE)
                                    ? SafeMode_MinimumConfidence_Percent        // 65-75%, 2026-07-14m
                                    : AggressiveMode_MinimumConfidence_Percent; // 50%, 2026-07-14v
      if(confidence < requiredConfidence)
      {
         LogBlockReason(StringFormat("confidence too low for %s (%.1f < %.1f required)",
                        (TradingStyle_SafeOrAggressive == MODE_SAFE ? "Safe Mode" : "Aggressive Mode"),
                        confidence, requiredConfidence));
         return;
      }
   }

   double stopDistancePoints = GetStopDistancePoints();
   double riskDollars = GetStopLossDollars();
   double targetDollars = GetProfitTargetDollars();

   if(riskDollars <= 0)
   {
      LogBlockReason("daily loss budget fully consumed -- cannot size a new trade");
      return; // daily loss budget fully consumed
   }

   double lots = CalculateLotSize(stopDistancePoints, riskDollars);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double moneyPerPointPerLot = (tickValue / tickSize) * point;
   double targetDistancePoints = (moneyPerPointPerLot > 0) ? targetDollars / (lots * moneyPerPointPerLot) : 0;

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   bool useHardTp = (HowProfitsAreLocked == EXIT_OUTRIGHT_CLOSE);
   ENUM_ORDER_TYPE orderType = (signal == SIGNAL_BUY) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double checkPrice = (signal == SIGNAL_BUY) ? ask : bid;

   if(!HasSufficientMargin(orderType, lots, checkPrice))
   {
      LogBlockReason(StringFormat("insufficient free margin for %.2f lots on %s -- account may be too small for this symbol/leverage",
                     lots, _Symbol));
      return;
   }

   // (2026-07-14x) MANUAL MODE: SIGNALS_ONLY never places a trade -- it
   // computes the exact same suggested lot size/stop-loss/take-profit as
   // AUTO_TRADE would have used, but only alerts the user instead of
   // calling trade.Buy()/trade.Sell().
   if(AutoTrade_Or_SignalsOnly == SIGNALS_ONLY)
   {
      double sl = (signal == SIGNAL_BUY) ? ask - stopDistancePoints * point : bid + stopDistancePoints * point;
      double tp = 0;
      if(useHardTp)
         tp = (signal == SIGNAL_BUY) ? ask + targetDistancePoints * point : bid - targetDistancePoints * point;
      SendSignalAlert(signal, lots, sl, tp);
      return;
   }

   if(signal == SIGNAL_BUY)
   {
      double sl = ask - stopDistancePoints * point;
      double tp = useHardTp ? ask + targetDistancePoints * point : 0;
      if(trade.Buy(lots, _Symbol, ask, sl, tp, "FatalibuildersTrader Scalper 1"))
         PrintFormat("FatalibuildersTrader Scalper 1: BUY placed, lots=%.2f sl=%.5f tp=%.5f", lots, sl, tp);
      else
         PrintFormat("FatalibuildersTrader Scalper 1: BUY failed, retcode=%d (%s)", trade.ResultRetcode(), trade.ResultRetcodeDescription());
   }
   else if(signal == SIGNAL_SELL)
   {
      double sl = bid + stopDistancePoints * point;
      double tp = useHardTp ? bid - targetDistancePoints * point : 0;
      if(trade.Sell(lots, _Symbol, bid, sl, tp, "FatalibuildersTrader Scalper 1"))
         PrintFormat("FatalibuildersTrader Scalper 1: SELL placed, lots=%.2f sl=%.5f tp=%.5f", lots, sl, tp);
      else
         PrintFormat("FatalibuildersTrader Scalper 1: SELL failed, retcode=%d (%s)", trade.ResultRetcode(), trade.ResultRetcodeDescription());
   }
}
