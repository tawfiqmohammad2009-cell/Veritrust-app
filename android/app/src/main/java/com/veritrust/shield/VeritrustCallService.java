package com.veritrust.shield;

import android.telecom.Call;
import android.telecom.InCallService;
import android.util.Log;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

public class VeritrustCallService extends InCallService {
    private static final String TAG = "VeritrustCallService";
    // Pointing to your local Flask backend endpoint
    private static final String API_URL = "http://10.24.99.178:5000/api/v1/check-number";

    @Override
    public void onCallAdded(Call call) {
        super.onCallAdded(call);
        
        if (call.getDetails() != null && call.getDetails().getHandle() != null) {
            String phoneNumber = call.getDetails().getHandle().getSchemeSpecificPart();
            Log.d(TAG, "Incoming call intercepted from: " + phoneNumber);
            
            // Send phone number to Flask threat-detection engine in a background thread
            checkNumberWithFlask(phoneNumber);
        }
    }

    private void checkNumberWithFlask(final String phoneNumber) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    URL url = new URL(API_URL);
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setRequestMethod("POST");
                    conn.setRequestProperty("Content-Type", "application/json; utf-8");
                    conn.setRequestProperty("Accept", "application/json");
                    conn.setDoOutput(true);

                    // JSON payload with the intercepted phone number
                    String jsonInputString = "{\"phone\": \"" + phoneNumber + "\"}";

                    try (OutputStream os = conn.getOutputStream()) {
                        byte[] input = jsonInputString.getBytes("utf-8");
                        os.write(input, 0, input.length);
                    }

                    int responseCode = conn.getResponseCode();
                    Log.d(TAG, "Flask API Response Code: " + responseCode);

                } catch (Exception e) {
                    Log.e(TAG, "Failed to connect to Flask threat-detection engine", e);
                }
            }
        }).start();
    }

    @Override
    public void onCallRemoved(Call call) {
        super.onCallRemoved(call);
        Log.d(TAG, "Call ended.");
    }
}
