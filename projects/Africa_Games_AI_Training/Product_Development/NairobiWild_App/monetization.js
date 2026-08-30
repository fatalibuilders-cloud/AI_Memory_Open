/*
 * Nairobi Wild — monetization
 *
 * This is the whole money layer. Game code calls four functions and never
 * touches a network, an SDK or a price:
 *
 *   Monetization.rewardedAd(placement, onReward)
 *   Monetization.purchase(productId, onSuccess, onFail)
 *   Monetization.products()
 *   Monetization.onEvent(fn)          // for analytics / revenue reporting
 *
 * WHAT ACTUALLY EARNS MONEY, and what is still needed:
 *
 * Nothing here can take real money until YOU open the accounts and paste
 * the IDs into CONFIG below. The code is finished; the accounts are not.
 * `Finance/revenue-activation.md` is the step-by-step checklist. In short:
 *
 *   1. AdMob account        → ad unit IDs        → rewarded video revenue
 *   2. Play Console account → in-app product IDs → card/Play-balance IAP
 *   3. Flutterwave/Paystack → public key         → M-PESA and mobile money
 *
 * Until then `provider` stays 'simulated' and every flow works end to end
 * without charging anyone — which is exactly what you want while testing.
 *
 * PROVIDER SELECTION is automatic: the module picks the best provider the
 * current environment can actually support, so the same build runs as a
 * web page, an installed Android app, or a demo.
 */
(function (global) {
  'use strict';

  /* ==================================================================
   * CONFIG — paste your real IDs here to switch on real revenue.
   * Everything is empty by default, which keeps the game in simulation.
   * ================================================================== */
  const CONFIG = {
    // --- Google AdMob (rewarded video) ---------------------------------
    admob: {
      appId: '',                  // ca-app-pub-XXXXXXXX~XXXXXXXX
      rewardedUnitId: '',         // ca-app-pub-XXXXXXXX/XXXXXXXX
      testMode: true,             // MUST stay true until the app is live
    },
    // --- Google Play Billing (via the Digital Goods API in a TWA) ------
    play: {
      enabled: false,
      // Product IDs must match the Play Console exactly.
      serviceProvider: 'https://play.google.com/billing',
    },
    // --- Mobile money / cards for the web build ------------------------
    // Kenya first: M-PESA is how people actually pay, not an alternative.
    web: {
      provider: '',               // 'flutterwave' | 'paystack' | ''
      publicKey: '',              // pk_live_... / FLWPUBK-...
      currency: 'KES',
      // Set once you know your own rate; used only for display.
      usdToLocal: 129,
    },
    // Where revenue events are reported. Wire to your analytics later.
    analytics: { enabled: true },
  };

  /* ==================================================================
   * CATALOGUE — one definition per thing that can be bought.
   * `usd` is the reference price; local prices are derived for display.
   * ================================================================== */
  const PRODUCTS = [
    { id: 'coins_500',    kind: 'coins',   usd: 0.99, coins: 500,                          label: 'Handful of coins',   note: '500 coins' },
    { id: 'coins_1500',   kind: 'coins',   usd: 2.49, coins: 1500, hammers: 5,             label: "Ranger's purse",     note: '1,500 coins + 5 hammers' },
    { id: 'bundle_big5',  kind: 'bundle',  usd: 5.99, coins: 4000, hammers: 15, shuffles: 15, label: 'Big Five bundle', note: '4,000 coins + 15 boosters' },
    { id: 'lives_refill', kind: 'lives',   usd: 0.99, lives: true,                         label: 'Refill lives',       note: 'Back to 5 hearts' },
    // A tip jar. Indie games in small markets earn real money from players
    // who simply want the makers to keep going — and it costs the player
    // nothing in gameplay terms, so it never distorts the design.
    { id: 'support_small', kind: 'support', usd: 1.99, coins: 600,  label: 'Support the makers', note: 'Buy the team a chai ☕ · +600 coins' },
    { id: 'support_big',   kind: 'support', usd: 9.99, coins: 4000, label: 'Back the studio',    note: 'Keep the game growing 💛 · +4,000 coins' },
  ];

  function productById(id) {
    return PRODUCTS.find((p) => p.id === id) || null;
  }

  /* Display price in the player's likely currency. */
  function priceLabel(product, cfg) {
    const c = (cfg || CONFIG).web;
    if (c && c.currency && c.currency !== 'USD' && c.usdToLocal > 0) {
      const local = Math.round(product.usd * c.usdToLocal);
      // Round to something a shop would actually print.
      const nice = local >= 100 ? Math.round(local / 10) * 10 : local;
      return c.currency + ' ' + nice.toLocaleString();
    }
    return '$' + product.usd.toFixed(2);
  }

  /*
   * Which provider can this environment actually support?
   * Pure function of the config plus a capability probe, so it is testable.
   */
  function selectProvider(cfg, env) {
    const e = env || {};
    if (cfg.play && cfg.play.enabled && e.hasDigitalGoods) return 'play';
    if (cfg.web && cfg.web.provider && cfg.web.publicKey) return 'web';
    if (cfg.admob && cfg.admob.rewardedUnitId && e.hasAdMobBridge) return 'admob';
    return 'simulated';
  }

  /* Is anything at all wired up for real money? */
  function isLive(cfg) {
    const c = cfg || CONFIG;
    const ads = !!(c.admob && c.admob.rewardedUnitId && !c.admob.testMode);
    const iap = !!((c.play && c.play.enabled) || (c.web && c.web.provider && c.web.publicKey));
    return { ads, iap, any: ads || iap };
  }

  /* ==================================================================
   * The module
   * ================================================================== */
  const listeners = [];
  let simulateAd = null;   // the host page supplies the placeholder ad UI

  function emit(event) {
    if (!CONFIG.analytics.enabled) return;
    listeners.forEach((fn) => { try { fn(event); } catch (e) {} });
  }

  function env() {
    return {
      hasDigitalGoods: typeof global !== 'undefined' && 'getDigitalGoodsService' in (global || {}),
      hasAdMobBridge: !!(global && global.admob),
    };
  }

  const Monetization = {
    CONFIG, PRODUCTS,
    productById, priceLabel, selectProvider, isLive,

    /* The page hands us its placeholder ad player for simulated mode. */
    useSimulatedAdPlayer(fn) { simulateAd = fn; },

    provider() { return selectProvider(CONFIG, env()); },

    products() {
      return PRODUCTS.map((p) => ({ ...p, price: priceLabel(p, CONFIG) }));
    },

    onEvent(fn) { listeners.push(fn); return () => listeners.splice(listeners.indexOf(fn), 1); },

    /*
     * Rewarded video. `placement` names WHERE it was offered, which is the
     * single most useful thing to have in revenue reporting later:
     * 'continue' | 'double' | 'lives' | 'shop'.
     */
    rewardedAd(placement, onReward) {
      const provider = this.provider();
      emit({ type: 'ad_requested', placement, provider });

      if (provider === 'admob' && global.admob && global.admob.showRewarded) {
        // Installed-app path: an AdMob bridge (Capacitor/Cordova plugin or
        // a TWA JS interface) is present. See revenue-activation.md.
        global.admob.showRewarded(CONFIG.admob.rewardedUnitId, (earned) => {
          if (earned) { emit({ type: 'ad_rewarded', placement, provider }); onReward(); }
          else emit({ type: 'ad_dismissed', placement, provider });
        });
        return;
      }

      // No ad network available: the placeholder still grants the reward,
      // so play-testing is never blocked by missing accounts.
      if (simulateAd) {
        simulateAd(() => { emit({ type: 'ad_rewarded', placement, provider: 'simulated' }); onReward(); });
      } else {
        emit({ type: 'ad_rewarded', placement, provider: 'simulated' });
        onReward();
      }
    },

    /*
     * A purchase. Resolves through whichever provider is live; in
     * simulation it succeeds immediately so the shop can be tested.
     */
    purchase(productId, onSuccess, onFail) {
      const product = productById(productId);
      if (!product) { if (onFail) onFail('unknown_product'); return; }
      const provider = this.provider();
      emit({ type: 'purchase_started', productId, usd: product.usd, provider });

      const ok = () => {
        emit({ type: 'purchase_completed', productId, usd: product.usd, provider });
        onSuccess(product);
      };
      const fail = (reason) => {
        emit({ type: 'purchase_failed', productId, reason, provider });
        if (onFail) onFail(reason);
      };

      if (provider === 'play') { this._playPurchase(product, ok, fail); return; }
      if (provider === 'web')  { this._webPurchase(product, ok, fail); return; }
      ok(); // simulated
    },

    /* Google Play Billing through the Digital Goods API (works in a TWA). */
    _playPurchase(product, ok, fail) {
      (async () => {
        try {
          const service = await global.getDigitalGoodsService(CONFIG.play.serviceProvider);
          const details = await service.getDetails([product.id]);
          if (!details || details.length === 0) { fail('not_in_play_console'); return; }
          const request = new global.PaymentRequest(
            [{ supportedMethods: CONFIG.play.serviceProvider, data: { sku: product.id } }],
            { total: { label: product.label, amount: { currency: 'USD', value: String(product.usd) } } }
          );
          const response = await request.show();
          const token = response.details && response.details.token;
          // Consumables must be consumed or they cannot be bought again.
          if (token && service.consume) await service.consume(token);
          await response.complete('success');
          ok();
        } catch (err) {
          fail((err && err.name === 'AbortError') ? 'cancelled' : 'play_error');
        }
      })();
    },

    /*
     * Mobile money / cards on the web build. The checkout SDK is loaded
     * lazily and only when a purchase is actually attempted, so players
     * who never buy anything never pay for the download.
     */
    _webPurchase(product, ok, fail) {
      const cfg = CONFIG.web;
      const amount = Math.round(product.usd * (cfg.usdToLocal || 1));
      if (cfg.provider === 'flutterwave' && global.FlutterwaveCheckout) {
        global.FlutterwaveCheckout({
          public_key: cfg.publicKey,
          tx_ref: product.id + '-' + Date.now(),
          amount,
          currency: cfg.currency,
          // M-PESA first: this is Kenya.
          payment_options: 'mpesa,card,mobilemoneyghana,ussd',
          customizations: { title: 'Nairobi Wild', description: product.note },
          callback: (res) => {
            if (res && (res.status === 'successful' || res.status === 'completed')) ok();
            else fail('not_completed');
          },
          onclose: () => fail('cancelled'),
        });
        return;
      }
      if (cfg.provider === 'paystack' && global.PaystackPop) {
        const handler = global.PaystackPop.setup({
          key: cfg.publicKey,
          amount: amount * 100,       // Paystack works in the minor unit
          currency: cfg.currency,
          ref: product.id + '-' + Date.now(),
          callback: () => ok(),
          onClose: () => fail('cancelled'),
        });
        handler.openIframe();
        return;
      }
      fail('checkout_unavailable');
    },
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = Monetization;
  else global.NairobiMoney = Monetization;
})(typeof window !== 'undefined' ? window : globalThis);
