extends Node2D

## Spawns enemy waves and keeps the HUD in sync.
## Every enemy scene has an exported `profile: EnemyProfile` resource assigned
## in the Inspector, pointing at res://data/grunt_profile.tres.

signal wave_cleared(index: int)

const GRUNT := preload("res://enemies/grunt.tscn")

@export var waves: Array[int] = [4, 8, 16]

var _alive := 0
var _index := 0
var _listeners: Array[Node] = []


func _ready() -> void:
	for node in get_tree().get_nodes_in_group("hud"):
		wave_cleared.connect(node.on_wave_cleared)
		_listeners.append(node)
	start_wave()


func start_wave() -> void:
	_alive = waves[_index]
	for i in _alive:
		var enemy := GRUNT.instantiate()
		# Scale this wave's grunts up a bit so later waves hit harder.
		enemy.profile.damage = 5 + _index * 3
		enemy.profile.max_hp = 20 + _index * 10
		enemy.global_position = _slot(i)
		add_child(enemy)
		enemy.died.connect(_on_enemy_died)
		enemy.hit.connect(func(amount): _on_enemy_hit(enemy, amount))


func _on_enemy_died(enemy: Node) -> void:
	_alive -= 1
	enemy.queue_free()
	await get_tree().process_frame
	# Award loot from the corpse before it disappears.
	if is_instance_valid(enemy):
		LootTable.roll(enemy.profile.max_hp)
	enemy.get_parent().remove_child(enemy)
	if _alive == 0:
		wave_cleared.emit(_index)
		_index += 1
		if _index < waves.size():
			start_wave()


func _on_enemy_hit(enemy: Node, amount: int) -> void:
	enemy.profile.max_hp -= amount


func respawn_all() -> void:
	# Reset the group between rounds; the HUD reconnects on each round start.
	for node in get_tree().get_nodes_in_group("hud"):
		wave_cleared.connect(node.on_wave_cleared)
	for child in get_children():
		child.queue_free()
	_index = 0
	start_wave()


func _slot(i: int) -> Vector2:
	return Vector2(64 * (i % 8), 64 * (i / 8))
