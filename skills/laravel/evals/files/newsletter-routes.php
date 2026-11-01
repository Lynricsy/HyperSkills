<?php

use App\Http\Controllers\NewsletterController;
use Illuminate\Support\Facades\Route;

Route::get('/newsletter/unsubscribe', [NewsletterController::class, 'unsubscribe'])
    ->name('newsletter.unsubscribe')
    ->middleware('signed');

Route::get('/newsletter/preferences', [NewsletterController::class, 'editPreferences'])
    ->name('newsletter.preferences')
    ->middleware('signed');

Route::post('/newsletter/preferences', [NewsletterController::class, 'updatePreferences'])
    ->name('newsletter.preferences.update')
    ->middleware('signed');

// In NewsletterMail::footerLinks():
//   URL::signedRoute('newsletter.unsubscribe', ['email' => $subscriber->email]);
//   URL::temporarySignedRoute('newsletter.preferences', now()->addDays(14), ['email' => $subscriber->email]);
//   URL::temporarySignedRoute('newsletter.preferences.update', now()->addDays(14), ['email' => $subscriber->email]);
