package com.motorica.games.stk;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class RuStoreLauncherActivity extends Activity
{
    @Override
    protected void onCreate(Bundle instance)
    {
        super.onCreate(instance);

        startActivity(new Intent(this, SuperTuxKartActivity.class));
        finish();
    }
}
