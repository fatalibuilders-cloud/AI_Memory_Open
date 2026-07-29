// TeleScalper — cTrader Automate cBot
//
// Reads trading signals from Telegram groups/channels, validates them, executes them
// on the connected cTrader account and manages them automatically:
//   - only signals that contain Symbol + Direction + SL + at least one TP are traded
//   - fixed lot size (default 0.01) or optional % risk sizing
//   - hard cap on simultaneously open trades (default 10)
//   - no duplicate trades from the same signal
//   - stop loss moved to break even once a configurable profit is reached
//   - partial close (default 50%) when TP1 is hit, remainder runs to TP2 with SL at break even
//   - Telegram notifications for every trade action, plus admin commands (/status, /positions, ...)
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
    public enum PartialFallbackMode
    {
        LetRunToTp2,
        CloseFullAtTp1
    }

    [Robot(AccessRights = AccessRights.FullAccess, AddIndicators = false, TimeZone = TimeZones.UTC)]
    public class TeleScalper : Robot
    {
        // ----------------------------------------------------------------- parameters

        [Parameter("Bot token", Group = "Telegram", DefaultValue = "")]
        public string BotToken { get; set; }

        [Parameter("Signal chat IDs (comma separated, max 5)", Group = "Telegram", DefaultValue = "")]
        public string SignalChatIds { get; set; }

        [Parameter("Admin / notify chat ID", Group = "Telegram", DefaultValue = "")]
        public string NotifyChatId { get; set; }

        [Parameter("Poll interval (seconds)", Group = "Telegram", DefaultValue = 3, MinValue = 1, MaxValue = 60)]
        public int PollSeconds { get; set; }

        [Parameter("Ignore signals older than (minutes, 0 = off)", Group = "Telegram", DefaultValue = 10, MinValue = 0, MaxValue = 1440)]
        public int MaxSignalAgeMinutes { get; set; }

        [Parameter("Enable trading", Group = "Trading", DefaultValue = true)]
        public bool EnableTrading { get; set; }

        [Parameter("Lot size", Group = "Trading", DefaultValue = 0.01, MinValue = 0.001, Step = 0.01)]
        public double LotSize { get; set; }

        [Parameter("Size by risk % instead of fixed lots", Group = "Trading", DefaultValue = false)]
        public bool UseRiskPercent { get; set; }

        [Parameter("Risk % of balance per trade", Group = "Trading", DefaultValue = 1.0, MinValue = 0.01, MaxValue = 20, Step = 0.1)]
        public double RiskPercent { get; set; }

        [Parameter("Max open trades", Group = "Trading", DefaultValue = 10, MinValue = 1, MaxValue = 100)]
        public int MaxOpenTrades { get; set; }

        [Parameter("Max open trades per symbol", Group = "Trading", DefaultValue = 3, MinValue = 1, MaxValue = 50)]
        public int MaxTradesPerSymbol { get; set; }

        [Parameter("Max spread (pips, 0 = off)", Group = "Trading", DefaultValue = 0, MinValue = 0)]
        public double MaxSpreadPips { get; set; }

        [Parameter("Max entry deviation (pips, 0 = off)", Group = "Trading", DefaultValue = 0, MinValue = 0)]
        public double MaxEntryDeviationPips { get; set; }

        [Parameter("Symbol whitelist (empty = all)", Group = "Trading", DefaultValue = "")]
        public string SymbolWhitelist { get; set; }

        [Parameter("Broker symbol suffix", Group = "Trading", DefaultValue = "")]
        public string SymbolSuffix { get; set; }

        [Parameter("Extra symbol map (SIGNAL=BROKER, comma separated)", Group = "Trading", DefaultValue = "")]
        public string SymbolMap { get; set; }

        [Parameter("Trade label", Group = "Trading", DefaultValue = "TeleScalper")]
        public string TradeLabel { get; set; }

        [Parameter("Close % at TP1", Group = "Management", DefaultValue = 50, MinValue = 0, MaxValue = 100)]
        public double PartialClosePercent { get; set; }

        [Parameter("If partial close impossible", Group = "Management", DefaultValue = PartialFallbackMode.LetRunToTp2)]
        public PartialFallbackMode PartialFallback { get; set; }

        [Parameter("Move SL to break even at TP1", Group = "Management", DefaultValue = true)]
        public bool BreakEvenAtTp1 { get; set; }

        [Parameter("Break even trigger (pips, 0 = off)", Group = "Management", DefaultValue = 0, MinValue = 0)]
        public double BreakEvenTriggerPips { get; set; }

        [Parameter("Break even buffer (pips)", Group = "Management", DefaultValue = 0.5, MinValue = 0, Step = 0.1)]
        public double BreakEvenBufferPips { get; set; }

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
            public double Tp1;
            public double? Tp2;
            public string Fingerprint;
            public long ChatId;
        }

        private sealed class TradeState
        {
            public double Tp1;
            public double? Tp2;
            public bool PartialDone;
            public bool BreakEvenDone;
            public string Fingerprint;
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
        // Matches "Entry: 2354.50", "@ 2354.50", "Buy Limit 1.08210", "SELL NOW 2354,50".
        private static readonly Regex EntryRegex = new Regex(@"(?:\b(?:ENTRY\s*PRICE|ENTRY|ENTER|EP|OPEN\s*PRICE|BUY|SELL|LONG|SHORT)\b|@)\s*(?:LIMIT|STOP|NOW|AT|ZONE|PRICE)?\s*[:=@\-]?\s*([0-9]+(?:[.,][0-9]+)*)", RegexOptions.IgnoreCase | RegexOptions.Compiled);
        private static readonly Regex SymbolTokenRegex = new Regex(@"\b([A-Za-z]{2,}(?:[ ]?[0-9]{1,3})?(?:/[A-Za-z]{3})?)\b", RegexOptions.Compiled);
        private static readonly Regex CommandRegex = new Regex(@"^/([a-zA-Z]+)(?:@\S+)?(?:\s+(.*))?$", RegexOptions.Compiled);

        private readonly ConcurrentQueue<IncomingMessage> _incoming = new ConcurrentQueue<IncomingMessage>();
        private readonly Dictionary<int, TradeState> _states = new Dictionary<int, TradeState>();
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
        private int _signalsAccepted;
        private int _signalsRejected;
        private int _tradesOpened;
        private DateTime? _lastSignalUtc;
        private string _lastPollError;

        // ----------------------------------------------------------------- lifecycle

        protected override void OnStart()
        {
            _tradingEnabled = EnableTrading;
            TradeLabel = string.IsNullOrWhiteSpace(TradeLabel) ? "TeleScalper" : TradeLabel.Trim();

            ParseChatIds();
            ParseSymbolMap();
            ParseWhitelist();
            RestoreStateFromOpenPositions();

            Positions.Closed += OnPositionClosed;

            _telegramReady = !string.IsNullOrWhiteSpace(BotToken) && _signalChats.Count > 0;
            if (!_telegramReady)
            {
                Print("TeleScalper: bot token and/or signal chat IDs are missing — no signals will be read. Fill in the parameters and restart the instance.");
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

            Print("TeleScalper started | account {0} | trading {1} | label {2} | chats {3}",
                Account.Number, _tradingEnabled ? "ON" : "OFF", TradeLabel, _signalChats.Count);
            Notify(string.Format("✅ TeleScalper started\nAccount: {0} ({1})\nTrading: {2}\nLot: {3}\nMax trades: {4}",
                Account.Number, Account.IsLive ? "LIVE" : "DEMO", _tradingEnabled ? "ON" : "OFF",
                UseRiskPercent ? RiskPercent.ToString("0.##", CultureInfo.InvariantCulture) + "% risk" : LotSize.ToString("0.###", CultureInfo.InvariantCulture),
                MaxOpenTrades));
        }

        protected override void OnTimer()
        {
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
                Print("TeleScalper: cancel error: {0}", ex.Message);
            }

            Notify("⛔ TeleScalper stopped. Open positions are no longer managed by the bot.");

            try
            {
                if (_http != null)
                    _http.Dispose();
            }
            catch (Exception ex)
            {
                Print("TeleScalper: dispose error: {0}", ex.Message);
            }
        }

        // ----------------------------------------------------------------- parameter parsing

        private void ParseChatIds()
        {
            foreach (var raw in SplitList(SignalChatIds))
            {
                long id;
                if (!long.TryParse(raw, NumberStyles.Integer, CultureInfo.InvariantCulture, out id))
                {
                    Print("TeleScalper: '{0}' is not a valid chat ID — skipped.", raw);
                    continue;
                }

                if (_signalChats.Count >= MaxSignalGroups)
                {
                    Print("TeleScalper: more than {0} signal chats configured — '{1}' ignored.", MaxSignalGroups, raw);
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
                {
                    Print("TeleScalper: symbol map entry '{0}' ignored (expected SIGNAL=BROKER).", pair);
                    continue;
                }

                var from = Normalize(parts[0]);
                var to = parts[1].Trim();
                if (from.Length == 0 || to.Length == 0)
                    continue;

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

        // ----------------------------------------------------------------- telegram polling

        private async Task PollLoopAsync(CancellationToken ct)
        {
            while (!ct.IsCancellationRequested)
            {
                string body = null;
                try
                {
                    var url = string.Format(CultureInfo.InvariantCulture,
                        "{0}/getUpdates?timeout={1}&offset={2}&allowed_updates=%5B%22message%22%2C%22channel_post%22%5D",
                        _apiBase, PollSeconds, _updateOffset);

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
            BeginInvokeOnMainThread(() => Print("TeleScalper: Telegram poll error: {0}", message));
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
                    Print("TeleScalper: error handling message: {0}", ex.Message);
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
                    Notify("⏸ Auto trading DISABLED. New signals will be ignored, open trades are still managed.");
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
                    Notify("Commands:\n/status — bot status\n/positions — open bot trades\n/start — enable auto trading\n/stop — disable auto trading\n/trading on|off — set auto trading\n/closeall — close all bot trades\n/help — this message");
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
            sb.AppendLine("📊 TeleScalper status");
            sb.AppendLine("Account: " + Account.Number + " (" + (Account.IsLive ? "LIVE" : "DEMO") + ")");
            sb.AppendLine("Balance: " + Account.Balance.ToString("0.00", CultureInfo.InvariantCulture) + " " + Account.Asset.Name);
            sb.AppendLine("Auto trading: " + (_tradingEnabled ? "ON" : "OFF"));
            sb.AppendLine("Signal chats: " + _signalChats.Count + "/" + MaxSignalGroups);
            sb.AppendLine("Open bot trades: " + mine.Length + "/" + MaxOpenTrades);
            sb.AppendLine("Size: " + (UseRiskPercent ? RiskPercent.ToString("0.##", CultureInfo.InvariantCulture) + "% risk" : LotSize.ToString("0.###", CultureInfo.InvariantCulture) + " lots"));
            sb.AppendLine("Signals accepted/rejected: " + _signalsAccepted + "/" + _signalsRejected);
            sb.AppendLine("Trades opened: " + _tradesOpened);
            sb.AppendLine("Last signal: " + (_lastSignalUtc.HasValue ? _lastSignalUtc.Value.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture) + " UTC" : "none yet"));
            sb.AppendLine("Server time: " + Server.Time.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture));
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
                TradeState state;
                _states.TryGetValue(position.Id, out state);
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
                    state != null && state.PartialDone ? " | TP1 taken" : string.Empty));
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
                    Print("TeleScalper: failed to close #{0}: {1}", position.Id, result.Error);
            }

            Notify("🛑 Closed " + closed + " of " + mine.Length + " bot trades on request.");
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

            var stopLossMatch = StopLossRegex.Match(text);
            if (!stopLossMatch.Success)
            {
                rejection = "no stop loss";
                return null;
            }

            double stopLoss;
            if (!TryParsePrice(stopLossMatch.Groups[1].Value, out stopLoss))
            {
                rejection = "unreadable stop loss";
                return null;
            }

            var takeProfits = ExtractTakeProfits(text);
            if (takeProfits.Count == 0)
            {
                rejection = "no take profit";
                return null;
            }

            double? entry = null;
            var entryMatch = EntryRegex.Match(text);
            if (entryMatch.Success)
            {
                double parsedEntry;
                if (TryParsePrice(entryMatch.Groups[1].Value, out parsedEntry))
                    entry = parsedEntry;
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

            // A number picked up as "entry" that is nowhere near the market (e.g. a lot size or a
            // risk figure) is discarded rather than trusted — the trade then executes at market.
            if (entry.HasValue && marketPrice > 0 && Math.Abs(entry.Value - marketPrice) / marketPrice > 0.2)
            {
                LogVerbose("Ignoring implausible entry {0} for {1} (market {2}) — treating the signal as market execution.",
                    entry.Value, brokerSymbol, marketPrice);
                entry = null;
            }

            var reference = entry ?? marketPrice;
            var tp1 = takeProfits[0];
            double? tp2 = takeProfits.Count > 1 ? takeProfits[1] : (double?)null;

            if (direction == TradeType.Buy && !(stopLoss < reference && tp1 > reference))
            {
                rejection = "BUY levels inconsistent (SL must be below, TP above entry)";
                return null;
            }

            if (direction == TradeType.Sell && !(stopLoss > reference && tp1 < reference))
            {
                rejection = "SELL levels inconsistent (SL must be above, TP below entry)";
                return null;
            }

            if (tp2.HasValue)
            {
                var tp2BeyondTp1 = direction == TradeType.Buy ? tp2.Value > tp1 : tp2.Value < tp1;
                if (!tp2BeyondTp1)
                    tp2 = null;
            }

            var signal = new ParsedSignal
            {
                BrokerSymbol = brokerSymbol,
                Direction = direction,
                Entry = entry,
                StopLoss = stopLoss,
                Tp1 = tp1,
                Tp2 = tp2,
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

                // "TP1"/"Target 2" rank by their own number, unnumbered targets rank by position in the message.
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
                // 1,234.56 — comma is a thousands separator
                text = text.Replace(",", string.Empty);
            }
            else if (hasComma)
            {
                var parts = text.Split(',');
                var last = parts[parts.Length - 1];
                // 2354,50 -> decimal comma; 1,234 / 1,234,567 -> thousands separator
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
                signal.Tp1.ToString("0.#####", CultureInfo.InvariantCulture));

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
                var token = match.Groups[1].Value;
                var normalized = Normalize(token);
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
                case "PIPS":
                case "PIP":
                case "PRICE":
                case "OPEN":
                case "CLOSE":
                case "TARGET":
                case "LIMIT":
                case "MARKET":
                case "LOTS":
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
            {
                candidates.Add(baseName + common);
            }

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

            var mine = Positions.FindAll(TradeLabel);
            if (mine.Length >= MaxOpenTrades)
            {
                Notify("⚠ Max open trades (" + MaxOpenTrades + ") reached — signal skipped:\n" + DescribeSignal(signal));
                return;
            }

            if (mine.Count(p => string.Equals(p.SymbolName, signal.BrokerSymbol, StringComparison.OrdinalIgnoreCase)) >= MaxTradesPerSymbol)
            {
                Notify("⚠ Max trades per symbol (" + MaxTradesPerSymbol + ") reached on " + signal.BrokerSymbol + " — signal skipped.");
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
                Notify(string.Format(CultureInfo.InvariantCulture, "⚠ Spread too wide on {0} ({1:0.0} pips > {2:0.0}) — signal skipped.",
                    symbol.Name, symbol.Spread / symbol.PipSize, MaxSpreadPips));
                return;
            }

            var marketPrice = signal.Direction == TradeType.Buy ? symbol.Ask : symbol.Bid;

            if (MaxEntryDeviationPips > 0 && signal.Entry.HasValue)
            {
                var deviationPips = Math.Abs(marketPrice - signal.Entry.Value) / symbol.PipSize;
                if (deviationPips > MaxEntryDeviationPips)
                {
                    Notify(string.Format(CultureInfo.InvariantCulture,
                        "⚠ {0}: price moved {1:0.0} pips away from signal entry {2} — signal skipped.",
                        symbol.Name, deviationPips, FormatPrice(symbol, signal.Entry.Value)));
                    return;
                }
            }

            // Re-validate against the live price so we never send an SL/TP on the wrong side.
            var slOnCorrectSide = signal.Direction == TradeType.Buy ? signal.StopLoss < marketPrice : signal.StopLoss > marketPrice;
            var tp1OnCorrectSide = signal.Direction == TradeType.Buy ? signal.Tp1 > marketPrice : signal.Tp1 < marketPrice;
            if (!slOnCorrectSide || !tp1OnCorrectSide)
            {
                Notify("⚠ " + symbol.Name + ": current price is already past SL or TP1 — signal skipped.");
                return;
            }

            var volume = CalculateVolume(symbol, marketPrice, signal.StopLoss);
            if (volume <= 0)
            {
                Notify("⚠ " + symbol.Name + ": calculated volume is below the minimum — signal skipped.");
                return;
            }

            var finalTakeProfit = signal.Tp2 ?? signal.Tp1;
            var comment = BuildComment(signal);

            // SL/TP are attached afterwards as absolute prices, so no protection is passed here.
            var result = ExecuteMarketOrder(signal.Direction, symbol.Name, volume, TradeLabel,
                (double?)null, (double?)null, comment);
            if (!result.IsSuccessful || result.Position == null)
            {
                Notify("❌ Order rejected on " + symbol.Name + ": " + result.Error);
                Print("TeleScalper: order rejected on {0}: {1}", symbol.Name, result.Error);
                return;
            }

            _seenFingerprints.Add(signal.Fingerprint);
            _tradesOpened++;

            var position = result.Position;
            var protection = ModifyPosition(position, RoundPrice(symbol, signal.StopLoss),
                RoundPrice(symbol, finalTakeProfit), ProtectionType.Absolute);
            if (!protection.IsSuccessful)
            {
                Print("TeleScalper: could not attach SL/TP to #{0}: {1}", position.Id, protection.Error);
                Notify("⚠ Trade #" + position.Id + " opened but SL/TP could not be set: " + protection.Error + " — the bot will keep managing it, check manually.");
            }

            _states[position.Id] = new TradeState
            {
                Tp1 = signal.Tp1,
                Tp2 = signal.Tp2,
                PartialDone = false,
                BreakEvenDone = false,
                Fingerprint = signal.Fingerprint
            };

            Print("TeleScalper: opened #{0} {1} {2} vol {3} SL {4} TP {5}", position.Id, position.TradeType, symbol.Name,
                volume, signal.StopLoss, finalTakeProfit);

            Notify(string.Format(CultureInfo.InvariantCulture,
                "🟩 New trade opened\n{0} {1} {2} lots\nEntry: {3}\nSL: {4}\nTP1: {5}{6}\nTicket: #{7}",
                symbol.Name,
                position.TradeType.ToString().ToUpperInvariant(),
                symbol.VolumeInUnitsToQuantity(position.VolumeInUnits).ToString("0.###", CultureInfo.InvariantCulture),
                FormatPrice(symbol, position.EntryPrice),
                FormatPrice(symbol, signal.StopLoss),
                FormatPrice(symbol, signal.Tp1),
                signal.Tp2.HasValue ? "\nTP2: " + FormatPrice(symbol, signal.Tp2.Value) : string.Empty,
                position.Id));
        }

        private double CalculateVolume(Symbol symbol, double entryPrice, double stopLoss)
        {
            double volume;

            if (UseRiskPercent)
            {
                var stopLossPips = Math.Abs(entryPrice - stopLoss) / symbol.PipSize;
                if (stopLossPips <= 0)
                    return 0;

                var riskAmount = Account.Balance * RiskPercent / 100.0;
                volume = symbol.VolumeForFixedRisk(riskAmount, stopLossPips, RoundingMode.Down);
            }
            else
            {
                volume = symbol.QuantityToVolumeInUnits(LotSize);
            }

            volume = symbol.NormalizeVolumeInUnits(volume, RoundingMode.Down);

            if (volume < symbol.VolumeInUnitsMin)
                return 0;

            if (volume > symbol.VolumeInUnitsMax)
                volume = symbol.VolumeInUnitsMax;

            return volume;
        }

        private string BuildComment(ParsedSignal signal)
        {
            var comment = string.Format(CultureInfo.InvariantCulture, "TS|{0}|{1}|{2}",
                signal.Fingerprint,
                signal.Tp1.ToString("0.#####", CultureInfo.InvariantCulture),
                signal.Tp2.HasValue ? signal.Tp2.Value.ToString("0.#####", CultureInfo.InvariantCulture) : string.Empty);

            return Trim(comment, 60);
        }

        // ----------------------------------------------------------------- management

        private void ManageOpenPositions()
        {
            var mine = Positions.FindAll(TradeLabel);
            if (mine.Length == 0)
                return;

            foreach (var position in mine)
            {
                TradeState state;
                if (!_states.TryGetValue(position.Id, out state))
                {
                    state = RestoreState(position);
                    if (state == null)
                        continue;

                    _states[position.Id] = state;
                }

                try
                {
                    ManagePosition(position, state);
                }
                catch (Exception ex)
                {
                    Print("TeleScalper: manage error on #{0}: {1}", position.Id, ex.Message);
                }
            }
        }

        private void ManagePosition(Position position, TradeState state)
        {
            var symbol = position.Symbol;
            var price = position.TradeType == TradeType.Buy ? symbol.Bid : symbol.Ask;
            var tolerance = symbol.TickSize / 2.0;

            if (!state.BreakEvenDone && BreakEvenTriggerPips > 0 && position.Pips >= BreakEvenTriggerPips)
            {
                if (MoveToBreakEven(position, state))
                    Notify("🎯 Break even activated\n" + position.SymbolName + " #" + position.Id + "\nSL moved to break even.");
            }

            if (state.PartialDone)
                return;

            var tp1Reached = position.TradeType == TradeType.Buy
                ? price >= state.Tp1 - tolerance
                : price <= state.Tp1 + tolerance;

            if (!tp1Reached)
                return;

            TakeFirstTarget(position, state);
        }

        private void TakeFirstTarget(Position position, TradeState state)
        {
            var symbol = position.Symbol;
            state.PartialDone = true;

            var closeVolume = PartialClosePercent > 0
                ? symbol.NormalizeVolumeInUnits(position.VolumeInUnits * PartialClosePercent / 100.0, RoundingMode.Down)
                : 0;

            var remaining = position.VolumeInUnits - closeVolume;
            var canSplit = closeVolume >= symbol.VolumeInUnitsMin && remaining >= symbol.VolumeInUnitsMin;

            if (PartialClosePercent > 0 && !canSplit)
            {
                if (PartialFallback == PartialFallbackMode.CloseFullAtTp1)
                {
                    var full = ClosePosition(position);
                    if (full.IsSuccessful)
                    {
                        Notify(string.Format(CultureInfo.InvariantCulture,
                            "💰 TP1 hit — position closed in full ({0} cannot be split at this volume)\n{1} #{2}",
                            symbol.Name, symbol.Name, position.Id));
                    }
                    else
                    {
                        Print("TeleScalper: full close at TP1 failed on #{0}: {1}", position.Id, full.Error);
                    }

                    return;
                }

                LogVerbose("#{0}: volume {1} cannot be split at TP1 — letting it run to the final target with SL at break even.",
                    position.Id, position.VolumeInUnits);
            }
            else if (PartialClosePercent > 0)
            {
                var partial = ClosePosition(position, closeVolume);
                if (partial.IsSuccessful)
                {
                    Notify(string.Format(CultureInfo.InvariantCulture,
                        "💰 {0:0.#}% profit taken at TP1\n{1} #{2}\nClosed {3} lots at {4}",
                        PartialClosePercent,
                        symbol.Name,
                        position.Id,
                        symbol.VolumeInUnitsToQuantity(closeVolume).ToString("0.###", CultureInfo.InvariantCulture),
                        FormatPrice(symbol, state.Tp1)));
                }
                else
                {
                    Print("TeleScalper: partial close failed on #{0}: {1}", position.Id, partial.Error);
                }
            }

            var live = Positions.FindById(position.Id);
            if (live == null)
                return;

            if (BreakEvenAtTp1)
                MoveToBreakEven(live, state);

            if (state.Tp2.HasValue)
            {
                var target = RoundPrice(live.Symbol, state.Tp2.Value);
                if (!live.TakeProfit.HasValue || Math.Abs(live.TakeProfit.Value - target) > live.Symbol.TickSize / 2.0)
                {
                    var result = ModifyPosition(live, live.StopLoss, target, ProtectionType.Absolute);
                    if (!result.IsSuccessful)
                        Print("TeleScalper: could not set TP2 on #{0}: {1}", live.Id, result.Error);
                }
            }
        }

        private bool MoveToBreakEven(Position position, TradeState state)
        {
            var symbol = position.Symbol;
            var buffer = BreakEvenBufferPips * symbol.PipSize;
            var target = position.TradeType == TradeType.Buy
                ? position.EntryPrice + buffer
                : position.EntryPrice - buffer;

            target = RoundPrice(symbol, target);

            var currentPrice = position.TradeType == TradeType.Buy ? symbol.Bid : symbol.Ask;
            var wouldTriggerNow = position.TradeType == TradeType.Buy ? target >= currentPrice : target <= currentPrice;
            if (wouldTriggerNow)
            {
                LogVerbose("#{0}: break even level {1} is already through the market — skipped for now.", position.Id, target);
                return false;
            }

            if (position.StopLoss.HasValue)
            {
                var alreadyBetter = position.TradeType == TradeType.Buy
                    ? position.StopLoss.Value >= target - symbol.TickSize / 2.0
                    : position.StopLoss.Value <= target + symbol.TickSize / 2.0;

                if (alreadyBetter)
                {
                    state.BreakEvenDone = true;
                    return false;
                }
            }

            var result = ModifyPosition(position, target, position.TakeProfit, ProtectionType.Absolute);
            if (!result.IsSuccessful)
            {
                Print("TeleScalper: break even failed on #{0}: {1}", position.Id, result.Error);
                return false;
            }

            state.BreakEvenDone = true;
            Print("TeleScalper: #{0} SL moved to break even at {1}", position.Id, target);
            return true;
        }

        private TradeState RestoreState(Position position)
        {
            var comment = position.Comment ?? string.Empty;
            if (!comment.StartsWith("TS|", StringComparison.OrdinalIgnoreCase))
                return null;

            var parts = comment.Split('|');
            if (parts.Length < 3)
                return null;

            double tp1;
            if (!double.TryParse(parts[2], NumberStyles.Float, CultureInfo.InvariantCulture, out tp1))
                return null;

            double? tp2 = null;
            double parsedTp2;
            if (parts.Length > 3 && double.TryParse(parts[3], NumberStyles.Float, CultureInfo.InvariantCulture, out parsedTp2))
                tp2 = parsedTp2;

            // If the stop is already at or beyond entry, TP1 management has clearly already happened.
            var stopAtBreakEven = position.StopLoss.HasValue && (position.TradeType == TradeType.Buy
                ? position.StopLoss.Value >= position.EntryPrice
                : position.StopLoss.Value <= position.EntryPrice);

            var state = new TradeState
            {
                Tp1 = tp1,
                Tp2 = tp2,
                Fingerprint = parts[1],
                PartialDone = stopAtBreakEven,
                BreakEvenDone = stopAtBreakEven
            };

            if (!string.IsNullOrEmpty(state.Fingerprint))
                _seenFingerprints.Add(state.Fingerprint);

            LogVerbose("Adopted existing position #{0} ({1}) TP1 {2} TP2 {3} partialDone {4}",
                position.Id, position.SymbolName, tp1, tp2, state.PartialDone);

            return state;
        }

        private void RestoreStateFromOpenPositions()
        {
            foreach (var position in Positions.FindAll(TradeLabel))
            {
                var state = RestoreState(position);
                if (state != null)
                    _states[position.Id] = state;
            }

            if (_states.Count > 0)
                Print("TeleScalper: adopted {0} existing position(s).", _states.Count);
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var position = args.Position;
            if (!string.Equals(position.Label, TradeLabel, StringComparison.Ordinal))
                return;

            if (Positions.FindById(position.Id) != null)
                return; // partial close — the position lives on, keep its state

            TradeState state;
            var known = _states.TryGetValue(position.Id, out state);
            _states.Remove(position.Id);

            Notify(string.Format(CultureInfo.InvariantCulture,
                "🏁 Trade closed\n{0} #{1}\nReason: {2}\nPips: {3:0.0}\nNet: {4:0.00} {5}{6}",
                position.SymbolName,
                position.Id,
                args.Reason,
                position.Pips,
                position.NetProfit,
                Account.Asset.Name,
                known && state.PartialDone ? "\n(TP1 had been taken)" : string.Empty));
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
            return string.Format(CultureInfo.InvariantCulture, "{0} {1}\nEntry: {2}\nSL: {3}\nTP1: {4}{5}",
                signal.BrokerSymbol,
                signal.Direction.ToString().ToUpperInvariant(),
                signal.Entry.HasValue ? FormatPrice(symbol, signal.Entry.Value) : "market",
                FormatPrice(symbol, signal.StopLoss),
                FormatPrice(symbol, signal.Tp1),
                signal.Tp2.HasValue ? "\nTP2: " + FormatPrice(symbol, signal.Tp2.Value) : string.Empty);
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
                Print("TeleScalper: " + string.Format(CultureInfo.InvariantCulture, format, args));
        }
    }
}
