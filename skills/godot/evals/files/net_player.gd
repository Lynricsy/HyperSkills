extends CharacterBody2D

## Networked avatar. One instance per connected peer, spawned by the host with
## `add_child(avatar)` from net.gd when `peer_connected` fires.
## The server is peer 1 and also plays.

@export var speed := 220.0

var hp := 100
var score := 0


func _ready() -> void:
	# Every peer runs this script, so everyone owns their own avatar.
	set_multiplayer_authority(multiplayer.get_unique_id())


func _physics_process(_delta: float) -> void:
	velocity = Input.get_vector("left", "right", "up", "down") * speed
	move_and_slide()
	push_state.rpc(global_position, velocity, hp)


@rpc("any_peer", "unreliable")
func push_state(pos: Vector2, vel: Vector2, health: int) -> void:
	global_position = pos
	velocity = vel
	hp = health


@rpc("any_peer")
func apply_damage(amount: int) -> void:
	hp -= amount
	if hp <= 0:
		die.rpc()


@rpc("any_peer")
func die() -> void:
	score -= 1
	queue_free()


@rpc("any_peer")
func award_kill(victim: Node) -> void:
	# Tell everyone who scored, and hand over the victim node so the HUD can
	# show its name.
	score += 1
	Net.hud.show_kill(victim)


func fire() -> void:
	if not is_multiplayer_authority():
		return
	var target := _pick_target()
	if target:
		target.apply_damage.rpc_id(target.get_multiplayer_authority(), 25)
		award_kill.rpc(target)


func _pick_target() -> Node:
	for peer in get_parent().get_children():
		if peer != self:
			return peer
	return null
