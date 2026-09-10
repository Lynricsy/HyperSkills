<?php

namespace App\Http\Controllers;

use App\Models\Post;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class PostController extends Controller
{
    public function index(Request $request)
    {
        $posts = Post::all();

        $rows = [];

        foreach ($posts as $post) {
            $rows[] = [
                'title' => $post->title,
                'author' => $post->author->name,
                'author_country' => $post->author->profile->country,
                'comments' => $post->comments->count(),
                'published' => $post->published_at ? date('Y-m-d', strtotime($post->published_at)) : null,
            ];
        }

        return view('posts.index', ['rows' => $rows]);
    }

    public function search(Request $request)
    {
        $term = $request->input('q');
        $direction = $request->input('dir', 'asc');

        $posts = DB::select("SELECT * FROM posts WHERE title LIKE '%{$term}%' ORDER BY created_at {$direction}");

        return view('posts.search', compact('posts'));
    }

    public function store(Request $request)
    {
        $request->validate([
            'title' => 'required|max:255',
            'body' => 'required',
            'user_id' => 'required|integer',
        ]);

        $post = Post::create($request->all());

        return redirect('/posts/'.$post->id);
    }

    public function update(Request $request, $id)
    {
        $post = Post::findOrFail($id);

        $post->update($request->all());

        return redirect('/posts/'.$post->id);
    }

    public function export()
    {
        $posts = Post::all();

        foreach ($posts as $post) {
            $post->update(['exported_at' => now()]);
        }

        return response()->json(['count' => $posts->count()]);
    }
}
