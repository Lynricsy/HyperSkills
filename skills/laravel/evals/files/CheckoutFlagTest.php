<?php

use App\Models\Order;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\Facades\Http;

uses(RefreshDatabase::class);

beforeEach(function () {
    $this->user = User::factory()->create([
        'email_verified_at' => null,
    ]);

    $this->order = Order::factory()->create([
        'user_id' => $this->user->id,
        'status' => 'draft',
    ]);

    Http::fake();
});

it('works', function () {
    Event::fake();

    Carbon::setTestNow('2026-01-01 09:00:00');

    $response = $this->actingAs($this->user)->post('/checkout', [
        'order_id' => $this->order->id,
    ]);

    $response->assertStatus(200);

    expect(true)->toBeTrue();
});

it('shows the new checkout to users in the rollout', function () {
    $response = $this->actingAs($this->user)->get('/checkout');

    // Flaky: passes locally, fails about one run in three on CI.
    $response->assertSee('Express checkout');
});

it('rejects checkout for another team', function () {
    $other = User::factory()->create();

    $this->actingAs($other)
        ->post('/checkout', ['order_id' => $this->order->id])
        ->assertStatus(403);
});
