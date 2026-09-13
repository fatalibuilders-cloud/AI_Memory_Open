package com.fatalibuilders.nairobiwild;

import android.annotation.SuppressLint;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;

import androidx.activity.OnBackPressedCallback;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;
import androidx.webkit.WebViewAssetLoader;
import androidx.webkit.WebViewClientCompat;

/**
 * The whole Android app: one WebView showing one bundled HTML file.
 *
 * The game itself is the web page — this class exists only to give it a
 * window, a real web origin, the system bars it should not draw under, and a
 * back button that behaves the way an Android player expects.
 */
public class MainActivity extends AppCompatActivity {

    /** Anything served from here is our own asset folder, never the network. */
    private static final String ORIGIN = "https://appassets.androidplatform.net";
    private static final String START = ORIGIN + "/assets/index.html";

    /** Dusk over the savanna — matches the page's own background exactly, so
     *  there is no flash of another colour while the page is parsing. */
    private static final int NIGHT = Color.parseColor("#0e1519");

    private WebView web;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Draw behind the bars, then pad the page back out of them below.
        // From Android 15 this is not a choice — the system does it anyway —
        // so it is done explicitly here and handled rather than fought.
        WindowCompat.setDecorFitsSystemWindows(getWindow(), false);
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        getWindow().setNavigationBarColor(Color.TRANSPARENT);
        WindowInsetsControllerCompat bars =
                WindowCompat.getInsetsController(getWindow(), getWindow().getDecorView());
        bars.setAppearanceLightStatusBars(false);      // light icons on a dark page
        bars.setAppearanceLightNavigationBars(false);

        final boolean debuggable =
                (getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0;
        WebView.setWebContentsDebuggingEnabled(debuggable);

        web = new WebView(this);
        web.setLayoutParams(new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        web.setBackgroundColor(NIGHT);
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);
        web.setLongClickable(false);
        web.setHapticFeedbackEnabled(false);
        // A long press on a tile must not offer "copy text" or start a
        // selection — this is a game board, not a document.
        web.setOnLongClickListener(v -> true);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);      // the save file lives in localStorage
        s.setAllowFileAccess(false);       // assets arrive through the loader
        s.setAllowContentAccess(false);
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        // Ignore the system font-size setting. The board is a fixed grid; a
        // player on "largest text" would otherwise see it burst its frame.
        s.setTextZoom(100);
        // The page gates its own audio on the first tap. Letting the WebView
        // start sound without a gesture removes one more way for a player to
        // report silence that is not the game's fault.
        s.setMediaPlaybackRequiresUserGesture(false);

        final WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        web.setWebViewClient(new WebViewClientCompat() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest req) {
                return loader.shouldInterceptRequest(req.getUrl());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                return openExternally(req.getUrl());
            }

            // Android 5 and 6 still call the string form.
            @SuppressWarnings("deprecation")
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return openExternally(Uri.parse(url));
            }
        });

        setContentView(web);

        ViewCompat.setOnApplyWindowInsetsListener(web, (v, insets) -> {
            Insets bar = insets.getInsets(
                    WindowInsetsCompat.Type.systemBars() | WindowInsetsCompat.Type.displayCutout());
            v.setPadding(bar.left, bar.top, bar.right, bar.bottom);
            return WindowInsetsCompat.CONSUMED;
        });

        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                // Ask the page first. It closes an overlay or steps back a
                // screen and answers true; only when it is already on the home
                // screen does back mean "leave the game".
                web.evaluateJavascript(
                        "(function(){try{return !!(window.NW_back && window.NW_back());}"
                                + "catch(e){return false;}})()",
                        value -> {
                            if (!"true".equals(value)) {
                                setEnabled(false);
                                getOnBackPressedDispatcher().onBackPressed();
                            }
                        });
            }
        });

        if (savedInstanceState != null) {
            web.restoreState(savedInstanceState);
        } else {
            web.loadUrl(START);
        }
    }

    /**
     * Our own page loads in place; anything else — a challenge link, a credits
     * link — opens in the browser rather than inside the game's own window,
     * where there would be no way back out.
     *
     * @return true when the WebView should not load it
     */
    private boolean openExternally(Uri u) {
        if (u == null) return false;
        if (ORIGIN.equals(u.getScheme() + "://" + u.getAuthority())) return false;
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, u));
        } catch (ActivityNotFoundException ignored) {
            // No browser installed: staying put beats crashing.
        }
        return true;
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.onResume();
        web.resumeTimers();
        // Nobody should have to poke the screen mid-puzzle to keep it awake.
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    }

    @Override
    protected void onPause() {
        // Stop the music and the scheduler the moment the app leaves the
        // foreground, rather than draining a battery from the background.
        web.onPause();
        web.pauseTimers();
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        if (web != null) {
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }
}
