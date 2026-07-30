// TeleScalper PRO — aggressive cTrader Automate cBot
//
// Same Telegram signal engine as TeleScalper, tuned to press winners much harder:
//   - risk-% position sizing (default 2% per signal) instead of a fixed 0.01 lot
//   - every signal is split into several positions with laddered targets (TP1/TP2/TP3),
//     and missing targets are extrapolated from the signal's own risk distance (R)
//   - once the first target is banked the rest of the ladder goes to break even and the
//     runner switches to a trailing stop
//   - optional pyramiding: adds to a group that is already winning
//   - optional recovery re-entry after a stopped-out signal (off by default, hard capped)
//   - daily loss circuit breaker that shuts trading down for the rest of the day
//
// Aggression cuts both ways: bigger size, more positions and pyramiding all raise the
// speed at which an account can be drawn down. Run it on demo first and set the daily
// loss limit before you let it near real money.
//
// Requires AccessRights.FullAccess (outbound HTTPS to api.telegram.org).

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    public enum SizingMode
    {
        RiskPercent,
        FixedLots
    }

    [Robot(AccessRights = AccessRights.FullAccess, AddIndicators = false, TimeZone = TimeZones.UTC)]
    public class TeleScalperPro : Robot
    {
        // ----------------------------------------------------------------- parameters

        [Parameter("Bot token", Group = "Telegram", DefaultValue = "")]
        public string BotToken { get; set; }

        [Parameter("Signal chat IDs (comma separated, max 5)", Group = "Telegram", DefaultValue = "")]
        public string SignalChatIds { get; set; }

        [Parameter("Admin / notify chat ID", Group = "Telegram", DefaultValue = "")]
        public string NotifyChatId { get; set; }

        [Parameter("Poll interval (seconds)", Group = "Telegram", DefaultValue = 2, MinValue = 1, MaxValue = 60)]
        public int PollSeconds { get; set; }

        [Parameter("Ignore signals older than (minutes, 0 = off)", Group = "Telegram", DefaultValue = 15, MinValue = 0, MaxValue = 1440)]
        public int MaxSignalAgeMinutes { get; set; }

        [Parameter("Enable trading", Group = "Trading", DefaultValue = true)]
        public bool EnableTrading { get; set; }

        [Parameter("Sizing mode", Group = "Trading", DefaultValue = SizingMode.RiskPercent)]
        public SizingMode Sizing { get; set; }

        [Parameter("Risk % of balance per signal", Group = "Trading", DefaultValue = 2.0, MinValue = 0.01, MaxValue = 20, Step = 0.25)]
        public double RiskPercent { get; set; }

        [Parameter("Fixed lots per signal", Group = "Trading", DefaultValue = 0.03, MinValue = 0.001, Step = 0.01)]
        public double FixedLots { get; set; }

        [Parameter("Entries per signal (ladder)", Group = "Trading", DefaultValue = 3, MinValue = 1, MaxValue = 5)]
        public int EntriesPerSignal { get; set; }

        [Parameter("Max open trades", Group = "Trading", DefaultValue = 20, MinValue = 1, MaxValue = 200)]
        public int MaxOpenTrades { get; set; }

        [Parameter("Max open trades per symbol", Group = "Trading", DefaultValue = 9, MinValue = 1, MaxValue = 100)]
        public int MaxTradesPerSymbol { get; set; }

        [Parameter("Max spread (pips, 0 = off)", Group = "Trading", DefaultValue = 0, MinValue = 0)]
        public double MaxSpreadPips { get; set; }

        [Parameter("Fallback SL (pips, 0 = require SL)", Group = "Trading", DefaultValue = 0, MinValue = 0)]
        public double FallbackStopLossPips { get; set; }

        [Parameter("Symbol whitelist (empty = all)", Group = "Trading", DefaultValue = "")]
        public string SymbolWhitelist { get; set; }

        [Parameter("Broker symbol suffix", Group = "Trading", DefaultValue = "")]
        public string SymbolSuffix { get; set; }

        [Parameter("Extra symbol map (SIGNAL=BROKER, comma separated)", Group = "Trading", DefaultValue = "")]
        public string SymbolMap { get; set; }

        [Parameter("Trade label", Group = "Trading", DefaultValue = "TeleScalperPro")]
        public string TradeLabel { get; set; }

        [Parameter("Extra target step (R multiples)", Group = "Targets", DefaultValue = 1.5, MinValue = 0.25, MaxValue = 10, Step = 0.25)]
        public double ExtraTargetStepR { get; set; }

        [Parameter("Break even after first target", Group = "Management", DefaultValue = true)]
        public bool BreakEvenAfterFirstTarget { get; set; }

        [Parameter("Break even buffer (pips)", Group = "Management", DefaultValue = 1.0, MinValue = 0, Step = 0.1)]
        public double BreakEvenBufferPips { get; set; }

        [Parameter("Trail start (R multiple, 0 = off)", Group = "Management", DefaultValue = 1.0, MinValue = 0, MaxValue = 10, Step = 0.25)]
        public double TrailStartR { get; set; }

        [Parameter("Trail distance (R multiple)", Group = "Management", DefaultValue = 0.75, MinValue = 0.1, MaxValue = 10, Step = 0.25)]
        public double TrailDistanceR { get; set; }

        [Parameter("Pyramid adds per signal (0 = off)", Group = "Aggression", DefaultValue = 1, MinValue = 0, MaxValue = 5)]
        public int MaxPyramidAdds { get; set; }

        [Parameter("Pyramid trigger (R multiple)", Group = "Aggression", DefaultValue = 1.0, MinValue = 0.25, MaxValue = 10, Step = 0.25)]
        public double PyramidTriggerR { get; set; }

        [Parameter("Pyramid size factor", Group = "Aggression", DefaultValue = 0.5, MinValue = 0.1, MaxValue = 2, Step = 0.1)]
        public double PyramidSizeFactor { get; set; }

        [Parameter("Recovery re-entries after SL (0 = off)", Group = "Aggression", DefaultValue = 0, MinValue = 0, MaxValue = 3)]
        public int MaxRecoverySteps { get; set; }

        [Parameter("Recovery size multiplier", Group = "Aggression", DefaultValue = 1.5, MinValue = 1, MaxValue = 3, Step = 0.1)]
        public double RecoveryMultiplier { get; set; }

        [Parameter("Daily loss limit % (0 = off)", Group = "Risk guard", DefaultValue = 10, MinValue = 0, MaxValue = 100, Step = 1)]
        public double MaxDailyLossPercent { get; set; }

        [Parameter("Max total risk % open at once (0 = off)", Group = "Risk guard", DefaultValue = 12, MinValue = 0, MaxValue = 100, Step = 1)]
        public double MaxOpenRiskPercent { get; set; }

        [Parameter("Verbose logging", Group = "Diagnostics", DefaultValue = true)]
        public bool VerboseLogging { get; set; }

        // ----------------------------------------------------------------- state

        private sealed class IncomingMessage
        {
            public long ChatId;
            public string Text;
            public DateTime UtcTime;
        }

        private sealed class ParsedSignal
        {
            public string BrokerSymbol;
            public TradeType Direction;
            public double? Entry;
            public double StopLoss;
            public List<double> Targets;
            public string Fingerprint;
            public long ChatId;
        }

        private sealed class LegState
        {
            public string Fingerprint;
            public double Target;
            public double RiskDistance;
            public double EntryPrice;
            public bool IsRunner;
            public bool BreakEvenDone;
        }

        private sealed class GroupState
        {
            public string Fingerprint;
            public string SymbolName;
            public TradeType Direction;
            public double RiskDistance;
            public double InitialStopLoss;
            public double FurthestTarget;
            public double BaseVolume;
            public int PyramidAdds;
            public int RecoveryStep;
            public bool FirstTargetBanked;
            public int OpenLegs;
            public double RealisedNet;
        }

        private const int MaxSignalGroups = 5;

        private static readonly Dictionary<string, string> SymbolAliases = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
        {
            { "GOLD", "XAUUSD" }, { "XAU", "XAUUSD" }, { "GOLDUSD", "XAUUSD" },
            { "SILVER", "XAGUSD" }, { "XAG", "XAGUSD" },
            { "DOW", "US30" }, { "DJ30", "US30" }, { "DJI30", "US30" }, { "WALLSTREET30", "US30" },
            { "NASDAQ", "NAS100" }, { "NAS", "NAS100" }, { "USTEC", "NAS100" }, { "NDX100", "NAS100" },
            { "SPX", "US500" }, { "SPX500", "US500" }, { "SP500", "US500" },
            { "DAX", "GER40" }, { "DAX40", "GER40" }, { "GER30", "GER40" },
            { "UK100", "UK100" }, { "FTSE", "UK100" }, { "FTSE100", "UK100" },
            { "JP225", "JPN225" }, { "NIKKEI", "JPN225" },
            { "USOIL", "USOIL" }, { "WTI", "USOIL" }, { "CRUDE", "USOIL" }, { "CL", "USOIL" },
            { "UKOIL", "UKOIL" }, { "BRENT", "UKOIL" },
            { "BTC", "BTCUSD" }, { "BITCOIN", "BTCUSD" }, { "XBTUSD", "BTCUSD" },
            { "ETH", "ETHUSD" }, { "ETHEREUM", "ETHUSD" }
        };

        private static readonly string[] CommonSuffixes = { "", ".r", ".a", ".p", ".pro", ".ecn", ".raw", ".cash", ".spot", ".std", "m", "c", "z", "#", "_", "-ECN", ".m" };

        private static readonly Regex DirectionRegex = new Regex(@"\b(BUY|SELL|LONG|SHORT)\b", RegexOptions.IgnoreCase | RegexOptions.Compiled);
        private static readonly Regex StopLossRegex = new Regex(@"\b(?:SL|S/L|S\.L|STOP\s*-?\s*LOSS|STOPLOSS)\b\s*[:=\-@]?\s*([0-9]+(?:[.,][0-9]+)*)", RegexOptions.IgnoreCase | RegexOptions.Compiled);
        private static readonly Regex TakeProfitRegex = new Regex(@"\b(?:TP|T/P|T\.P|TAKE\s*-?\s*PROFIT|TARGET)\s*([0-9])?\b\s*[:=\-@]?\s*([0-9]+(?:[.,][0-9]+)*)", RegexOptions.IgnoreCase | RegexOptions.Compiled);
        private static readonly Regex EntryRegex = new Regex(@"(?:\b(?:ENTRY\s*PRICE|ENTRY|ENTER|EP|OPEN\s*PRICE|BUY|SELL|LONG|SHORT)\b|@)\s*(?:LIMIT|STOP|NOW|AT|ZONE|PRICE)?\s*[:=@\-]?\s*([0-9]+(?:[.,][0-9]+)*)", RegexOptions.IgnoreCase | RegexOptions.Compiled);
        private static readonly Regex SymbolTokenRegex = new Regex(@"\b([A-Za-z]{2,}(?:[ ]?[0-9]{1,3})?(?:/[A-Za-z]{3})?)\b", RegexOptions.Compiled);
        private static readonly Regex CommandRegex = new Regex(@"^/([a-zA-Z]+)(?:@\S+)?(?:\s+(.*))?$", RegexOptions.Compiled);

        private readonly ConcurrentQueue<IncomingMessage> _incoming = new ConcurrentQueue<IncomingMessage>();
        private readonly Dictionary<int, LegState> _legs = new Dictionary<int, LegState>();
        private readonly Dictionary<string, GroupState> _groups = new Dictionary<string, GroupState>(StringComparer.OrdinalIgnoreCase);
        private readonly HashSet<string> _seenFingerprints = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, string> _symbolResolveCache = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, string> _userSymbolMap = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        private readonly HashSet<long> _signalChats = new HashSet<long>();
        private readonly HashSet<string> _whitelist = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        private HttpClient _http;
        private CancellationTokenSource _cts;
        private long _updateOffset;
        private long? _adminChatId;
        private string _apiBase;
        private bool _tradingEnabled;
        private bool _telegramReady;
        private bool _dayLocked;
        private DateTime _currentDay;
        private double _dayStartBalance;
        private int _signalsAccepted;
        private int _signalsRejected;
        private int _tradesOpened;
        private DateTime? _lastSignalUtc;
        private string _lastPollError;

        // ----------------------------------------------------------------- lifecycle

        protected override void OnStart()
        {
            _tradingEnabled = EnableTrading;
            TradeLabel = string.IsNullOrWhiteSpace(TradeLabel) ? "TeleScalperPro" : TradeLabel.Trim();
            _currentDay = Server.Time.Date;
            _dayStartBalance = Account.Balance;

            ParseChatIds();
            ParseSymbolMap();
            ParseWhitelist();
            RestoreStateFromOpenPositions();

            Positions.Closed += OnPositionClosed;

            _telegramReady = !string.IsNullOrWhiteSpace(BotToken) && _signalChats.Count > 0;
            if (!_telegramReady)
            {
                Print("TeleScalperPro: bot token and/or signal chat IDs are missing — no signals will be read.");
            }
            else
            {
                _apiBase = "https://api.telegram.org/bot" + BotToken.Trim();
                _http = new HttpClient();
                _http.Timeout = TimeSpan.FromSeconds(PollSeconds + 25);
                _cts = new CancellationTokenSource();
                Task.Run(() => PollLoopAsync(_cts.Token));
            }

            Timer.Start(TimeSpan.FromSeconds(1));

            Print("TeleScalperPro started | account {0} | trading {1} | ladder {2} | risk {3}",
                Account.Number, _tradingEnabled ? "ON" : "OFF", EntriesPerSignal, DescribeSizing());

            Notify(string.Format(CultureInfo.InvariantCulture,
                "🔥 TeleScalper PRO started\nAccount: {0} ({1})\nTrading: {2}\nSize: {3}\nLadder: {4} entries/signal\nMax trades: {5}\nDaily loss limit: {6}",
                Account.Number, Account.IsLive ? "LIVE" : "DEMO", _tradingEnabled ? "ON" : "OFF",
                DescribeSizing(), EntriesPerSignal, MaxOpenTrades,
                MaxDailyLossPercent > 0 ? MaxDailyLossPercent.ToString("0.#", CultureInfo.InvariantCulture) + "%" : "off"));
        }

        protected override void OnTimer()
        {
            CheckDayRollover();
            DrainIncoming();
            ManageOpenPositions();
        }

        protected override void OnStop()
        {
            try
            {
                if (_cts != null)
                    _cts.Cancel();
            }
            catch (Exception ex)
            {
                Print("TeleScalperPro: cancel error: {0}", ex.Message);
            }

            Notify("⛔ TeleScalper PRO stopped. Open positions are no longer managed.");

            try
            {
                if (_http != null)
                    _http.Dispose();
            }
            catch (Exception ex)
            {
                Print("TeleScalperPro: dispose error: {0}", ex.Message);
            }
        }

        private string DescribeSizing()
        {
            return Sizing == SizingMode.RiskPercent
                ? RiskPercent.ToString("0.##", CultureInfo.InvariantCulture) + "% risk"
                : FixedLots.ToString("0.###", CultureInfo.InvariantCulture) + " lots";
        }

        // ----------------------------------------------------------------- parameter parsing

        private void ParseChatIds()
        {
            foreach (var raw in SplitList(SignalChatIds))
            {
                long id;
                if (!long.TryParse(raw, NumberStyles.Integer, CultureInfo.InvariantCulture, out id))
                {
                    Print("TeleScalperPro: '{0}' is not a valid chat ID — skipped.", raw);
                    continue;
                }

                if (_signalChats.Count >= MaxSignalGroups)
                {
                    Print("TeleScalperPro: more than {0} signal chats configured — '{1}' ignored.", MaxSignalGroups, raw);
                    continue;
                }

                _signalChats.Add(id);
            }

            long admin;
            if (long.TryParse((NotifyChatId ?? string.Empty).Trim(), NumberStyles.Integer, CultureInfo.InvariantCulture, out admin))
                _adminChatId = admin;
        }

        private void ParseSymbolMap()
        {
            foreach (var pair in SplitList(SymbolMap))
            {
                var parts = pair.Split('=');
                if (parts.Length != 2)
                    continue;

                var from = Normalize(parts[0]);
                var to = parts[1].Trim();
                if (from.Length > 0 && to.Length > 0)
                    _userSymbolMap[from] = to;
            }
        }

        private void ParseWhitelist()
        {
            foreach (var item in SplitList(SymbolWhitelist))
            {
                var normalized = Normalize(item);
                if (normalized.Length > 0)
                    _whitelist.Add(normalized);
            }
        }

        private static IEnumerable<string> SplitList(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
                return Enumerable.Empty<string>();

            return value
                .Split(new[] { ',', ';', '\n', '\r', '|' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(x => x.Trim())
                .Where(x => x.Length > 0);
        }

        // ----------------------------------------------------------------- telegram

        private async Task PollLoopAsync(CancellationToken ct)
        {
            while (!ct.IsCancellationRequested)
            {
                try
                {
                    var url = string.Format(CultureInfo.InvariantCulture,
                        "{0}/getUpdates?timeout={1}&offset={2}&allowed_updates=%5B%22message%22%2C%22channel_post%22%5D",
                        _apiBase, PollSeconds, _updateOffset);

                    string body;
                    using (var response = await _http.GetAsync(url, ct).ConfigureAwait(false))
                    {
                        body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                        if (!response.IsSuccessStatusCode)
                        {
                            ReportPollError(string.Format("HTTP {0} from Telegram: {1}", (int)response.StatusCode, Trim(body, 200)));
                            await Task.Delay(TimeSpan.FromSeconds(5), ct).ConfigureAwait(false);
                            continue;
                        }
                    }

                    _lastPollError = null;
                    HandleUpdatesPayload(body);
                }
                catch (OperationCanceledException)
                {
                    return;
                }
                catch (Exception ex)
                {
                    ReportPollError(ex.Message);
                    try
                    {
                        await Task.Delay(TimeSpan.FromSeconds(5), ct).ConfigureAwait(false);
                    }
                    catch (OperationCanceledException)
                    {
                        return;
                    }
                }
            }
        }

        private void ReportPollError(string message)
        {
            if (_lastPollError == message)
                return;

            _lastPollError = message;
            BeginInvokeOnMainThread(() => Print("TeleScalperPro: Telegram poll error: {0}", message));
        }

        private void HandleUpdatesPayload(string json)
        {
            if (string.IsNullOrWhiteSpace(json))
                return;

            using (var doc = JsonDocument.Parse(json))
            {
                var root = doc.RootElement;

                JsonElement ok;
                if (root.TryGetProperty("ok", out ok) && ok.ValueKind == JsonValueKind.False)
                {
                    JsonElement description;
                    var reason = root.TryGetProperty("description", out description) ? description.GetString() : "unknown error";
                    ReportPollError("Telegram API said: " + reason);
                    return;
                }

                JsonElement result;
                if (!root.TryGetProperty("result", out result) || result.ValueKind != JsonValueKind.Array)
                    return;

                foreach (var update in result.EnumerateArray())
                {
                    JsonElement updateId;
                    if (update.TryGetProperty("update_id", out updateId) && updateId.ValueKind == JsonValueKind.Number)
                    {
                        var id = updateId.GetInt64();
                        if (id >= _updateOffset)
                            _updateOffset = id + 1;
                    }

                    JsonElement message;
                    if (!TryGetAny(update, out message, "message", "channel_post"))
                        continue;

                    JsonElement chat;
                    if (!message.TryGetProperty("chat", out chat))
                        continue;

                    JsonElement chatIdElement;
                    if (!chat.TryGetProperty("id", out chatIdElement) || chatIdElement.ValueKind != JsonValueKind.Number)
                        continue;

                    var text = GetStringProperty(message, "text") ?? GetStringProperty(message, "caption");
                    if (string.IsNullOrWhiteSpace(text))
                        continue;

                    var utc = DateTime.UtcNow;
                    JsonElement date;
                    if (message.TryGetProperty("date", out date) && date.ValueKind == JsonValueKind.Number)
                        utc = DateTimeOffset.FromUnixTimeSeconds(date.GetInt64()).UtcDateTime;

                    _incoming.Enqueue(new IncomingMessage
                    {
                        ChatId = chatIdElement.GetInt64(),
                        Text = text,
                        UtcTime = utc
                    });
                }
            }
        }

        private static bool TryGetAny(JsonElement parent, out JsonElement found, params string[] names)
        {
            found = default(JsonElement);

            for (var i = 0; i < names.Length; i++)
            {
                JsonElement candidate;
                if (parent.TryGetProperty(names[i], out candidate) && candidate.ValueKind == JsonValueKind.Object)
                {
                    found = candidate;
                    return true;
                }
            }

            return false;
        }

        private static string GetStringProperty(JsonElement parent, string name)
        {
            JsonElement element;
            if (parent.TryGetProperty(name, out element) && element.ValueKind == JsonValueKind.String)
                return element.GetString();

            return null;
        }

        private void SendTelegram(long chatId, string text)
        {
            if (_http == null || string.IsNullOrWhiteSpace(text))
                return;

            var payload = new Dictionary<string, string>
            {
                { "chat_id", chatId.ToString(CultureInfo.InvariantCulture) },
                { "text", text },
                { "disable_web_page_preview", "true" }
            };

            var task = _http.PostAsync(_apiBase + "/sendMessage", new FormUrlEncodedContent(payload));
            task.ContinueWith(t =>
            {
                if (t.Status == TaskStatus.RanToCompletion)
                {
                    if (t.Result != null)
                        t.Result.Dispose();
                }
                else if (t.Exception != null)
                {
                    ReportPollError("sendMessage failed: " + t.Exception.GetBaseException().Message);
                }
            });
        }

        private void Notify(string text)
        {
            if (_adminChatId.HasValue)
                SendTelegram(_adminChatId.Value, text);
        }

        // ----------------------------------------------------------------- message handling

        private void DrainIncoming()
        {
            IncomingMessage message;
            while (_incoming.TryDequeue(out message))
            {
                try
                {
                    HandleMessage(message);
                }
                catch (Exception ex)
                {
                    Print("TeleScalperPro: error handling message: {0}", ex.Message);
                }
            }
        }

        private void HandleMessage(IncomingMessage message)
        {
            var text = message.Text.Trim();

            var command = CommandRegex.Match(text);
            if (command.Success)
            {
                if (_adminChatId.HasValue && message.ChatId == _adminChatId.Value)
                    HandleCommand(command.Groups[1].Value.ToLowerInvariant(), command.Groups[2].Value.Trim());

                return;
            }

            if (!_signalChats.Contains(message.ChatId))
                return;

            if (MaxSignalAgeMinutes > 0 && (DateTime.UtcNow - message.UtcTime).TotalMinutes > MaxSignalAgeMinutes)
            {
                LogVerbose("Signal ignored (older than {0} minutes).", MaxSignalAgeMinutes);
                return;
            }

            string rejection;
            var signal = ParseSignal(text, message.ChatId, out rejection);
            if (signal == null)
            {
                _signalsRejected++;
                LogVerbose("Signal rejected: {0} | {1}", rejection, Trim(text.Replace('\n', ' '), 120));
                return;
            }

            _signalsAccepted++;
            _lastSignalUtc = DateTime.UtcNow;
            ExecuteSignal(signal);
        }

        private void HandleCommand(string command, string argument)
        {
            switch (command)
            {
                case "start":
                case "trading":
                    if (command == "trading" && argument.Length > 0)
                        _tradingEnabled = argument.Equals("on", StringComparison.OrdinalIgnoreCase) || argument.Equals("true", StringComparison.OrdinalIgnoreCase);
                    else
                        _tradingEnabled = true;

                    Notify(_tradingEnabled ? "▶ Auto trading ENABLED." : "⏸ Auto trading DISABLED (open trades still managed).");
                    break;

                case "stop":
                    _tradingEnabled = false;
                    Notify("⏸ Auto trading DISABLED. Open trades are still managed.");
                    break;

                case "unlock":
                    _dayLocked = false;
                    _dayStartBalance = Account.Balance;
                    Notify("🔓 Daily loss lock cleared, balance baseline reset to " + Account.Balance.ToString("0.00", CultureInfo.InvariantCulture));
                    break;

                case "status":
                    Notify(BuildStatusText());
                    break;

                case "positions":
                    Notify(BuildPositionsText());
                    break;

                case "closeall":
                    CloseAllBotPositions();
                    break;

                case "help":
                    Notify("Commands:\n/status — bot status\n/positions — open bot trades\n/start — enable auto trading\n/stop — disable auto trading\n/trading on|off — set auto trading\n/unlock — clear the daily loss lock\n/closeall — close all bot trades\n/help — this message");
                    break;

                default:
                    Notify("Unknown command /" + command + ". Send /help for the list.");
                    break;
            }
        }

        private string BuildStatusText()
        {
            var mine = Positions.FindAll(TradeLabel);
            var sb = new StringBuilder();
            sb.AppendLine("🔥 TeleScalper PRO status");
            sb.AppendLine("Account: " + Account.Number + " (" + (Account.IsLive ? "LIVE" : "DEMO") + ")");
            sb.AppendLine("Balance: " + Account.Balance.ToString("0.00", CultureInfo.InvariantCulture) + " " + Account.Asset.Name);
            sb.AppendLine("Equity: " + Account.Equity.ToString("0.00", CultureInfo.InvariantCulture));
            sb.AppendLine("Auto trading: " + (_tradingEnabled ? "ON" : "OFF") + (_dayLocked ? " (DAILY LOSS LOCK)" : string.Empty));
            sb.AppendLine("Day P/L: " + (Account.Equity - _dayStartBalance).ToString("0.00", CultureInfo.InvariantCulture));
            sb.AppendLine("Open bot trades: " + mine.Length + "/" + MaxOpenTrades + " in " + _groups.Count + " signal group(s)");
            sb.AppendLine("Size: " + DescribeSizing() + " over " + EntriesPerSignal + " entries");
            sb.AppendLine("Open risk: " + EstimateOpenRiskPercent().ToString("0.0", CultureInfo.InvariantCulture) + "%"
                + (MaxOpenRiskPercent > 0 ? " / " + MaxOpenRiskPercent.ToString("0.#", CultureInfo.InvariantCulture) + "%" : string.Empty));
            sb.AppendLine("Signals accepted/rejected: " + _signalsAccepted + "/" + _signalsRejected);
            sb.AppendLine("Trades opened: " + _tradesOpened);
            sb.AppendLine("Last signal: " + (_lastSignalUtc.HasValue ? _lastSignalUtc.Value.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture) + " UTC" : "none yet"));
            if (!string.IsNullOrEmpty(_lastPollError))
                sb.AppendLine("Last poll error: " + _lastPollError);

            return sb.ToString();
        }

        private string BuildPositionsText()
        {
            var mine = Positions.FindAll(TradeLabel);
            if (mine.Length == 0)
                return "No open bot trades.";

            var sb = new StringBuilder();
            sb.AppendLine("📄 Open bot trades (" + mine.Length + ")");
            foreach (var position in mine)
            {
                LegState leg;
                _legs.TryGetValue(position.Id, out leg);
                sb.AppendLine(string.Format(CultureInfo.InvariantCulture,
                    "#{0} {1} {2} {3} lots @ {4} | SL {5} | TP {6} | {7} pips | {8}{9}",
                    position.Id,
                    position.SymbolName,
                    position.TradeType,
                    position.Symbol.VolumeInUnitsToQuantity(position.VolumeInUnits).ToString("0.###", CultureInfo.InvariantCulture),
                    FormatPrice(position.Symbol, position.EntryPrice),
                    position.StopLoss.HasValue ? FormatPrice(position.Symbol, position.StopLoss.Value) : "-",
                    position.TakeProfit.HasValue ? FormatPrice(position.Symbol, position.TakeProfit.Value) : "-",
                    position.Pips.ToString("0.0", CultureInfo.InvariantCulture),
                    position.NetProfit.ToString("0.00", CultureInfo.InvariantCulture),
                    leg != null && leg.IsRunner ? " | runner" : string.Empty));
            }

            return sb.ToString();
        }

        private void CloseAllBotPositions()
        {
            var mine = Positions.FindAll(TradeLabel);
            var closed = 0;
            foreach (var position in mine)
            {
                var result = ClosePosition(position);
                if (result.IsSuccessful)
                    closed++;
                else
                    Print("TeleScalperPro: failed to close #{0}: {1}", position.Id, result.Error);
            }

            Notify("🛑 Closed " + closed + " of " + mine.Length + " bot trades on request.");
        }

        // ----------------------------------------------------------------- risk guards

        private void CheckDayRollover()
        {
            if (Server.Time.Date == _currentDay)
                return;

            _currentDay = Server.Time.Date;
            _dayStartBalance = Account.Balance;

            if (_dayLocked)
            {
                _dayLocked = false;
                Notify("🔓 New trading day — daily loss lock cleared. Baseline " + Account.Balance.ToString("0.00", CultureInfo.InvariantCulture));
            }
        }

        private bool DailyLossHit()
        {
            if (MaxDailyLossPercent <= 0 || _dayStartBalance <= 0)
                return false;

            var loss = _dayStartBalance - Account.Equity;
            return loss / _dayStartBalance * 100.0 >= MaxDailyLossPercent;
        }

        private double EstimateOpenRiskPercent()
        {
            if (Account.Balance <= 0)
                return 0;

            var risk = 0.0;
            foreach (var position in Positions.FindAll(TradeLabel))
            {
                if (!position.StopLoss.HasValue)
                    continue;

                var symbol = position.Symbol;
                var distance = Math.Abs(position.EntryPrice - position.StopLoss.Value) / symbol.PipSize;
                var stopIsProfitable = position.TradeType == TradeType.Buy
                    ? position.StopLoss.Value > position.EntryPrice
                    : position.StopLoss.Value < position.EntryPrice;

                if (stopIsProfitable)
                    continue;

                risk += distance * symbol.PipValue * position.VolumeInUnits;
            }

            return risk / Account.Balance * 100.0;
        }

        // ----------------------------------------------------------------- signal parsing

        private ParsedSignal ParseSignal(string text, long chatId, out string rejection)
        {
            rejection = null;

            var directionMatch = DirectionRegex.Match(text);
            if (!directionMatch.Success)
            {
                rejection = "no BUY/SELL direction";
                return null;
            }

            var directionWord = directionMatch.Groups[1].Value.ToUpperInvariant();
            var direction = (directionWord == "BUY" || directionWord == "LONG") ? TradeType.Buy : TradeType.Sell;

            var takeProfits = ExtractTakeProfits(text);
            if (takeProfits.Count == 0)
            {
                rejection = "no take profit";
                return null;
            }

            var brokerSymbol = FindSymbolInText(text);
            if (brokerSymbol == null)
            {
                rejection = "symbol not found on this account";
                return null;
            }

            if (_whitelist.Count > 0 && !_whitelist.Contains(Normalize(brokerSymbol)))
            {
                rejection = brokerSymbol + " not in whitelist";
                return null;
            }

            var symbol = Symbols.GetSymbol(brokerSymbol);
            var marketPrice = direction == TradeType.Buy ? symbol.Ask : symbol.Bid;

            double? entry = null;
            var entryMatch = EntryRegex.Match(text);
            if (entryMatch.Success)
            {
                double parsedEntry;
                if (TryParsePrice(entryMatch.Groups[1].Value, out parsedEntry))
                    entry = parsedEntry;
            }

            if (entry.HasValue && marketPrice > 0 && Math.Abs(entry.Value - marketPrice) / marketPrice > 0.2)
                entry = null;

            var reference = entry ?? marketPrice;

            double stopLoss;
            var stopLossMatch = StopLossRegex.Match(text);
            if (stopLossMatch.Success && TryParsePrice(stopLossMatch.Groups[1].Value, out stopLoss))
            {
                // signal carries its own stop
            }
            else if (FallbackStopLossPips > 0)
            {
                stopLoss = direction == TradeType.Buy
                    ? reference - FallbackStopLossPips * symbol.PipSize
                    : reference + FallbackStopLossPips * symbol.PipSize;

                LogVerbose("{0}: signal had no stop loss — using the {1} pip fallback.", brokerSymbol, FallbackStopLossPips);
            }
            else
            {
                rejection = "no stop loss";
                return null;
            }

            if (direction == TradeType.Buy && !(stopLoss < reference && takeProfits[0] > reference))
            {
                rejection = "BUY levels inconsistent (SL must be below, TP above entry)";
                return null;
            }

            if (direction == TradeType.Sell && !(stopLoss > reference && takeProfits[0] < reference))
            {
                rejection = "SELL levels inconsistent (SL must be above, TP below entry)";
                return null;
            }

            // Keep only targets that sit beyond the entry in the trade direction, in order.
            var ordered = new List<double>();
            foreach (var tp in takeProfits)
            {
                var beyondEntry = direction == TradeType.Buy ? tp > reference : tp < reference;
                var beyondPrevious = ordered.Count == 0 || (direction == TradeType.Buy ? tp > ordered[ordered.Count - 1] : tp < ordered[ordered.Count - 1]);
                if (beyondEntry && beyondPrevious)
                    ordered.Add(tp);
            }

            if (ordered.Count == 0)
            {
                rejection = "no usable take profit";
                return null;
            }

            var signal = new ParsedSignal
            {
                BrokerSymbol = brokerSymbol,
                Direction = direction,
                Entry = entry,
                StopLoss = stopLoss,
                Targets = ordered,
                ChatId = chatId
            };

            signal.Fingerprint = BuildFingerprint(signal);
            return signal;
        }

        private List<double> ExtractTakeProfits(string text)
        {
            var indexed = new List<KeyValuePair<int, double>>();
            var order = 0;

            foreach (Match match in TakeProfitRegex.Matches(text))
            {
                double value;
                if (!TryParsePrice(match.Groups[2].Value, out value))
                    continue;

                var rank = ++order;
                int explicitIndex;
                if (match.Groups[1].Success && int.TryParse(match.Groups[1].Value, NumberStyles.Integer, CultureInfo.InvariantCulture, out explicitIndex) && explicitIndex > 0)
                    rank = explicitIndex;

                indexed.Add(new KeyValuePair<int, double>(rank, value));
            }

            return indexed
                .OrderBy(x => x.Key)
                .Select(x => x.Value)
                .Distinct()
                .ToList();
        }

        private static bool TryParsePrice(string raw, out double value)
        {
            value = 0;
            if (string.IsNullOrWhiteSpace(raw))
                return false;

            var text = raw.Trim();
            var hasDot = text.IndexOf('.') >= 0;
            var hasComma = text.IndexOf(',') >= 0;

            if (hasDot && hasComma)
            {
                text = text.Replace(",", string.Empty);
            }
            else if (hasComma)
            {
                var parts = text.Split(',');
                var last = parts[parts.Length - 1];
                text = (parts.Length == 2 && last.Length != 3)
                    ? text.Replace(',', '.')
                    : text.Replace(",", string.Empty);
            }

            return double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out value) && value > 0;
        }

        private string BuildFingerprint(ParsedSignal signal)
        {
            var raw = string.Format(CultureInfo.InvariantCulture, "{0}|{1}|{2}|{3}|{4}",
                signal.BrokerSymbol,
                signal.Direction,
                signal.Entry.HasValue ? signal.Entry.Value.ToString("0.#####", CultureInfo.InvariantCulture) : "mkt",
                signal.StopLoss.ToString("0.#####", CultureInfo.InvariantCulture),
                signal.Targets[0].ToString("0.#####", CultureInfo.InvariantCulture));

            unchecked
            {
                var hash = 23U;
                foreach (var c in raw)
                    hash = hash * 31U + c;

                return hash.ToString("x8", CultureInfo.InvariantCulture);
            }
        }

        // ----------------------------------------------------------------- symbol resolution

        private string FindSymbolInText(string text)
        {
            foreach (Match match in SymbolTokenRegex.Matches(text))
            {
                var normalized = Normalize(match.Groups[1].Value);
                if (normalized.Length < 2 || normalized.Length > 16)
                    continue;

                if (IsNoiseWord(normalized) || IsNoiseWord(StripTrailingDigits(normalized)))
                    continue;

                var resolved = ResolveSymbol(normalized);
                if (resolved != null)
                    return resolved;
            }

            return null;
        }

        private static string StripTrailingDigits(string value)
        {
            var end = value.Length;
            while (end > 0 && char.IsDigit(value[end - 1]))
                end--;

            return value.Substring(0, end);
        }

        private static bool IsNoiseWord(string normalized)
        {
            switch (normalized)
            {
                case "BUY":
                case "SELL":
                case "LONG":
                case "SHORT":
                case "SL":
                case "TP":
                case "TP1":
                case "TP2":
                case "TP3":
                case "ENTRY":
                case "NOW":
                case "RISK":
                case "TIME":
                case "SIGNAL":
                case "VIP":
                case "LOT":
                case "LOTS":
                case "PIPS":
                case "PIP":
                case "PRICE":
                case "OPEN":
                case "CLOSE":
                case "TARGET":
                case "LIMIT":
                case "MARKET":
                case "ZONE":
                case "STOP":
                case "LOSS":
                case "PROFIT":
                case "TAKE":
                    return true;
                default:
                    return false;
            }
        }

        private string ResolveSymbol(string normalizedToken)
        {
            string cached;
            if (_symbolResolveCache.TryGetValue(normalizedToken, out cached))
                return cached;

            var resolved = ResolveSymbolCore(normalizedToken);
            _symbolResolveCache[normalizedToken] = resolved;
            return resolved;
        }

        private string ResolveSymbolCore(string normalizedToken)
        {
            string mapped;
            if (_userSymbolMap.TryGetValue(normalizedToken, out mapped))
                return Symbols.Exists(mapped) ? mapped : null;

            var candidates = new List<string>();
            AddSymbolCandidates(candidates, normalizedToken);

            string alias;
            if (SymbolAliases.TryGetValue(normalizedToken, out alias))
                AddSymbolCandidates(candidates, alias);

            foreach (var candidate in candidates)
            {
                if (Symbols.Exists(candidate))
                    return candidate;
            }

            return null;
        }

        private void AddSymbolCandidates(List<string> candidates, string baseName)
        {
            var suffix = (SymbolSuffix ?? string.Empty).Trim();
            if (suffix.Length > 0)
            {
                candidates.Add(baseName + suffix);
                candidates.Add(baseName.ToLowerInvariant() + suffix);
            }

            foreach (var common in CommonSuffixes)
                candidates.Add(baseName + common);

            if (baseName.Length == 6)
                candidates.Add(baseName.Substring(0, 3) + "/" + baseName.Substring(3, 3));
        }

        private static string Normalize(string value)
        {
            if (string.IsNullOrEmpty(value))
                return string.Empty;

            var sb = new StringBuilder(value.Length);
            foreach (var c in value)
            {
                if (char.IsLetterOrDigit(c))
                    sb.Append(char.ToUpperInvariant(c));
            }

            return sb.ToString();
        }

        // ----------------------------------------------------------------- execution

        private void ExecuteSignal(ParsedSignal signal)
        {
            if (_seenFingerprints.Contains(signal.Fingerprint))
            {
                LogVerbose("Duplicate signal {0} for {1} ignored.", signal.Fingerprint, signal.BrokerSymbol);
                return;
            }

            if (!_tradingEnabled)
            {
                Notify("⏸ Signal received but auto trading is OFF:\n" + DescribeSignal(signal));
                return;
            }

            if (_dayLocked || DailyLossHit())
            {
                if (!_dayLocked)
                {
                    _dayLocked = true;
                    Notify("🔒 Daily loss limit hit — no new trades today. Send /unlock to override.");
                }

                return;
            }

            var mine = Positions.FindAll(TradeLabel);
            if (mine.Length >= MaxOpenTrades)
            {
                Notify("⚠ Max open trades (" + MaxOpenTrades + ") reached — signal skipped.");
                return;
            }

            if (MaxOpenRiskPercent > 0 && EstimateOpenRiskPercent() >= MaxOpenRiskPercent)
            {
                Notify("⚠ Open risk already at " + EstimateOpenRiskPercent().ToString("0.0", CultureInfo.InvariantCulture) + "% — signal skipped.");
                return;
            }

            var symbol = Symbols.GetSymbol(signal.BrokerSymbol);

            if (!symbol.MarketHours.IsOpened())
            {
                Notify("⚠ Market closed for " + symbol.Name + " — signal skipped.");
                return;
            }

            if (MaxSpreadPips > 0 && symbol.Spread / symbol.PipSize > MaxSpreadPips)
            {
                Notify("⚠ Spread too wide on " + symbol.Name + " — signal skipped.");
                return;
            }

            var marketPrice = signal.Direction == TradeType.Buy ? symbol.Ask : symbol.Bid;
            var slOnCorrectSide = signal.Direction == TradeType.Buy ? signal.StopLoss < marketPrice : signal.StopLoss > marketPrice;
            var firstTargetOnCorrectSide = signal.Direction == TradeType.Buy ? signal.Targets[0] > marketPrice : signal.Targets[0] < marketPrice;
            if (!slOnCorrectSide || !firstTargetOnCorrectSide)
            {
                Notify("⚠ " + symbol.Name + ": current price is already past SL or the first target — signal skipped.");
                return;
            }

            var riskDistance = Math.Abs(marketPrice - signal.StopLoss);
            if (riskDistance <= 0)
                return;

            var perSymbol = mine.Count(p => string.Equals(p.SymbolName, signal.BrokerSymbol, StringComparison.OrdinalIgnoreCase));
            var roomBySymbol = Math.Max(0, MaxTradesPerSymbol - perSymbol);
            var roomTotal = Math.Max(0, MaxOpenTrades - mine.Length);
            var legs = Math.Min(EntriesPerSignal, Math.Min(roomBySymbol, roomTotal));
            if (legs <= 0)
            {
                Notify("⚠ No room left for " + symbol.Name + " (per-symbol cap " + MaxTradesPerSymbol + ") — signal skipped.");
                return;
            }

            var totalVolume = CalculateTotalVolume(symbol, riskDistance);
            if (totalVolume <= 0)
            {
                Notify("⚠ " + symbol.Name + ": calculated volume is below the minimum — signal skipped.");
                return;
            }

            double perLeg;
            while (true)
            {
                perLeg = symbol.NormalizeVolumeInUnits(totalVolume / legs, RoundingMode.Down);
                if (perLeg >= symbol.VolumeInUnitsMin || legs == 1)
                    break;

                legs--;
            }

            if (perLeg < symbol.VolumeInUnitsMin)
                perLeg = symbol.VolumeInUnitsMin;

            var targets = BuildTargetLadder(signal, marketPrice, riskDistance, legs);

            var group = new GroupState
            {
                Fingerprint = signal.Fingerprint,
                SymbolName = symbol.Name,
                Direction = signal.Direction,
                RiskDistance = riskDistance,
                InitialStopLoss = signal.StopLoss,
                FurthestTarget = targets[targets.Count - 1],
                BaseVolume = perLeg,
                OpenLegs = 0
            };

            _seenFingerprints.Add(signal.Fingerprint);
            _groups[signal.Fingerprint] = group;

            var opened = 0;
            for (var i = 0; i < legs; i++)
            {
                var isRunner = i == legs - 1;
                if (OpenLeg(symbol, signal.Direction, perLeg, signal.StopLoss, targets[i], group, isRunner))
                    opened++;
            }

            if (opened == 0)
            {
                _groups.Remove(signal.Fingerprint);
                return;
            }

            Notify(string.Format(CultureInfo.InvariantCulture,
                "🟩 {0} {1} — {2} entries opened\nSize: {3} lots each\nSL: {4}\nTargets: {5}\nRisk: {6}",
                symbol.Name,
                signal.Direction.ToString().ToUpperInvariant(),
                opened,
                symbol.VolumeInUnitsToQuantity(perLeg).ToString("0.###", CultureInfo.InvariantCulture),
                FormatPrice(symbol, signal.StopLoss),
                string.Join(" / ", targets.Take(opened).Select(t => FormatPrice(symbol, t))),
                DescribeSizing()));
        }

        private List<double> BuildTargetLadder(ParsedSignal signal, double marketPrice, double riskDistance, int legs)
        {
            var targets = new List<double>(signal.Targets);
            var step = riskDistance * ExtraTargetStepR;

            while (targets.Count < legs)
            {
                var last = targets[targets.Count - 1];
                targets.Add(signal.Direction == TradeType.Buy ? last + step : last - step);
            }

            // The runner always aims at the furthest target in the list.
            if (targets.Count > legs)
            {
                var furthest = targets[targets.Count - 1];
                targets = targets.Take(legs).ToList();
                targets[legs - 1] = furthest;
            }

            return targets;
        }

        private bool OpenLeg(Symbol symbol, TradeType direction, double volume, double stopLoss, double target, GroupState group, bool isRunner)
        {
            var comment = Trim(string.Format(CultureInfo.InvariantCulture, "TSP|{0}|{1}|{2}",
                group.Fingerprint,
                target.ToString("0.#####", CultureInfo.InvariantCulture),
                isRunner ? "R" : "L"), 60);

            var result = ExecuteMarketOrder(direction, symbol.Name, volume, TradeLabel, (double?)null, (double?)null, comment);
            if (!result.IsSuccessful || result.Position == null)
            {
                Print("TeleScalperPro: order rejected on {0}: {1}", symbol.Name, result.Error);
                Notify("❌ Order rejected on " + symbol.Name + ": " + result.Error);
                return false;
            }

            var position = result.Position;
            _tradesOpened++;
            group.OpenLegs++;

            var protection = ModifyPosition(position, RoundPrice(symbol, stopLoss), RoundPrice(symbol, target), ProtectionType.Absolute);
            if (!protection.IsSuccessful)
            {
                Print("TeleScalperPro: could not attach SL/TP to #{0}: {1}", position.Id, protection.Error);
                Notify("⚠ Trade #" + position.Id + " opened but SL/TP could not be set: " + protection.Error);
            }

            _legs[position.Id] = new LegState
            {
                Fingerprint = group.Fingerprint,
                Target = target,
                RiskDistance = group.RiskDistance,
                EntryPrice = position.EntryPrice,
                IsRunner = isRunner,
                BreakEvenDone = false
            };

            return true;
        }

        private double CalculateTotalVolume(Symbol symbol, double riskDistance)
        {
            double volume;

            if (Sizing == SizingMode.RiskPercent)
            {
                var stopLossPips = riskDistance / symbol.PipSize;
                if (stopLossPips <= 0)
                    return 0;

                var riskAmount = Account.Balance * RiskPercent / 100.0;
                volume = symbol.VolumeForFixedRisk(riskAmount, stopLossPips, RoundingMode.Down);
            }
            else
            {
                volume = symbol.QuantityToVolumeInUnits(FixedLots);
            }

            volume = symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);

            if (volume < symbol.VolumeInUnitsMin)
                return 0;

            if (volume > symbol.VolumeInUnitsMax)
                volume = symbol.VolumeInUnitsMax;

            return volume;
        }

        // ----------------------------------------------------------------- management

        private void ManageOpenPositions()
        {
            var mine = Positions.FindAll(TradeLabel);
            if (mine.Length == 0)
                return;

            foreach (var position in mine)
            {
                LegState leg;
                if (!_legs.TryGetValue(position.Id, out leg))
                {
                    leg = RestoreLeg(position);
                    if (leg == null)
                        continue;

                    _legs[position.Id] = leg;
                }

                try
                {
                    ManageLeg(position, leg);
                }
                catch (Exception ex)
                {
                    Print("TeleScalperPro: manage error on #{0}: {1}", position.Id, ex.Message);
                }
            }

            TryPyramid(mine);
        }

        private void ManageLeg(Position position, LegState leg)
        {
            var symbol = position.Symbol;
            var price = position.TradeType == TradeType.Buy ? symbol.Bid : symbol.Ask;
            var progress = position.TradeType == TradeType.Buy
                ? price - position.EntryPrice
                : position.EntryPrice - price;

            GroupState group;
            _groups.TryGetValue(leg.Fingerprint, out group);

            var groupBankedProfit = group != null && group.FirstTargetBanked;

            if (!leg.BreakEvenDone && BreakEvenAfterFirstTarget && groupBankedProfit)
                MoveToBreakEven(position, leg);

            if (TrailStartR <= 0 || leg.RiskDistance <= 0)
                return;

            if (progress < leg.RiskDistance * TrailStartR)
                return;

            var trailDistance = leg.RiskDistance * TrailDistanceR;
            var newStop = position.TradeType == TradeType.Buy
                ? RoundPrice(symbol, price - trailDistance)
                : RoundPrice(symbol, price + trailDistance);

            var improves = !position.StopLoss.HasValue || (position.TradeType == TradeType.Buy
                ? newStop > position.StopLoss.Value + symbol.TickSize / 2.0
                : newStop < position.StopLoss.Value - symbol.TickSize / 2.0);

            if (!improves)
                return;

            var wouldTriggerNow = position.TradeType == TradeType.Buy ? newStop >= price : newStop <= price;
            if (wouldTriggerNow)
                return;

            var result = ModifyPosition(position, newStop, position.TakeProfit, ProtectionType.Absolute);
            if (result.IsSuccessful)
            {
                leg.BreakEvenDone = true;
                LogVerbose("#{0} trailing stop moved to {1}", position.Id, newStop);
            }
            else
            {
                Print("TeleScalperPro: trailing stop failed on #{0}: {1}", position.Id, result.Error);
            }
        }

        private bool MoveToBreakEven(Position position, LegState leg)
        {
            var symbol = position.Symbol;
            var buffer = BreakEvenBufferPips * symbol.PipSize;
            var target = position.TradeType == TradeType.Buy
                ? RoundPrice(symbol, position.EntryPrice + buffer)
                : RoundPrice(symbol, position.EntryPrice - buffer);

            var currentPrice = position.TradeType == TradeType.Buy ? symbol.Bid : symbol.Ask;
            var wouldTriggerNow = position.TradeType == TradeType.Buy ? target >= currentPrice : target <= currentPrice;
            if (wouldTriggerNow)
                return false;

            if (position.StopLoss.HasValue)
            {
                var alreadyBetter = position.TradeType == TradeType.Buy
                    ? position.StopLoss.Value >= target - symbol.TickSize / 2.0
                    : position.StopLoss.Value <= target + symbol.TickSize / 2.0;

                if (alreadyBetter)
                {
                    leg.BreakEvenDone = true;
                    return false;
                }
            }

            var result = ModifyPosition(position, target, position.TakeProfit, ProtectionType.Absolute);
            if (!result.IsSuccessful)
            {
                Print("TeleScalperPro: break even failed on #{0}: {1}", position.Id, result.Error);
                return false;
            }

            leg.BreakEvenDone = true;
            Print("TeleScalperPro: #{0} SL moved to break even at {1}", position.Id, target);
            return true;
        }

        private void TryPyramid(Position[] mine)
        {
            if (MaxPyramidAdds <= 0 || !_tradingEnabled || _dayLocked)
                return;

            if (mine.Length >= MaxOpenTrades)
                return;

            foreach (var group in _groups.Values.ToList())
            {
                if (group.PyramidAdds >= MaxPyramidAdds || group.OpenLegs <= 0)
                    continue;

                if (MaxOpenRiskPercent > 0 && EstimateOpenRiskPercent() >= MaxOpenRiskPercent)
                    return;

                var legs = mine.Where(p =>
                {
                    LegState state;
                    return _legs.TryGetValue(p.Id, out state) && state.Fingerprint == group.Fingerprint;
                }).ToArray();

                if (legs.Length == 0)
                    continue;

                if (legs.Count(p => string.Equals(p.SymbolName, group.SymbolName, StringComparison.OrdinalIgnoreCase)) >= MaxTradesPerSymbol)
                    continue;

                var symbol = Symbols.GetSymbol(group.SymbolName);
                var price = group.Direction == TradeType.Buy ? symbol.Bid : symbol.Ask;
                var reference = legs[0].EntryPrice;
                var progress = group.Direction == TradeType.Buy ? price - reference : reference - price;

                if (group.RiskDistance <= 0 || progress < group.RiskDistance * PyramidTriggerR)
                    continue;

                var volume = symbol.NormalizeVolumeInUnits(group.BaseVolume * PyramidSizeFactor, RoundingMode.Down);
                if (volume < symbol.VolumeInUnitsMin)
                    volume = symbol.VolumeInUnitsMin;

                // The add is protected at the group's break-even level, never at the original stop.
                var stop = group.Direction == TradeType.Buy
                    ? reference + BreakEvenBufferPips * symbol.PipSize
                    : reference - BreakEvenBufferPips * symbol.PipSize;

                var stopIsSane = group.Direction == TradeType.Buy ? stop < price : stop > price;
                if (!stopIsSane)
                    continue;

                group.PyramidAdds++;

                if (OpenLeg(symbol, group.Direction, volume, stop, group.FurthestTarget, group, false))
                {
                    Notify(string.Format(CultureInfo.InvariantCulture,
                        "📈 Pyramid add #{0} on {1} {2}\nSize: {3} lots\nSL: {4} (group break even)\nTarget: {5}",
                        group.PyramidAdds,
                        symbol.Name,
                        group.Direction.ToString().ToUpperInvariant(),
                        symbol.VolumeInUnitsToQuantity(volume).ToString("0.###", CultureInfo.InvariantCulture),
                        FormatPrice(symbol, stop),
                        FormatPrice(symbol, group.FurthestTarget)));
                }
            }
        }

        private LegState RestoreLeg(Position position)
        {
            var comment = position.Comment ?? string.Empty;
            if (!comment.StartsWith("TSP|", StringComparison.OrdinalIgnoreCase))
                return null;

            var parts = comment.Split('|');
            if (parts.Length < 3)
                return null;

            double target;
            if (!double.TryParse(parts[2], NumberStyles.Float, CultureInfo.InvariantCulture, out target))
                return null;

            var fingerprint = parts[1];
            var isRunner = parts.Length > 3 && parts[3] == "R";

            GroupState group;
            if (!_groups.TryGetValue(fingerprint, out group))
            {
                var riskDistance = position.StopLoss.HasValue
                    ? Math.Abs(position.EntryPrice - position.StopLoss.Value)
                    : Math.Abs(target - position.EntryPrice) / 2.0;

                group = new GroupState
                {
                    Fingerprint = fingerprint,
                    SymbolName = position.SymbolName,
                    Direction = position.TradeType,
                    RiskDistance = riskDistance,
                    InitialStopLoss = position.StopLoss ?? position.EntryPrice,
                    FurthestTarget = target,
                    BaseVolume = position.VolumeInUnits,
                    PyramidAdds = MaxPyramidAdds, // never pyramid onto an adopted group
                    OpenLegs = 0
                };

                _groups[fingerprint] = group;
                _seenFingerprints.Add(fingerprint);
            }

            group.OpenLegs++;

            var stopAtBreakEven = position.StopLoss.HasValue && (position.TradeType == TradeType.Buy
                ? position.StopLoss.Value >= position.EntryPrice
                : position.StopLoss.Value <= position.EntryPrice);

            LogVerbose("Adopted existing position #{0} ({1}) target {2}", position.Id, position.SymbolName, target);

            return new LegState
            {
                Fingerprint = fingerprint,
                Target = target,
                RiskDistance = group.RiskDistance,
                EntryPrice = position.EntryPrice,
                IsRunner = isRunner,
                BreakEvenDone = stopAtBreakEven
            };
        }

        private void RestoreStateFromOpenPositions()
        {
            foreach (var position in Positions.FindAll(TradeLabel))
            {
                var leg = RestoreLeg(position);
                if (leg != null)
                    _legs[position.Id] = leg;
            }

            if (_legs.Count > 0)
                Print("TeleScalperPro: adopted {0} existing position(s) in {1} group(s).", _legs.Count, _groups.Count);
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var position = args.Position;
            if (!string.Equals(position.Label, TradeLabel, StringComparison.Ordinal))
                return;

            if (Positions.FindById(position.Id) != null)
                return;

            LegState leg;
            if (!_legs.TryGetValue(position.Id, out leg))
                return;

            _legs.Remove(position.Id);

            GroupState group;
            _groups.TryGetValue(leg.Fingerprint, out group);

            if (group != null)
            {
                group.OpenLegs--;
                group.RealisedNet += position.NetProfit;

                if (position.NetProfit > 0)
                    group.FirstTargetBanked = true;
            }

            Notify(string.Format(CultureInfo.InvariantCulture,
                "🏁 Trade closed\n{0} #{1}{2}\nReason: {3}\nPips: {4:0.0}\nNet: {5:0.00} {6}",
                position.SymbolName,
                position.Id,
                leg.IsRunner ? " (runner)" : string.Empty,
                args.Reason,
                position.Pips,
                position.NetProfit,
                Account.Asset.Name));

            if (group != null && group.OpenLegs <= 0)
                OnGroupClosed(group);

            if (DailyLossHit() && !_dayLocked)
            {
                _dayLocked = true;
                Notify("🔒 Daily loss limit hit — no new trades today. Send /unlock to override.");
            }
        }

        private void OnGroupClosed(GroupState group)
        {
            _groups.Remove(group.Fingerprint);

            Notify(string.Format(CultureInfo.InvariantCulture, "📊 Signal finished on {0}: net {1:0.00} {2}",
                group.SymbolName, group.RealisedNet, Account.Asset.Name));

            if (group.RealisedNet >= 0 || MaxRecoverySteps <= 0)
                return;

            if (group.RecoveryStep >= MaxRecoverySteps || !_tradingEnabled || _dayLocked)
                return;

            var symbol = Symbols.GetSymbol(group.SymbolName);
            if (!symbol.MarketHours.IsOpened())
                return;

            var price = group.Direction == TradeType.Buy ? symbol.Ask : symbol.Bid;
            var volume = symbol.NormalizeVolumeInUnits(group.BaseVolume * RecoveryMultiplier, RoundingMode.Down);
            if (volume < symbol.VolumeInUnitsMin)
                volume = symbol.VolumeInUnitsMin;

            var stop = group.Direction == TradeType.Buy ? price - group.RiskDistance : price + group.RiskDistance;
            var target = group.Direction == TradeType.Buy
                ? price + group.RiskDistance * ExtraTargetStepR
                : price - group.RiskDistance * ExtraTargetStepR;

            var recovery = new GroupState
            {
                Fingerprint = group.Fingerprint + "r" + (group.RecoveryStep + 1),
                SymbolName = group.SymbolName,
                Direction = group.Direction,
                RiskDistance = group.RiskDistance,
                InitialStopLoss = stop,
                FurthestTarget = target,
                BaseVolume = volume,
                RecoveryStep = group.RecoveryStep + 1,
                PyramidAdds = MaxPyramidAdds // recovery trades are never pyramided
            };

            _groups[recovery.Fingerprint] = recovery;

            if (OpenLeg(symbol, group.Direction, volume, stop, target, recovery, true))
            {
                Notify(string.Format(CultureInfo.InvariantCulture,
                    "♻ Recovery entry {0}/{1} on {2} {3}\nSize: {4} lots\nSL: {5}\nTarget: {6}",
                    recovery.RecoveryStep, MaxRecoverySteps,
                    symbol.Name, group.Direction.ToString().ToUpperInvariant(),
                    symbol.VolumeInUnitsToQuantity(volume).ToString("0.###", CultureInfo.InvariantCulture),
                    FormatPrice(symbol, stop),
                    FormatPrice(symbol, target)));
            }
            else
            {
                _groups.Remove(recovery.Fingerprint);
            }
        }

        // ----------------------------------------------------------------- helpers

        private static double RoundPrice(Symbol symbol, double price)
        {
            return Math.Round(price, symbol.Digits);
        }

        private static string FormatPrice(Symbol symbol, double price)
        {
            return price.ToString("F" + symbol.Digits.ToString(CultureInfo.InvariantCulture), CultureInfo.InvariantCulture);
        }

        private string DescribeSignal(ParsedSignal signal)
        {
            var symbol = Symbols.GetSymbol(signal.BrokerSymbol);
            return string.Format(CultureInfo.InvariantCulture, "{0} {1}\nEntry: {2}\nSL: {3}\nTargets: {4}",
                signal.BrokerSymbol,
                signal.Direction.ToString().ToUpperInvariant(),
                signal.Entry.HasValue ? FormatPrice(symbol, signal.Entry.Value) : "market",
                FormatPrice(symbol, signal.StopLoss),
                string.Join(" / ", signal.Targets.Select(t => FormatPrice(symbol, t))));
        }

        private static string Trim(string value, int maxLength)
        {
            if (string.IsNullOrEmpty(value) || value.Length <= maxLength)
                return value;

            return value.Substring(0, maxLength);
        }

        private void LogVerbose(string format, params object[] args)
        {
            if (VerboseLogging)
                Print("TeleScalperPro: " + string.Format(CultureInfo.InvariantCulture, format, args));
        }
    }
}
