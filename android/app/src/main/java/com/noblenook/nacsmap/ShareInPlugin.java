package com.noblenook.nacsmap;

import android.content.Intent;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * 다른 앱에서 공유(ACTION_SEND text/plain)하거나 geo: 링크로 연 목적지를 웹 화면에 전달합니다.
 * - 앱이 꺼져 있다가 공유로 열린 경우: JS 가 getPending() 으로 가져감
 * - 앱이 켜져 있을 때 공유된 경우: "share" 이벤트로 전달
 */
@CapacitorPlugin(name = "ShareIn")
public class ShareInPlugin extends Plugin {
    private String pending;

    @Override
    public void load() {
        pending = extract(getActivity().getIntent());
    }

    @Override
    protected void handleOnNewIntent(Intent intent) {
        super.handleOnNewIntent(intent);
        String text = extract(intent);
        if (text != null) {
            JSObject data = new JSObject();
            data.put("text", text);
            notifyListeners("share", data, true);
        }
    }

    @PluginMethod
    public void getPending(PluginCall call) {
        JSObject data = new JSObject();
        data.put("text", pending);
        pending = null;
        call.resolve(data);
    }

    private static String extract(Intent intent) {
        if (intent == null || intent.getAction() == null) return null;
        if (Intent.ACTION_SEND.equals(intent.getAction())) {
            String text = intent.getStringExtra(Intent.EXTRA_TEXT);
            String subject = intent.getStringExtra(Intent.EXTRA_SUBJECT);
            if (text == null) return subject;
            if (subject != null && !text.contains(subject)) return subject + "\n" + text;
            return text;
        }
        if (Intent.ACTION_VIEW.equals(intent.getAction()) && intent.getData() != null) {
            return intent.getData().toString();
        }
        return null;
    }
}
