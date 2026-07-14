//+------------------------------------------------------------------+
//| AITrader.mq5                                                      |
//| Draft v0.1 -- implements the risk-management, dual-mode, and      |
//| daily-control decisions from Master-Context.md as of 2026-07-14.  |
//|                                                                    |
//| NOT PRODUCTION READY. See the "OPEN ITEMS / PLACEHOLDERS" block   |
//| below and Product_Development/MQL5_EA/README.md before trusting   |
//| any part of this for real trading. Not yet compiled or backtested.|
//+------------------------------------------------------------------+
#property copyright "AITrader"
#property version   "0.10"
#property strict

#include <Trade\Trade.mqh>
CTrade trade;

//+------------------------------------------------------------------+
//| OPEN ITEMS / PLACEHOLDERS -- read before using this file          |
//|                                                                    |
//| 1. ENTRY SIGNAL LOGIC (SignalDirection, below) is a PLACEHOLDER.  |
//|    Nothing in the staging process ever specified what actually    |
//|    triggers a trade -- every decision so far has been about risk  |
//|    management, exits, and sizing, not the "AI" signal itself.     |
//|    This file uses a simple EMA-crossover + RSI filter as a        |
//|    stand-in so the EA is structurally complete and testable.      |
//|    This is the single biggest remaining design gap.               |
//|                                                                    |
//| 2. GetSignalConfidence() (Safe Mode's 65-75% win-probability       |
//|    filter) is a PLACEHOLDER stub. No real confidence-scoring       |
//|    model exists yet -- it needs to come from actual backtested     |
//|    setup classification once the real signal logic is built.      |
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

//=== EMA / RSI placeholder signal inputs =============================
input int    InpFastEmaPeriod = 12;
input int    InpSlowEmaPeriod = 26;
input int    InpRsiPeriod     = 14;

//=== Global state ======================================================
double   g_dayStartEquity = 0;
MqlDateTime g_dayKey;
int      g_handleFastEma, g_handleSlowEma, g_handleRsi, g_handleAtr;
bool     g_dailyHalted = false;

//+------------------------------------------------------------------+
int OnInit()
{
   g_handleFastEma = iMA(_Symbol, PERIOD_CURRENT, InpFastEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   g_handleSlowEma = iMA(_Symbol, PERIOD_CURRENT, InpSlowEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   g_handleRsi     = iRSI(_Symbol, PERIOD_CURRENT, InpRsiPeriod, PRICE_CLOSE);
   g_handleAtr     = iATR(_Symbol, PERIOD_CURRENT, InpAtrPeriod);

   if(g_handleFastEma == INVALID_HANDLE || g_handleSlowEma == INVALID_HANDLE ||
      g_handleRsi == INVALID_HANDLE || g_handleAtr == INVALID_HANDLE)
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
   IndicatorRelease(g_handleFastEma);
   IndicatorRelease(g_handleSlowEma);
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
//| PLACEHOLDER SIGNAL LOGIC -- see OPEN ITEMS block at top of file.  |
//| Simple EMA crossover + RSI filter, purely a structural stand-in.  |
//+------------------------------------------------------------------+
enum ENUM_SIGNAL { SIGNAL_NONE, SIGNAL_BUY, SIGNAL_SELL };

ENUM_SIGNAL GetEntrySignal()
{
   double fastEma[], slowEma[], rsi[];
   ArraySetAsSeries(fastEma, true);
   ArraySetAsSeries(slowEma, true);
   ArraySetAsSeries(rsi, true);

   if(CopyBuffer(g_handleFastEma, 0, 0, 2, fastEma) <= 0) return SIGNAL_NONE;
   if(CopyBuffer(g_handleSlowEma, 0, 0, 2, slowEma) <= 0) return SIGNAL_NONE;
   if(CopyBuffer(g_handleRsi, 0, 0, 1, rsi) <= 0) return SIGNAL_NONE;

   bool crossedUp   = (fastEma[1] <= slowEma[1] && fastEma[0] > slowEma[0]);
   bool crossedDown = (fastEma[1] >= slowEma[1] && fastEma[0] < slowEma[0]);

   if(crossedUp && rsi[0] < 70) return SIGNAL_BUY;
   if(crossedDown && rsi[0] > 30) return SIGNAL_SELL;
   return SIGNAL_NONE;
}

//+------------------------------------------------------------------+
//| PLACEHOLDER confidence score -- Safe Mode's 65-75% win-probability |
//| filter (2026-07-14m). No real model exists; stub returns a fixed   |
//| value so the EA is structurally complete. Must be replaced with a  |
//| real, backtested confidence estimate before this filter means      |
//| anything.                                                          |
//+------------------------------------------------------------------+
double GetSignalConfidence(ENUM_SIGNAL signal)
{
   // TODO: replace with a real model (e.g., historical win-rate by
   // setup type/volatility regime/session, derived from backtesting).
   return 70.0; // placeholder mid-range value
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

   if(CheckDailyLimits())
      return; // daily profit target or loss limit reached -- no new trades today

   if(CountOpenPositions() >= InpMaxConcurrentTrades)
      return; // 2026-07-14h: max 2 concurrent trades

   if(IsHighImpactNewsWindow())
      return; // first-pass reaction: skip new entries near high-impact news

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
