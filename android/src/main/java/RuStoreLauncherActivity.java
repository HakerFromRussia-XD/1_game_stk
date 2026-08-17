package com.motorica.games.stk;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;

public class RuStoreLauncherActivity extends Activity
{
    @Override
    protected void onCreate(Bundle instance)
    {
        super.onCreate(instance);

        getPackageManager().setComponentEnabledSetting(
            new ComponentName(this, RuStoreLauncherActivity.class),
            PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
            PackageManager.DONT_KILL_APP);

        startActivity(new Intent(this, SuperTuxKartActivity.class));
        finish();
    }
}
