<?php

namespace App\Http\Controllers;

use App\Models\Subscriber;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class NewsletterController extends Controller
{
    /**
     * GET /newsletter/unsubscribe?email=...&signature=...
     *
     * Linked from the footer of every newsletter (see NewsletterMail::footerLinks()).
     */
    public function unsubscribe(Request $request): View
    {
        $subscriber = Subscriber::where('email', $request->input('email'))->firstOrFail();

        $subscriber->update(['unsubscribed_at' => now()]);

        return view('newsletter.unsubscribed', ['email' => $subscriber->email]);
    }

    /**
     * POST /newsletter/preferences?email=...&expires=...&signature=...
     *
     * The preferences form posts back to the signed URL it was rendered from.
     */
    public function updatePreferences(Request $request): RedirectResponse
    {
        $data = $request->validate([
            'email' => ['required', 'email'],
            'frequency' => ['required', 'in:daily,weekly,monthly,never'],
            'topics' => ['array'],
            'topics.*' => ['string', 'in:product,events,offers'],
        ]);

        Subscriber::where('email', $data['email'])->update([
            'frequency' => $data['frequency'],
            'topics' => $data['topics'] ?? [],
        ]);

        return back()->with('status', 'Preferences saved.');
    }
}
