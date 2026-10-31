package com.kassandra.pokedex;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Kassandra's Pokédex: the app itself is a web page (assets/index.html).
 * This wrapper gives it three things a web page can't do on its own:
 * download TCGplayer's data, save files on the tablet, and share text.
 */
public class MainActivity extends Activity {
    private WebView web;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setLoadsImagesAutomatically(true);
        s.setTextZoom(100);
        web.setWebViewClient(new WebViewClient());
        web.setWebChromeClient(new WebChromeClient());
        web.addJavascriptInterface(new Bridge(), "Android");
        setContentView(web);
        web.loadUrl("file:///android_asset/index.html");
    }

    @Override
    public void onBackPressed() {
        // let the page close a pop-up first; leave the app only from the main screen
        web.evaluateJavascript("window.goBack ? window.goBack() : false", result -> {
            if (!"true".equals(result)) {
                MainActivity.super.onBackPressed();
            }
        });
    }

    private File file(String name) {
        String safe = name.replaceAll("[^A-Za-z0-9._-]", "_");
        return new File(getFilesDir(), safe);
    }

    class Bridge {
        /** Download a web address in the background; the answer goes to window.__done(id, ok, text). */
        @JavascriptInterface
        public void get(final String id, final String address) {
            new Thread(() -> {
                boolean ok = false;
                String body;
                try {
                    HttpURLConnection c = (HttpURLConnection) new URL(address).openConnection();
                    c.setRequestProperty("User-Agent", "KassandrasPokedex/1.0 (Android)");
                    c.setConnectTimeout(20000);
                    c.setReadTimeout(30000);
                    int code = c.getResponseCode();
                    InputStream in = code < 400 ? c.getInputStream() : c.getErrorStream();
                    body = read(in);
                    ok = code < 400;
                } catch (Exception e) {
                    body = String.valueOf(e);
                }
                final String js = "window.__done(" + JSONObject.quote(id) + "," + ok + "," + JSONObject.quote(body) + ")";
                runOnUiThread(() -> web.evaluateJavascript(js, null));
            }).start();
        }

        @JavascriptInterface
        public String load(String name) {
            try {
                return read(new FileInputStream(file(name)));
            } catch (Exception e) {
                return "";
            }
        }

        @JavascriptInterface
        public boolean save(String name, String text) {
            try {
                File tmp = file(name + ".tmp");
                FileOutputStream out = new FileOutputStream(tmp);
                out.write(text.getBytes(StandardCharsets.UTF_8));
                out.close();
                return tmp.renameTo(file(name));
            } catch (Exception e) {
                return false;
            }
        }

        @JavascriptInterface
        public double modified(String name) {
            File f = file(name);
            return f.exists() ? f.lastModified() / 1000.0 : 0;
        }

        @JavascriptInterface
        public void share(String title, String text) {
            Intent send = new Intent(Intent.ACTION_SEND);
            send.setType("text/plain");
            send.putExtra(Intent.EXTRA_SUBJECT, title);
            send.putExtra(Intent.EXTRA_TEXT, text);
            runOnUiThread(() -> startActivity(Intent.createChooser(send, title)));
        }
    }

    private static String read(InputStream in) throws Exception {
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        byte[] chunk = new byte[16384];
        int n;
        while ((n = in.read(chunk)) > 0) {
            buf.write(chunk, 0, n);
        }
        in.close();
        return buf.toString("UTF-8");
    }
}
