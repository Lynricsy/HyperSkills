<?php

namespace App\Services;

use App\Models\Event;
use App\Models\Reservation;
use App\Models\User;
use Illuminate\Contracts\Cache\LockTimeoutException;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;

/**
 * Called from ReservationController@store. Laravel 13, CACHE_STORE=redis, 6 PHP-FPM hosts.
 */
class SeatReservationService
{
    public function reserve(Event $event, User $user, int $seats, string $paymentToken): Reservation
    {
        try {
            return Cache::lock('event-seats:'.$event->id, 5)->block(10, function () use ($event, $user, $seats, $paymentToken) {
                $event->refresh();

                if ($event->seats_remaining < $seats) {
                    throw new SoldOutException($event);
                }

                // Pre-authorise the card before we commit the seats.
                $authorisation = Http::withToken(config('services.payhub.key'))
                    ->connectTimeout(3)
                    ->timeout(20)
                    ->retry(2, 500)
                    ->post('https://api.payhub.example/v2/authorisations', [
                        'token' => $paymentToken,
                        'amount' => $event->price_cents * $seats,
                        'currency' => 'EUR',
                    ])
                    ->throw()
                    ->json();

                return DB::transaction(function () use ($event, $user, $seats, $authorisation) {
                    $event->update(['seats_remaining' => $event->seats_remaining - $seats]);

                    return Reservation::create([
                        'event_id' => $event->id,
                        'user_id' => $user->id,
                        'seats' => $seats,
                        'authorisation_id' => $authorisation['id'],
                    ]);
                });
            });
        } catch (LockTimeoutException) {
            throw new TryAgainLaterException();
        }
    }
}
