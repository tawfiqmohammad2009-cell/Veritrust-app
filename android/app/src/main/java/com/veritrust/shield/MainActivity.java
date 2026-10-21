package com.veritrust.shield;

import android.app.Activity;
import android.app.role.RoleManager;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {

    private FrameLayout container;

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
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);

        TextView tv = new TextView(this);
        tv.setText("Section 1: Dialer & Calls\n[Keypad, Logs, & Messaging]");
        tv.setTextColor(android.graphics.Color.WHITE);
        tv.setGravity(Gravity.CENTER);
        layout.addView(tv);

        container.removeAllViews();
        container.addView(layout);
    }

    private void showSection2Lookup() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);

        TextView tv = new TextView(this);
        tv.setText("Section 2: Number Lookup\n[Identify & Verify Numbers]");
        tv.setTextColor(android.graphics.Color.WHITE);
        tv.setGravity(Gravity.CENTER);
        layout.addView(tv);

        container.removeAllViews();
        container.addView(layout);
    }

    private void showSection3AIShield() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);

        TextView tv = new TextView(this);
        tv.setText("Section 3: AI Voice Clone Shield\n[Real-time Call Analysis]");
        tv.setTextColor(android.graphics.Color.WHITE);
        tv.setGravity(Gravity.CENTER);
        layout.addView(tv);

        container.removeAllViews();
        container.addView(layout);
    }
}
