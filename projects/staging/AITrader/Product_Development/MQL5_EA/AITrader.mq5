//+------------------------------------------------------------------+
//| AITrader.mq5                                                      |
//| Draft v0.30 -- implements the risk-management, dual-mode, daily-  |
//| control, entry-filter, and (v0.30) signal-design decisions from   |
//| Master-Context.md as of 2026-07-14.                                |
//|                                                                    |
//| NOT PRODUCTION READY. See the "OPEN ITEMS / PLACEHOLDERS" block   |
//| below and Product_Development/MQL5_EA/README.md before trusting   |
//| any part of this for real trading. Not yet compiled or backtested.|
//+------------------------------------------------------------------+
#property copyright "AITrader"
#property version   "1.00"
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
//| 1. ENTRY SIGNAL LOGIC (GetEntrySignal, below) is now a REAL v1    |
//|    HYPOTHESIS, not a throwaway placeholder: a multi-timeframe      |
//|    trend + pullback momentum entry, grounded in published/widely-  |
//|    taught methodology (see decisions-learnings/2026-07-14q). This  |
//|    replaces the earlier naive single-timeframe EMA crossover.      |
//|    IMPORTANT: "grounded in published methodology" is NOT the same  |
//|    as "proven to work for AITrader" -- this specific parameter set |
//|    has never been backtested. Treat it as a serious starting point |
//|    to validate, not a finished strategy.                           |
//|                                                                    |
//| 2. GetSignalConfidence() (Safe Mode's 65-75% win-probability       |
//|    filter) is now a rule-based heuristic (ADX trend strength +     |
//|    RSI momentum conviction), upgraded from a flat placeholder      |
//|    value. It is EXPLICITLY NOT a calibrated probability -- it has  |
//|    never been checked against real win-rate outcomes. Needs real   |
//|    backtest validation before Safe Mode's filter threshold means   |
//|    anything statistically.                                        |
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
//+------------------------------------------------------------------+

//=== Trading mode / exit mode ========================================
enum ENUM_TRADING_MODE  { MODE_SAFE, MODE_AGGRESSIVE };
enum ENUM_EXIT_MODE     { EXIT_OUTRIGHT_CLOSE, EXIT_BREAKEVEN_AND_RUN };

//=== Inputs -- values below match Master-Context.md decisions =======
input ENUM_TRADING_MODE InpTradingMode              = MODE_SAFE;
input ENUM_EXIT_MODE    InpExitMode                 = EXIT_OUTRIGHT_CLOSE;

input double InpEquityTierBreakpoint                = 50.0;   // 2026-07-14f
input double InpStopLossDollarsLowTier              = 1.0;    // 2026-07-14f
input double InpStopLossDollarsHighTier             = 3.0;    // 2026-07-14f

input double InpSafeModeTargetDollarsLowTier        = 1.50;   // 2026-07-14m
input double InpSafeModeTargetDollarsHighTier       = 3.00;   // 2026-07-14m
input double InpSafeModeMinWinProbabilityPct        = 65.0;   // 2026-07-14m (65-75% range; floor used here)
input double InpAggressiveModeTargetDollars         = 0.50;   // 2026-07-14h

input double InpDailyLossLimitPct                   = 3.0;    // 2026-07-14i
input double InpDailyProfitTargetSafePct            = 5.0;    // 2026-07-14l
input double InpDailyProfitTargetAggressivePct      = 20.0;   // 2026-07-14k

input int    InpMaxConcurrentTrades                 = 2;      // 2026-07-14h
input double InpStartingLot                         = 0.01;   // 2026-07-14e
input int    InpAtrPeriod                           = 14;     // placeholder stop-distance basis
input double InpAtrStopMultiple                     = 1.0;    // placeholder
input int    InpNewsLookaheadMinutes                = 30;     // placeholder news window
input int    InpMagicNumber                         = 20260714;

//=== Signal v1 -- multi-timeframe trend + pullback momentum entry ====
// (2026-07-14q) Replaces the earlier naive single-timeframe EMA
// crossover. Grounded in a widely-documented, widely-taught retail/
// research methodology: trade only with the higher-timeframe trend,
// enter on a confirmed pullback + momentum-resumption trigger on the
// trading timeframe. This is a v1 HYPOTHESIS, not a proven edge --
// still requires real backtesting before being trusted. See
// decisions-learnings/2026-07-14q_signal_design_v1.md for the sourcing
// and reasoning.
input ENUM_TIMEFRAMES InpHigherTimeframe   = PERIOD_H1;  // trend-direction timeframe
input int    InpHigherTrendMaPeriod        = 200;        // higher-TF trend MA period
input int    InpPullbackMaPeriod           = 20;         // trading-TF pullback MA period
input int    InpRsiPeriod                  = 14;         // momentum-resumption trigger
input double InpMomentumRsiUpLevel         = 40.0;       // RSI crossing up through this = uptrend resumption
input double InpMomentumRsiDownLevel       = 60.0;       // RSI crossing down through this = downtrend resumption

//=== Entry-condition filters (v0.20) -- see header note above ========
// Reference concept: "Volume Filter" -- avoid illiquid periods with poor
// execution / wide spreads (research: confirms activity before entry).
input bool   InpUseVolumeFilter      = true;
input int    InpVolumeAvgPeriod      = 20;

// Reference concept: "Volatility Filter" -- reject dead markets (poor
// R:R) and abnormal volatility spikes (often news/gap, not clean trend).
input bool   InpUseVolatilityFilter  = true;
input double InpVolatilityRatioMin   = 0.5;
input double InpVolatilityRatioMax   = 2.5;

// Reference concept: "Range Filter" -- our EMA-crossover signal is
// trend-following, so the useful pairing is a trend-strength gate
// (ADX) that skips choppy/ranging conditions where crossovers whipsaw.
input bool   InpUseRangeFilter       = true;
input int    InpAdxPeriod            = 14;
input double InpAdxTrendThreshold    = 20.0;

// Reference concept: "Information Feed Filter" -- interpreted here as a
// data-sanity check: reject trading on stale quotes or abnormal spread.
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

//=== Global state ======================================================
double   g_dayStartEquity = 0;
MqlDateTime g_dayKey;
int      g_handleHigherTrendMa, g_handlePullbackMa, g_handleRsi, g_handleAtr, g_handleAdx;
bool     g_dailyHalted = false;

//+------------------------------------------------------------------+
int OnInit()
{
   g_handleHigherTrendMa = iMA(_Symbol, InpHigherTimeframe, InpHigherTrendMaPeriod, 0, MODE_SMA, PRICE_CLOSE);
   g_handlePullbackMa    = iMA(_Symbol, PERIOD_CURRENT, InpPullbackMaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   g_handleRsi     = iRSI(_Symbol, PERIOD_CURRENT, InpRsiPeriod, PRICE_CLOSE);
   g_handleAtr     = iATR(_Symbol, PERIOD_CURRENT, InpAtrPeriod);
   g_handleAdx     = iADX(_Symbol, PERIOD_CURRENT, InpAdxPeriod);

   if(g_handleHigherTrendMa == INVALID_HANDLE || g_handlePullbackMa == INVALID_HANDLE ||
      g_handleRsi == INVALID_HANDLE || g_handleAtr == INVALID_HANDLE ||
      g_handleAdx == INVALID_HANDLE)
   {
      Print("AITrader: failed to create indicator handles");
      return(INIT_FAILED);
   }

   trade.SetExpertMagicNumber(InpMagicNumber);
   ResetDailyTracking();
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   IndicatorRelease(g_handleHigherTrendMa);
   IndicatorRelease(g_handlePullbackMa);
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
         PrintFormat("AITrader: daily limit reached (%.2f%%), halting until next day", changePct);
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

// "Volume Filter": only trade when current bar's tick volume is at or
// above its recent average -- avoids illiquid periods (poor execution,
// wider spreads).
bool PassesVolumeFilter()
{
   if(!InpUseVolumeFilter) return true;

   long vol[];
   ArraySetAsSeries(vol, true);
   if(CopyTickVolume(_Symbol, PERIOD_CURRENT, 0, InpVolumeAvgPeriod + 1, vol) <= 0)
      return true; // fail open -- don't block trading on a data hiccup

   long sum = 0;
   for(int i = 1; i <= InpVolumeAvgPeriod; i++)
      sum += vol[i];
   double avgVol = (double)sum / InpVolumeAvgPeriod;

   return (double)vol[0] >= avgVol;
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

// "Range Filter": the placeholder signal (EMA crossover) is trend-
// following, so the useful pairing is an ADX trend-strength gate --
// skip choppy/ranging conditions where crossovers tend to whipsaw.
bool PassesRangeFilter()
{
   if(!InpUseRangeFilter) return true;

   double adx[];
   ArraySetAsSeries(adx, true);
   if(CopyBuffer(g_handleAdx, MAIN_LINE, 0, 1, adx) <= 0)
      return true;

   return adx[0] >= InpAdxTrendThreshold;
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

// Force-close all AITrader positions ahead of the weekend close.
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
//| SIGNAL v1 -- multi-timeframe trend + pullback momentum entry.     |
//| (2026-07-14q, replaces the earlier naive EMA-crossover placeholder|
//| from v0.10.) This is a well-documented, widely-taught approach,   |
//| not something invented for this project -- see                   |
//| decisions-learnings/2026-07-14q_signal_design_v1.md for sourcing. |
//| It is still a v1 HYPOTHESIS: real behind it is published research |
//| on the general approach, not a backtest of THIS specific parameter|
//| set on real AITrader data. Treat as a starting point to validate, |
//| not a proven edge.                                                |
//|                                                                    |
//| Logic:                                                             |
//|  1. Determine trend direction on a HIGHER timeframe (default H1)  |
//|     using price vs. a slow MA (default 200 SMA).                  |
//|  2. On the TRADING timeframe, require price to have pulled back    |
//|     to/through a shorter MA (default 20 EMA) -- i.e. a genuine dip |
//|     against the higher-timeframe trend, not a trade chasing a move |
//|     that's already extended.                                      |
//|  3. Require a momentum-resumption trigger: RSI crossing back       |
//|     through a level (default 40 up / 60 down) confirms the pullback|
//|     is over and the higher-timeframe trend is reasserting.         |
//| Paired with the existing ADX/volume/volatility filters (v0.20),    |
//| which were already designed to suit a trend-following signal.     |
//+------------------------------------------------------------------+
enum ENUM_SIGNAL { SIGNAL_NONE, SIGNAL_BUY, SIGNAL_SELL };

ENUM_SIGNAL GetEntrySignal()
{
   // 1. Higher-timeframe trend direction: price vs. slow MA
   double higherTrendMa[];
   ArraySetAsSeries(higherTrendMa, true);
   if(CopyBuffer(g_handleHigherTrendMa, 0, 0, 1, higherTrendMa) <= 0) return SIGNAL_NONE;

   double higherClose[];
   ArraySetAsSeries(higherClose, true);
   if(CopyClose(_Symbol, InpHigherTimeframe, 0, 1, higherClose) <= 0) return SIGNAL_NONE;

   bool higherTrendUp   = higherClose[0] > higherTrendMa[0];
   bool higherTrendDown = higherClose[0] < higherTrendMa[0];

   // 2. Trading-timeframe pullback: was price at/through the short MA
   //    on the prior bar (i.e. dipped against the higher-TF trend)?
   double pullbackMa[];
   ArraySetAsSeries(pullbackMa, true);
   if(CopyBuffer(g_handlePullbackMa, 0, 0, 2, pullbackMa) <= 0) return SIGNAL_NONE;

   double close[];
   ArraySetAsSeries(close, true);
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 2, close) <= 0) return SIGNAL_NONE;

   bool pulledBackAgainstUptrend   = (close[1] <= pullbackMa[1]);
   bool pulledBackAgainstDowntrend = (close[1] >= pullbackMa[1]);

   // 3. Momentum-resumption trigger: RSI crossing back through its level
   double rsi[];
   ArraySetAsSeries(rsi, true);
   if(CopyBuffer(g_handleRsi, 0, 0, 2, rsi) <= 0) return SIGNAL_NONE;

   bool momentumResumeUp   = (rsi[1] <= InpMomentumRsiUpLevel   && rsi[0] > InpMomentumRsiUpLevel);
   bool momentumResumeDown = (rsi[1] >= InpMomentumRsiDownLevel && rsi[0] < InpMomentumRsiDownLevel);

   if(higherTrendUp   && pulledBackAgainstUptrend   && momentumResumeUp)   return SIGNAL_BUY;
   if(higherTrendDown && pulledBackAgainstDowntrend && momentumResumeDown) return SIGNAL_SELL;
   return SIGNAL_NONE;
}

//+------------------------------------------------------------------+
//| Confidence score -- Safe Mode's 65-75% win-probability filter      |
//| (2026-07-14m). Upgraded (2026-07-14q) from a flat placeholder to a |
//| rule-based heuristic combining trend strength (ADX) and momentum   |
//| conviction (RSI distance from neutral). This is EXPLICITLY NOT a   |
//| calibrated probability -- it has not been checked against real     |
//| win-rate outcomes. It's an honest, explainable scoring rule, not   |
//| the reference EA's "AI Filter" -- deliberately not labeled "AI"     |
//| since no model has been trained or validated (see header note).    |
//| Must be validated against real backtest win rates before Safe      |
//| Mode's filter threshold means anything statistically.              |
//+------------------------------------------------------------------+
double GetSignalConfidence(ENUM_SIGNAL signal)
{
   double adx[];
   ArraySetAsSeries(adx, true);
   double adxScore = 50.0; // neutral default if data unavailable
   if(CopyBuffer(g_handleAdx, MAIN_LINE, 0, 1, adx) > 0)
      adxScore = MathMin(100.0, adx[0] * 2.0); // ADX typically ~0-50 -> scaled to 0-100

   double rsi[];
   ArraySetAsSeries(rsi, true);
   double rsiScore = 50.0;
   if(CopyBuffer(g_handleRsi, 0, 0, 1, rsi) > 0)
   {
      double distanceFromMid = MathAbs(rsi[0] - 50.0); // 0-50
      rsiScore = MathMin(100.0, distanceFromMid * 2.0);
   }

   return (adxScore + rsiScore) / 2.0;
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
         PrintFormat("AITrader: moved position #%I64u to breakeven at $%.2f profit", ticket, profit);
      }
   }
}

//+------------------------------------------------------------------+
void OnTick()
{
   ManageOpenPositions();
   ApplyWeekendCloseAll();

   if(CheckDailyLimits())
      return; // daily profit target or loss limit reached -- no new trades today

   if(CountOpenPositions() >= InpMaxConcurrentTrades)
      return; // 2026-07-14h: max 2 concurrent trades

   if(IsWeekendEntryBlocked())
      return; // v0.20: weekend protection -- no new risk into a weekend gap

   if(!PassesDataFeedSanityCheck())
      return; // v0.20: stale quotes / abnormal spread

   if(IsHighImpactNewsWindow())
      return; // first-pass reaction: skip new entries near high-impact news

   if(!PassesVolumeFilter() || !PassesVolatilityFilter() || !PassesRangeFilter())
      return; // v0.20: entry-condition filters -- see header note

   ENUM_SIGNAL signal = GetEntrySignal();
   if(signal == SIGNAL_NONE)
      return;

   if(InpTradingMode == MODE_SAFE)
   {
      double confidence = GetSignalConfidence(signal);
      if(confidence < InpSafeModeMinWinProbabilityPct)
         return; // 2026-07-14m: Safe Mode only takes 65-75%+ confidence setups
   }

   double stopDistancePoints = GetStopDistancePoints();
   double riskDollars = GetStopLossDollars();
   double targetDollars = GetProfitTargetDollars();

   if(riskDollars <= 0)
      return; // daily loss budget fully consumed

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
      trade.Buy(lots, _Symbol, ask, sl, tp, "AITrader");
   }
   else if(signal == SIGNAL_SELL)
   {
      double sl = bid + stopDistancePoints * point;
      double tp = useHardTp ? bid - targetDistancePoints * point : 0;
      trade.Sell(lots, _Symbol, bid, sl, tp, "AITrader");
   }
}
