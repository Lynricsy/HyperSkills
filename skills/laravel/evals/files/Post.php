<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;

class Post extends Model
{
    protected $guarded = [];

    protected $casts = [
        'meta' => 'array',
    ];

    public function author()
    {
        return $this->belongsTo(User::class, 'user_id');
    }

    public function comments()
    {
        return $this->hasMany(Comment::class);
    }

    public function scopePublished($query)
    {
        return $query->whereNotNull('published_at');
    }

    public function scopeForCurrentTeam($query)
    {
        return $query->where('team_id', auth()->user()->team_id);
    }

    public function publish(): void
    {
        $this->update(['published_at' => now()]);

        $this->author->notify(new \App\Notifications\PostPublished($this));

        \App\Jobs\WarmPostCache::dispatch($this);
    }
}
