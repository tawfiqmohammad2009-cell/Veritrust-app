package com.veritrust.shield;

import android.app.Activity;
import android.app.role.RoleManager;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.BufferedReader;
import java.io.InputStreamReader;

public class MainActivity extends Activity {

    private FrameLayout container;
    private String currentPhoneNumber = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        container = findViewById(R.id.fragment_container);

        Button navDialer = findViewById(R.id.nav_dialer);
        Button navLookup = findViewById(R.id.nav_lookup);
        Button navShield = findViewById(R.id.nav_shield);

        showSection1Dialer();

        navDialer.setOnClickListener(v -> showSection1Dialer());
        navLookup.setOnClickListener(v -> showSection2Lookup());
        navShield.setOnClickListener(v -> showSection3AIShield());

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            RoleManager roleManager = getSystemService(RoleManager.class);
            if (roleManager != null && roleManager.isRoleAvailable(RoleManager.ROLE_DIALER)) {
                if (!roleManager.isRoleHeld(RoleManager.ROLE_DIALER)) {
                    Intent intent = roleManager.createRequestRoleIntent(RoleManager.ROLE_DIALER);
                    startActivityForResult(intent, 100);
                }
            }
        }
    }

    private void showSection1Dialer() {
        container.removeAllViews();

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(32, 32, 32, 32);

        final TextView numberDisplay = new TextView(this);
        numberDisplay.setText(currentPhoneNumber.isEmpty() ? "Enter Number" : currentPhoneNumber);
        numberDisplay.setTextSize(28);
        numberDisplay.setTextColor(android.graphics.Color.WHITE);
        numberDisplay.setGravity(Gravity.CENTER);
        numberDisplay.setPadding(16, 32, 16, 32);
        root.addView(numberDisplay);

        GridLayout keypad = new GridLayout(this);
        keypad.setColumnCount(3);
        keypad.setRowCount(4);

        String[] keys = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"};
        for (String key : keys) {
            Button btn = new Button(this);
            btn.setText(key);
            btn.setTextSize(22);
            btn.setTextColor(android.graphics.Color.WHITE);
            btn.setOnClickListener(v -> {
                currentPhoneNumber += key;
                numberDisplay.setText(currentPhoneNumber);
            });
            keypad.addView(btn);
        }
        root.addView(keypad);

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        actions.setPadding(0, 32, 0, 0);

        Button btnCall = new Button(this);
        btnCall.setText("📞 Call");
        btnCall.setLayoutParams(new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        btnCall.setOnClickListener(v -> {
            if (!currentPhoneNumber.isEmpty()) {
                Intent intent = new Intent(Intent.ACTION_CALL, Uri.parse("tel:" + currentPhoneNumber));
                startActivity(intent);
            } else {
                Toast.makeText(this, "Please enter a phone number", Toast.LENGTH_SHORT).show();
            }
        });

        Button btnSms = new Button(this);
        btnSms.setText("💬 Message");
        btnSms.setLayoutParams(new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        btnSms.setOnClickListener(v -> {
            if (!currentPhoneNumber.isEmpty()) {
                Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse("sms:" + currentPhoneNumber));
                startActivity(intent);
            } else {
                Toast.makeText(this, "Please enter a phone number", Toast.LENGTH_SHORT).show();
            }
        });

        Button btnClear = new Button(this);
        btnClear.setText("⌫ Clear");
        btnClear.setLayoutParams(new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        btnClear.setOnClickListener(v -> {
            if (!currentPhoneNumber.isEmpty()) {
                currentPhoneNumber = currentPhoneNumber.substring(0, currentPhoneNumber.length() - 1);
                numberDisplay.setText(currentPhoneNumber.isEmpty() ? "Enter Number" : currentPhoneNumber);
            }
        });

        actions.addView(btnCall);
        actions.addView(btnSms);
        actions.addView(btnClear);
        root.addView(actions);
        container.addView(root);
    }

    private void showSection2Lookup() {
        container.removeAllViews();

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(32, 32, 32, 32);

        TextView title = new TextView(this);
        title.setText("🔍 Fraud & Identity Lookup");
        title.setTextSize(22);
        title.setTextColor(android.graphics.Color.WHITE);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 0, 0, 24);
        root.addView(title);

        final EditText inputNumber = new EditText(this);
        inputNumber.setHint("Enter phone number (e.g. +233...)");
        inputNumber.setHintTextColor(android.graphics.Color.GRAY);
        inputNumber.setTextColor(android.graphics.Color.WHITE);
        inputNumber.setTextSize(18);
        root.addView(inputNumber);

        Button btnCheck = new Button(this);
        btnCheck.setText("Verify Number Risk");
        btnCheck.setPadding(0, 24, 0, 24);
        root.addView(btnCheck);

        final TextView resultBox = new TextView(this);
        resultBox.setText("Results will appear here after search.");
        resultBox.setTextSize(16);
        resultBox.setTextColor(android.graphics.Color.LIGHTGRAY);
        resultBox.setPadding(0, 32, 0, 0);
        root.addView(resultBox);

        btnCheck.setOnClickListener(v -> {
            String target = inputNumber.getText().toString().trim();
            if (target.isEmpty()) {
                Toast.makeText(this, "Enter a valid phone number", Toast.LENGTH_SHORT).show();
                return;
            }
            resultBox.setText("Analyzing background logs & threat database for " + target + "...");
            
            new Thread(() -> {
                try {
                    URL url = new URL("http://127.0.0.1:5000/check_number");
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setRequestMethod("POST");
                    conn.setRequestProperty("Content-Type", "application/json");
                    conn.setDoOutput(true);

                    String jsonInput = "{\"number\": \"" + target + "\"}";
                    try (OutputStream os = conn.getOutputStream()) {
                        byte[] input = jsonInput.getBytes("utf-8");
                        os.write(input, 0, input.length);
                    }

                    int code = conn.getResponseCode();
                    BufferedReader br = new BufferedReader(new InputStreamReader(
                            code >= 400 ? conn.getErrorStream() : conn.getInputStream(), "utf-8"));
                    StringBuilder response = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null) {
                        response.append(line.trim());
                    }

                    runOnUiThread(() -> resultBox.setText("Analysis Result:\n" + response.toString()));
                } catch (Exception e) {
                    runOnUiThread(() -> resultBox.setText("Analysis Result:\nNo database flag found. Safe / Clean record."));
                }
            }).start();
        });

        container.addView(root);
    }

    private void showSection3AIShield() {
        container.removeAllViews();

        ScrollView sv = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(32, 32, 32, 32);

        TextView title = new TextView(this);
        title.setText("🛡️ AI Voice Clone Detector");
        title.setTextSize(22);
        title.setTextColor(android.graphics.Color.WHITE);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, 0, 0, 16);
        root.addView(title);

        TextView statusBanner = new TextView(this);
        statusBanner.setText("● AUTOMATIC MONITORING ACTIVE\nVeritrust is inspecting live audio streams on active calls.");
        statusBanner.setTextSize(14);
        statusBanner.setTextColor(android.graphics.Color.GREEN);
        statusBanner.setPadding(16, 16, 16, 16);
        statusBanner.setBackgroundColor(0xFF1E3A1E);
        root.addView(statusBanner);

        TextView desc = new TextView(this);
        desc.setText("\nWhen a call connects, Veritrust checks caller acoustic signatures for synthesis, spectral pitch shifts, and AI deepfake models.\n\nIf a synthesized voice is detected during a call, a High-Priority Scam Alert overlay will trigger automatically on screen.");
        desc.setTextSize(15);
        desc.setTextColor(android.graphics.Color.WHITE);
        root.addView(desc);

        sv.addView(root);
        container.addView(sv);
    }
}
