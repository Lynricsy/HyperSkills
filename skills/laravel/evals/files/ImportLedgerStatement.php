<?php

namespace App\Jobs;

use App\Models\LedgerEntry;
use App\Models\Statement;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Queue\Attributes\Backoff;
use Illuminate\Queue\Attributes\MaxExceptions;
use Illuminate\Queue\Attributes\Timeout;
use Illuminate\Queue\Attributes\Tries;
use Illuminate\Queue\Middleware\WithoutOverlapping;
use Illuminate\Support\Facades\Storage;

#[Tries(25)]            // imports for one account queue up behind each other; lock misses release the job
#[MaxExceptions(3)]     // but a statement that really fails should give up after three bad attempts
#[Backoff(30)]
#[Timeout(600)]
class ImportLedgerStatement implements ShouldQueue
{
    use Queueable;

    public function __construct(public Statement $statement) {}

    public function middleware(): array
    {
        return [
            (new WithoutOverlapping($this->statement->account_id))
                ->releaseAfter(60)
                ->expireAfter(900),
        ];
    }

    public function handle(): void
    {
        $rows = array_map('str_getcsv', file(Storage::path($this->statement->path)));
        $header = array_shift($rows);

        foreach ($rows as $row) {
            $line = array_combine($header, $row);

            LedgerEntry::create([
                'statement_id' => $this->statement->id,
                'account_id' => $this->statement->account_id,
                'booked_on' => $line['booked_on'],
                'amount_cents' => (int) round(((float) $line['amount']) * 100),
                'reference' => $line['reference'],
            ]);
        }

        $this->statement->update(['imported_at' => now()]);
    }
}
