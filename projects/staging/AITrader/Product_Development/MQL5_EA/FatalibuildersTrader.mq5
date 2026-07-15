//+------------------------------------------------------------------+
//| FatalibuildersTrader.mq5                                          |
//| Draft v0.50 (Market tag 1.20) -- implements the risk-management,   |
//| dual-mode, daily-control, and entry-filter decisions from          |
//| Master-Context.md as of 2026-07-14, a volume-filter bug fix and    |
//| diagnostic logging (2026-07-14s), a v2 short-timeframe scalping     |
//| signal (Bollinger Bands + RSI + Stochastic mean-reversion)          |
//| restricted to forex/metals (2026-07-14u), and (2026-07-14v) a more  |
//| aggressive default configuration: Aggressive Mode now takes any     |
//| signal the confidence heuristic rates above 50% (previously no      |
//| filter at all), the Range Filter's ADX ceiling was raised to admit  |
//| more setups, and the default trading mode is now Aggressive.        |
//|                                                                    |
//| NOT PRODUCTION READY. See the "OPEN ITEMS / PLACEHOLDERS" block   |
//| below and Product_Development/MQL5_EA/README.md before trusting   |
//| any part of this for real trading. Compiles (per founder), still  |
//| not backtested.                                                    |
//+------------------------------------------------------------------+
#property copyright "FatalibuildersTrader"
#property version   "1.20"
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
//| 6. IsAllowedInstrument() (2026-07-14u) is a HEURISTIC, not a        |
//|    guaranteed-correct classification -- it checks MT5's forex      |
//|    calc-mode flag plus XAU/XAG/XPT/XPD in the symbol name. Some     |
//|    brokers may name/classify symbols unusually; verify it behaves   |
//|    correctly on your broker's actual symbol names before relying   |
//|    on it. InpMaxSpreadPoints (default 30) is tuned for major forex  |
//|    pairs and is almost certainly too tight for metals -- raise it   |
//|    manually when trading XAUUSD/XAGUSD, the code does not auto-      |
//|    detect a sane per-symbol default. The chart timeframe (M1-M5     |
//|    recommended for scalping) is NOT enforced by the code -- it will |
//|    run on any timeframe you attach it to, since PERIOD_CURRENT      |
//|    simply follows the chart.                                       |
//+------------------------------------------------------------------+

//=== Trading mode / exit mode ========================================
enum ENUM_TRADING_MODE  { MODE_SAFE, MODE_AGGRESSIVE };
enum ENUM_EXIT_MODE     { EXIT_OUTRIGHT_CLOSE, EXIT_BREAKEVEN_AND_RUN };

//=== Inputs -- values below match Master-Context.md decisions =======
// Default mode changed to MODE_AGGRESSIVE (2026-07-14v) per founder
// request to make the EA more aggressive out of the box. Still
// user-configurable in the input panel.
input ENUM_TRADING_MODE InpTradingMode              = MODE_AGGRESSIVE;
input ENUM_EXIT_MODE    InpExitMode                 = EXIT_OUTRIGHT_CLOSE;

input double InpEquityTierBreakpoint                = 50.0;   // 2026-07-14f
input double InpStopLossDollarsLowTier              = 1.0;    // 2026-07-14f
input double InpStopLossDollarsHighTier             = 3.0;    // 2026-07-14f

input double InpSafeModeTargetDollarsLowTier        = 1.50;   // 2026-07-14m
input double InpSafeModeTargetDollarsHighTier       = 3.00;   // 2026-07-14m
input double InpSafeModeMinWinProbabilityPct        = 65.0;   // 2026-07-14m (65-75% range; floor used here)
input double InpAggressiveModeTargetDollars         = 0.50;   // 2026-07-14h
// (2026-07-14v) Aggressive Mode previously had NO confidence filter at
// all -- took every raw signal regardless of estimated quality. Founder
// asked for it to take any opportunity the confidence heuristic rates
// above 50% (barely better than a coin flip), not literally everything.
input double InpAggressiveModeMinWinProbabilityPct  = 50.0;   // 2026-07-14v

input double InpDailyLossLimitPct                   = 3.0;    // 2026-07-14i
input double InpDailyProfitTargetSafePct            = 5.0;    // 2026-07-14l
input double InpDailyProfitTargetAggressivePct      = 20.0;   // 2026-07-14k

input int    InpMaxConcurrentTrades                 = 2;      // 2026-07-14h
input double InpStartingLot                         = 0.01;   // 2026-07-14e
input int    InpAtrPeriod                           = 14;     // placeholder stop-distance basis
input double InpAtrStopMultiple                     = 1.0;    // placeholder
input int    InpNewsLookaheadMinutes                = 30;     // placeholder news window
input int    InpMagicNumber                         = 20260714;

//=== Signal v2 -- Bollinger Bands + RSI + Stochastic scalping =========
// (2026-07-14u) Replaces the v1 multi-timeframe trend+pullback swing
// entry. Founder asked for a genuine short-timeframe (M1-M5) scalper
// restricted to forex and metals -- this is a widely-documented,
// widely-taught 1-minute scalping methodology: mean-reversion off
// Bollinger Band extremes, confirmed by RSI oversold/overbought, with a
// Stochastic turn-confirmation trigger (not just a static extreme
// reading) to avoid catching a falling knife mid-move. See
// decisions-learnings/2026-07-14u_scalping_signal_v2.md for sourcing.
// Still a HYPOTHESIS -- never backtested on real data.
input int    InpBollingerPeriod      = 20;    // Bollinger Bands period
input double InpBollingerDeviation   = 2.0;   // Bollinger Bands std-dev multiple
input int    InpRsiPeriod            = 14;    // RSI period
input double InpRsiOversold          = 30.0;  // RSI oversold threshold (buy side)
input double InpRsiOverbought        = 70.0;  // RSI overbought threshold (sell side)
input int    InpStochKPeriod         = 14;    // Stochastic %K period (research: 14,1,3)
input int    InpStochDPeriod         = 1;
input int    InpStochSlowing         = 3;
input double InpStochOversold        = 20.0;  // Stochastic oversold threshold
input double InpStochOverbought      = 80.0;  // Stochastic overbought threshold

//=== Entry-condition filters (v0.20, adjusted v2 -- see notes) ========
// Reference concept: "Volume Filter" -- avoid illiquid periods with poor
// execution / wide spreads (research: confirms activity before entry).
input bool   InpUseVolumeFilter      = true;
input int    InpVolumeAvgPeriod      = 20;

// Reference concept: "Volatility Filter" -- reject dead markets (poor
// R:R) and abnormal volatility spikes (often news/gap -- dangerous for
// mean reversion, since a spike can blow straight through the bands).
input bool   InpUseVolatilityFilter  = true;
input double InpVolatilityRatioMin   = 0.5;
input double InpVolatilityRatioMax   = 2.5;

// Reference concept: "Range Filter" -- FLIPPED for v2 (2026-07-14u).
// The v1 signal was trend-following, so it wanted HIGH ADX (strong
// trend). This v2 signal is MEAN-REVERSION, which wants the OPPOSITE:
// strong trends are dangerous here because price can "walk the band"
// straight through a Bollinger extreme without reverting. This filter
// now REJECTS entries when ADX is too high (too trendy), and favors
// ranging/choppy conditions instead.
// (2026-07-14v) Ceiling raised from 25 to 30 per founder's request for
// more trade frequency/opportunities -- lets moderately-trending
// conditions through, not just calm ranges. This is a direct
// frequency-vs-risk tradeoff: more setups qualify, but more of them
// will be entered while a real trend is starting to build.
input bool   InpUseRangeFilter            = true;
input int    InpAdxPeriod                 = 14;
input double InpAdxMaxForMeanReversion    = 30.0;  // reject entries when ADX exceeds this

// Reference concept: "Information Feed Filter" -- interpreted here as a
// data-sanity check: reject trading on stale quotes or abnormal spread.
// NOTE: the 30-point default is reasonable for major forex pairs but is
// almost certainly too tight for metals (XAUUSD spreads commonly run
// well above 30 points depending on broker's point convention) -- raise
// this input when trading gold/silver, don't rely on the default.
input bool   InpUseDataFeedFilter    = true;
input double InpMaxSpreadPoints      = 30.0;
input int    InpMaxQuoteStaleSeconds = 60;

// Reference concept: "Weekend Protection" / Friday-close / Monday-start
// -- avoids holding new risk into a weekend gap. Not present in prior
// drafts; added here as a straightforward, well-justified risk control.
input bool   InpUseWeekendProtection = true;
input int    InpFridayCloseAllHour   = 20;  // server time
input int    InpFridayEntryBlockHour = 16;  // server time
input int    InpMondayStartHour      = 2;   // server time

// Diagnostics (2026-07-14s) -- prints the specific reason no trade was
// taken, once per new bar, to the Experts/Journal log. Turn off once the
// EA is confirmed working to reduce log noise.
input bool   InpVerboseLogging       = true;

//=== Global state ======================================================
double   g_dayStartEquity = 0;
datetime g_lastLogBarTime = 0;
MqlDateTime g_dayKey;
int      g_handleBands, g_handleStoch, g_handleRsi, g_handleAtr, g_handleAdx;
bool     g_dailyHalted = false;

//+------------------------------------------------------------------+
//| Instrument restriction (2026-07-14u) -- founder asked for forex    |
//| and metals only. SYMBOL_TRADE_CALC_MODE reliably flags true forex  |
//| pairs; metals are commonly offered as CFD-calc-mode instruments on  |
//| most brokers, so calc mode alone isn't enough -- also check the     |
//| symbol name for XAU/XAG/XPT/XPD. This is a heuristic, not a         |
//| perfect classification (broker symbol-naming conventions vary) --   |
//| it fails CLOSED (refuses to run) on anything not clearly recognized |
//| rather than guessing.                                               |
//+------------------------------------------------------------------+
bool IsAllowedInstrument()
{
   ENUM_SYMBOL_CALC_MODE calcMode = (ENUM_SYMBOL_CALC_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_CALC_MODE);
   bool isForexCalc = (calcMode == SYMBOL_CALC_MODE_FOREX || calcMode == SYMBOL_CALC_MODE_FOREX_NO_LEVERAGE);

   string name = _Symbol;
   StringToUpper(name);
   bool isMetal = (StringFind(name, "XAU") >= 0 || StringFind(name, "XAG") >= 0 ||
                   StringFind(name, "XPT") >= 0 || StringFind(name, "XPD") >= 0);

   return (isForexCalc || isMetal);
}

//+------------------------------------------------------------------+
int OnInit()
{
   if(!IsAllowedInstrument())
   {
      PrintFormat("FatalibuildersTrader: %s is not a recognized forex or metals instrument. This EA is restricted to forex and metals only (2026-07-14u) -- refusing to initialize.", _Symbol);
      return(INIT_FAILED);
   }

   g_handleBands   = iBands(_Symbol, PERIOD_CURRENT, InpBollingerPeriod, 0, InpBollingerDeviation, PRICE_CLOSE);
   g_handleStoch   = iStochastic(_Symbol, PERIOD_CURRENT, InpStochKPeriod, InpStochDPeriod, InpStochSlowing, MODE_SMA, STO_LOWHIGH);
   g_handleRsi     = iRSI(_Symbol, PERIOD_CURRENT, InpRsiPeriod, PRICE_CLOSE);
   g_handleAtr     = iATR(_Symbol, PERIOD_CURRENT, InpAtrPeriod);
   g_handleAdx     = iADX(_Symbol, PERIOD_CURRENT, InpAdxPeriod);

   if(g_handleBands == INVALID_HANDLE || g_handleStoch == INVALID_HANDLE ||
      g_handleRsi == INVALID_HANDLE || g_handleAtr == INVALID_HANDLE ||
      g_handleAdx == INVALID_HANDLE)
   {
      Print("FatalibuildersTrader: failed to create indicator handles");
      return(INIT_FAILED);
   }

   trade.SetExpertMagicNumber(InpMagicNumber);
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

// Returns true if trading should be halted for the rest of the day.
bool CheckDailyLimits()
{
   if(IsNewDay())
      ResetDailyTracking();

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double changePct = (equity - g_dayStartEquity) / g_dayStartEquity * 100.0;

   double lossLimitPct = InpDailyLossLimitPct;                      // 3%, 2026-07-14i
   double profitTargetPct = (InpTradingMode == MODE_SAFE)
                              ? InpDailyProfitTargetSafePct          // 5%, 2026-07-14l
                              : InpDailyProfitTargetAggressivePct;   // 20%, 2026-07-14k

   if(changePct <= -lossLimitPct || changePct >= profitTargetPct)
   {
      if(!g_dailyHalted)
         PrintFormat("FatalibuildersTrader: daily limit reached (%.2f%%), halting until next day", changePct);
      g_dailyHalted = true;
   }
   return g_dailyHalted;
}

// Remaining daily loss budget in dollars, given today's equity so far.
// Resolves the tier-boundary interaction flagged 2026-07-14i: a single
// trade's risk must never exceed what's left of the day's loss budget.
double RemainingDailyLossBudget()
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double lossSoFar = MathMax(0.0, g_dayStartEquity - equity);
   double totalBudget = g_dayStartEquity * (InpDailyLossLimitPct / 100.0);
   return MathMax(0.0, totalBudget - lossSoFar);
}

//+------------------------------------------------------------------+
//| Risk parameters by equity tier + mode (2026-07-14f, 2026-07-14m)  |
//+------------------------------------------------------------------+
double GetStopLossDollars()
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double tierRisk = (equity < InpEquityTierBreakpoint) ? InpStopLossDollarsLowTier : InpStopLossDollarsHighTier;

   // Tier-boundary fix: never risk more on one trade than remains of the daily loss budget.
   double remaining = RemainingDailyLossBudget();
   return MathMin(tierRisk, remaining);
}

double GetProfitTargetDollars()
{
   if(InpTradingMode == MODE_AGGRESSIVE)
      return InpAggressiveModeTargetDollars;                        // $0.50, both tiers, 2026-07-14h

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   return (equity < InpEquityTierBreakpoint)
           ? InpSafeModeTargetDollarsLowTier                        // $1.50, 2026-07-14m
           : InpSafeModeTargetDollarsHighTier;                      // $3.00, 2026-07-14m
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
      return InpStartingLot;

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
   return (atr[0] * InpAtrStopMultiple) / point;
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
   datetime to   = TimeCurrent() + InpNewsLookaheadMinutes * 60;

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
   if(!InpUseVolumeFilter) return true;

   long vol[];
   ArraySetAsSeries(vol, true);
   if(CopyTickVolume(_Symbol, PERIOD_CURRENT, 0, InpVolumeAvgPeriod + 2, vol) <= 0)
      return true; // fail open -- don't block trading on a data hiccup

   long sum = 0;
   for(int i = 2; i <= InpVolumeAvgPeriod + 1; i++)
      sum += vol[i];
   double avgVol = (double)sum / InpVolumeAvgPeriod;

   return (double)vol[1] >= avgVol;
}

// "Volatility Filter": reject both dead markets (ATR far below its own
// recent average -- poor risk:reward, spread dominates) and abnormal
// spikes (ATR far above average -- often a news/gap event, not a clean
// trend the placeholder signal is designed for).
bool PassesVolatilityFilter()
{
   if(!InpUseVolatilityFilter) return true;

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
   return (ratio >= InpVolatilityRatioMin && ratio <= InpVolatilityRatioMax);
}

// "Range Filter" -- FLIPPED for v2 (2026-07-14u). The v1 signal was
// trend-following and wanted HIGH ADX; this v2 signal is MEAN-REVERSION
// and wants the OPPOSITE -- strong trends are dangerous for mean
// reversion (price can "walk the band" through a Bollinger extreme
// without reverting), so this now REJECTS entries when ADX is too high.
bool PassesRangeFilter()
{
   if(!InpUseRangeFilter) return true;

   double adx[];
   ArraySetAsSeries(adx, true);
   if(CopyBuffer(g_handleAdx, MAIN_LINE, 0, 1, adx) <= 0)
      return true;

   return adx[0] <= InpAdxMaxForMeanReversion;
}

// "Information Feed Filter": interpreted as a data-sanity check --
// reject trading on stale quotes or an abnormally wide spread, both
// signs of a bad/thin data feed moment rather than a real setup.
bool PassesDataFeedSanityCheck()
{
   if(!InpUseDataFeedFilter) return true;

   double spread = (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID))
                     / SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(spread > InpMaxSpreadPoints)
      return false;

   datetime lastTick = (datetime)SymbolInfoInteger(_Symbol, SYMBOL_TIME);
   if(TimeCurrent() - lastTick > InpMaxQuoteStaleSeconds)
      return false;

   return true;
}

// "Weekend Protection": avoid opening new risk into a weekend gap, and
// block new entries approaching Friday close / just after Monday open.
bool IsWeekendEntryBlocked()
{
   if(!InpUseWeekendProtection) return false;

   MqlDateTime t;
   TimeToStruct(TimeCurrent(), t);

   if(t.day_of_week == DOW_FRIDAY && t.hour >= InpFridayEntryBlockHour) return true;
   if(t.day_of_week == DOW_MONDAY && t.hour < InpMondayStartHour)       return true;
   return false;
}

// Force-close all FatalibuildersTrader positions ahead of the weekend close.
void ApplyWeekendCloseAll()
{
   if(!InpUseWeekendProtection) return;

   MqlDateTime t;
   TimeToStruct(TimeCurrent(), t);
   if(t.day_of_week != DOW_FRIDAY || t.hour < InpFridayCloseAllHour)
      return;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket) && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber)
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
   bool rsiOversold   = (rsi[1] <= InpRsiOversold);
   bool rsiOverbought = (rsi[1] >= InpRsiOverbought);

   // 3. Stochastic turn-confirmation: was in extreme territory, now
   //    turning back -- the actual entry trigger, not a static state
   bool stochTurningUp   = (stochMain[1] <= InpStochOversold   && stochMain[0] > stochMain[1]);
   bool stochTurningDown = (stochMain[1] >= InpStochOverbought && stochMain[0] < stochMain[1]);

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
      double extremity = (signal == SIGNAL_BUY) ? (InpRsiOversold - rsi[0]) : (rsi[0] - InpRsiOverbought);
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
      if(PositionSelectByTicket(ticket) && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber)
         count++;
   }
   return count;
}

// EXIT_BREAKEVEN_AND_RUN: once floating profit reaches the target, move
// SL to entry (lock breakeven) instead of closing outright, and let the
// position run without a hard TP (2026-07-14, dual-mode exit decision).
void ManageOpenPositions()
{
   if(InpExitMode != EXIT_BREAKEVEN_AND_RUN)
      return;

   for(int i = 0; i < PositionsTotal(); i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket) || PositionGetInteger(POSITION_MAGIC) != InpMagicNumber)
         continue;

      double profit = PositionGetDouble(POSITION_PROFIT);
      double target = GetProfitTargetDollars();
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double currentSl = PositionGetDouble(POSITION_SL);

      bool alreadyBreakeven = (MathAbs(currentSl - openPrice) < SymbolInfoDouble(_Symbol, SYMBOL_POINT));
      if(profit >= target && !alreadyBreakeven)
      {
         trade.PositionModify(ticket, openPrice, PositionGetDouble(POSITION_TP));
         PrintFormat("FatalibuildersTrader: moved position #%I64u to breakeven at $%.2f profit", ticket, profit);
      }
   }
}

//+------------------------------------------------------------------+
//| Diagnostic logging (2026-07-14s) -- prints once per new bar, not   |
//| every tick, so the log stays readable instead of flooding.         |
//+------------------------------------------------------------------+
void LogBlockReason(string reason)
{
   if(!InpVerboseLogging) return;

   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(barTime == g_lastLogBarTime) return; // already logged this bar

   g_lastLogBarTime = barTime;
   PrintFormat("FatalibuildersTrader [%s]: no trade -- %s", TimeToString(TimeCurrent(), TIME_SECONDS), reason);
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

   if(CountOpenPositions() >= InpMaxConcurrentTrades)
   {
      LogBlockReason(StringFormat("max concurrent trades reached (%d)", InpMaxConcurrentTrades));
      return; // 2026-07-14h: max 2 concurrent trades
   }

   if(IsWeekendEntryBlocked())
   {
      LogBlockReason("weekend protection window (near Friday close / Monday open)");
      return;
   }

   if(!PassesDataFeedSanityCheck())
   {
      double spreadNow = (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID))
                          / SymbolInfoDouble(_Symbol, SYMBOL_POINT);
      LogBlockReason(StringFormat("data feed check failed (spread=%.1f pts, max=%.1f, or stale quote)",
                     spreadNow, InpMaxSpreadPoints));
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
      LogBlockReason(StringFormat("range filter -- ADX too high for mean reversion (max=%.1f)", InpAdxMaxForMeanReversion));
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
      double requiredConfidence = (InpTradingMode == MODE_SAFE)
                                    ? InpSafeModeMinWinProbabilityPct        // 65-75%, 2026-07-14m
                                    : InpAggressiveModeMinWinProbabilityPct; // 50%, 2026-07-14v
      if(confidence < requiredConfidence)
      {
         LogBlockReason(StringFormat("confidence too low for %s (%.1f < %.1f required)",
                        (InpTradingMode == MODE_SAFE ? "Safe Mode" : "Aggressive Mode"),
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

   bool useHardTp = (InpExitMode == EXIT_OUTRIGHT_CLOSE);

   if(signal == SIGNAL_BUY)
   {
      double sl = ask - stopDistancePoints * point;
      double tp = useHardTp ? ask + targetDistancePoints * point : 0;
      if(trade.Buy(lots, _Symbol, ask, sl, tp, "FatalibuildersTrader"))
         PrintFormat("FatalibuildersTrader: BUY placed, lots=%.2f sl=%.5f tp=%.5f", lots, sl, tp);
      else
         PrintFormat("FatalibuildersTrader: BUY failed, retcode=%d (%s)", trade.ResultRetcode(), trade.ResultRetcodeDescription());
   }
   else if(signal == SIGNAL_SELL)
   {
      double sl = bid + stopDistancePoints * point;
      double tp = useHardTp ? bid - targetDistancePoints * point : 0;
      if(trade.Sell(lots, _Symbol, bid, sl, tp, "FatalibuildersTrader"))
         PrintFormat("FatalibuildersTrader: SELL placed, lots=%.2f sl=%.5f tp=%.5f", lots, sl, tp);
      else
         PrintFormat("FatalibuildersTrader: SELL failed, retcode=%d (%s)", trade.ResultRetcode(), trade.ResultRetcodeDescription());
   }
}
