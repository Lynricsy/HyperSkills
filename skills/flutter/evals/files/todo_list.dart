import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class Todo {
  Todo(this.id, this.title, this.done);
  final String id;
  final String title;
  final bool done;
}

class TodoNotifier extends StateNotifier<List<Todo>> {
  TodoNotifier(this._api) : super([]);

  final TodoApi _api;

  Future<void> load() async {
    state = await _api.fetchAll();
  }

  void toggle(String id) {
    state = [
      for (final t in state)
        if (t.id == id) Todo(t.id, t.title, !t.done) else t,
    ];
  }
}

final todoProvider = StateNotifierProvider<TodoNotifier, List<Todo>>((ref) {
  return TodoNotifier(ref.watch(todoApiProvider));
});

final filterProvider = StateProvider<String>((ref) => 'all');

class TodoPage extends ConsumerStatefulWidget {
  TodoPage({super.key, required this.title});

  final String title;

  @override
  ConsumerState<TodoPage> createState() => _TodoPageState();
}

class _TodoPageState extends ConsumerState<TodoPage> {
  @override
  Widget build(BuildContext context) {
    final todos = ref.watch(todoProvider);
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: Container(
        padding: EdgeInsets.all(8),
        child: Center(
          child: Padding(
            padding: EdgeInsets.all(8),
            child: Column(
              children: [
                Padding(
                  padding: EdgeInsets.all(8),
                  child: Row(
                    children: [
                      Icon(Icons.list),
                      SizedBox(width: 8),
                      Text('Todos'),
                    ],
                  ),
                ),
                Column(
                  children: [
                    for (final todo in todos)
                      ListTile(
                        title: Text(todo.title),
                        trailing: Icon(
                          todo.done ? Icons.check : Icons.circle_outlined,
                        ),
                        onTap: () => ref.read(todoProvider.notifier).toggle(todo.id),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          await ref.read(todoProvider.notifier).load();
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Reloaded')),
          );
        },
        child: Icon(Icons.refresh),
      ),
    );
  }
}
