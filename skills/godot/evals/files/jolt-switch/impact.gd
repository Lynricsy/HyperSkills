extends Node3D
## Bullet impacts. Picks the impact sound and decal from the surface of the triangle hit.
## The vault's collision is a single ConcavePolygonShape3D baked from vault_collision.obj;
## tools/bake_surfaces.gd writes one surface id per triangle into surface_ids, in the same
## order as the shape's faces: 0 concrete, 1 wood, 2 glass, 3 metal.

const SURFACE_NAMES := ["concrete", "wood", "glass", "metal"]

@export var surface_ids: PackedByteArray
@export var impact_sounds: Array[AudioStream] = []
@export var impact_decals: Array[PackedScene] = []

@onready var _player: AudioStreamPlayer3D = $ImpactPlayer


func fire(from: Vector3, to: Vector3) -> void:
	var query := PhysicsRayQueryParameters3D.create(from, to)
	query.collision_mask = 0b1
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		return
	var surface: int = surface_ids[hit.face_index]
	_spawn_impact(surface, hit.position, hit.normal)


func _spawn_impact(surface: int, at: Vector3, normal: Vector3) -> void:
	_player.global_position = at
	_player.stream = impact_sounds[surface]
	_player.play()
	var decal: Node3D = impact_decals[surface].instantiate()
	get_tree().current_scene.add_child(decal)
	decal.global_position = at
	decal.look_at(at + normal, Vector3.UP if absf(normal.y) < 0.99 else Vector3.RIGHT)
