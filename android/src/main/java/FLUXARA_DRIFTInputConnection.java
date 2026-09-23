package com.motorica.games.fluxara_drift;

import com.motorica.games.fluxara_drift.FLUXARA_DRIFTEditText;

import android.view.inputmethod.InputConnection;
import android.view.inputmethod.InputConnectionWrapper;

public class FLUXARA_DRIFTInputConnection extends InputConnectionWrapper
{
    /* The global edittext which will be "copied" to the current focused FLUXARA_DRIFT
     * box. */
    final private FLUXARA_DRIFTEditText m_fluxara_drift_edittext;

    // ------------------------------------------------------------------------
    public FLUXARA_DRIFTInputConnection(InputConnection target, FLUXARA_DRIFTEditText fluxara_drift_edittext)
    {
        super(target, true/*mutable*/);
        m_fluxara_drift_edittext = fluxara_drift_edittext;
    }
    // ------------------------------------------------------------------------
    @Override
    public boolean setComposingText(CharSequence text, int new_cursor_position)
    {
        boolean ret = super.setComposingText(text, new_cursor_position);
        String composing_text = text.toString();
        String new_text = m_fluxara_drift_edittext.getText().toString();
        int composing_start = 0;
        int composing_end = 0;
        // Test last char
        if (!composing_text.isEmpty() && !new_text.isEmpty() &&
            composing_text.charAt(composing_text.length() - 1) ==
            new_text.charAt(new_text.length() - 1))
        {
            composing_start = new_text.length() - composing_text.length();
            composing_end = composing_start + composing_text.length();
        }
        m_fluxara_drift_edittext.setComposingRegion(composing_start, composing_end);
        m_fluxara_drift_edittext.updateFLUXARA_DRIFTEditBox();
        return ret;
    }
    // ------------------------------------------------------------------------
    @Override
    public boolean finishComposingText()
    {
        m_fluxara_drift_edittext.setComposingRegion(0, 0);
        m_fluxara_drift_edittext.updateFLUXARA_DRIFTEditBox();
        return super.finishComposingText();
    }
    // ------------------------------------------------------------------------
    @Override
    public boolean setComposingRegion(int start, int end)
    {
        m_fluxara_drift_edittext.setComposingRegion(start, end);
        m_fluxara_drift_edittext.updateFLUXARA_DRIFTEditBox();
        return super.setComposingRegion(start, end);
    }
    // ------------------------------------------------------------------------
    @Override
    public boolean commitText(CharSequence text, int new_cursor_position)
    {
        // Usually only a single character, so dismiss composing region
        boolean ret = super.commitText(text, new_cursor_position);
        m_fluxara_drift_edittext.setComposingRegion(0, 0);
        m_fluxara_drift_edittext.updateFLUXARA_DRIFTEditBox();
        return ret;
    }

}
