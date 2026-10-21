package com.veritrust.shield;

import android.telecom.Call;
import android.telecom.InCallService;
import android.util.Log;

public class VeritrustCallService extends InCallService {
    private static final String TAG = "VeritrustCallService";

    @Override
    public void onCallAdded(Call call) {
        super.onCallAdded(call);
        
        if (call.getDetails() != null && call.getDetails().getHandle() != null) {
            String phoneNumber = call.getDetails().getHandle().getSchemeSpecificPart();
            Log.d(TAG, "Incoming call intercepted from: " + phoneNumber);
            
            // Here you can trigger your Flask backend check or display your floating alert overlay
        }
    }

    @Override
    public void onCallRemoved(Call call) {
        super.onCallRemoved(call);
        Log.d(TAG, "Call ended.");
    }
}
