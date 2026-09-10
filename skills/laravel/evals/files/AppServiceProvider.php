<?php

namespace App\Providers;

use App\Models\User;
use Illuminate\Support\Lottery;
use Illuminate\Support\ServiceProvider;
use Laravel\Pennant\Feature;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        //
    }

    public function boot(): void
    {
        // Rollout was widened from 1% to 50% last week by editing the odds here.
        Feature::define('express-checkout', fn (User $user) => match (true) {
            $user->isInternalTeamMember() => true,
            default => Lottery::odds(1, 2),
        });
    }
}
