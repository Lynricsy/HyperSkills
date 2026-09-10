<?php

namespace App\Services;

use App\Jobs\SyncOrderToWarehouse;
use App\Models\Order;
use Illuminate\Support\Facades\DB;

class CheckoutService
{
    public function place(array $data): Order
    {
        return DB::transaction(function () use ($data) {
            $order = Order::create($data);

            foreach ($data['lines'] as $line) {
                $order->lines()->create($line);
            }

            SyncOrderToWarehouse::dispatch($order);

            event(new \App\Events\OrderPlaced($order));

            return $order;
        });
    }
}
