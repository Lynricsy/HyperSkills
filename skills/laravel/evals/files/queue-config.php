<?php

// config/queue.php (excerpt)

return [
    'default' => env('QUEUE_CONNECTION', 'redis'),

    'connections' => [
        'redis' => [
            'driver' => 'redis',
            'connection' => 'default',
            'queue' => 'default',
            'retry_after' => 90,
            'block_for' => null,
        ],
    ],

    'failed' => [
        'driver' => 'database-uuids',
        'database' => 'mysql',
        'table' => 'failed_jobs',
    ],
];

// Deployment runs: php artisan queue:work redis --tries=3 --timeout=300
