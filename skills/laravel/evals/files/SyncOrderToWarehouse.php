<?php

namespace App\Jobs;

use App\Models\Order;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Throwable;

class SyncOrderToWarehouse implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public $tries = 5;

    public $timeout = 300;

    public $attemptLog = [];

    public function __construct(public Order $order)
    {
    }

    public function handle(): void
    {
        $this->attemptLog[] = now()->toIso8601String();

        $response = Http::post('https://warehouse.example.com/v1/shipments', [
            'order_id' => $this->order->id,
            'lines' => $this->order->lines->map->toArray(),
        ]);

        $this->order->update([
            'warehouse_reference' => $response->json('reference'),
            'status' => 'submitted',
        ]);

        $this->order->customer->notify(new \App\Notifications\OrderSubmitted($this->order));
    }

    public function failed(?Throwable $e): void
    {
        Log::error('warehouse sync failed after '.count($this->attemptLog).' attempts', [
            'order' => $this->order->id,
        ]);
    }
}
