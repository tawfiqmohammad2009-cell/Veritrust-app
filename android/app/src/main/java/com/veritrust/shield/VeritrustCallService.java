package com.veritrust.shield;

import android.telecom.Call;
import android.telecom.InCallService;
import android.util.Log;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class VeritrustCallService extends InCallService {
    private static final String TAG = "VeritrustCallService";

    @Override
    public void onCallAdded(Call call) {
        super.onCallAdded(call);
        String phoneNumber = "";
        if (call.getDetails() != null && call.getDetails().getHandle() != null) {
            phoneNumber = call.getDetails().getHandle().getSchemeSpecificPart();
        }
        Log.d(TAG, "Call intercepted: " + phoneNumber);
        sendCallToServer(phoneNumber);
    }

    @Override
    public void onCallRemoved(Call call) {
        super.onCallRemoved(call);
        Log.d(TAG, "Call ended");
    }

    private void sendCallToServer(final String number) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    URL url = new URL("http://10.0.2.2:5000/log_call");
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setRequestMethod("POST");
                    conn.setRequestProperty("Content-Type", "application/json; utf-8");
                    conn.setDoOutput(true);

                    String jsonInputString = "{\"phone_number\": \"" + number + "\"}";
                    try (OutputStream os = conn.getOutputStream()) {
                        byte[] input = jsonInputString.getBytes("utf-8");
                        os.write(input, 0, input.length);
                    }

                    int responseCode = conn.getResponseCode();
                    Log.d(TAG, "Server sync status: " + responseCode);
                } catch (Exception e) {
                    Log.e(TAG, "Failed to connect to Flask backend", e);
                }
            }
        }).start();
    }
}
