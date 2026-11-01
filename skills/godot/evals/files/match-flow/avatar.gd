extends CharacterBody2D

## Player avatar for the team arena (Godot 4.7.2). The host spawns one per peer through
## a MultiplayerSpawner and names the node after the peer id. The MultiplayerSynchronizer
## child replicates position and velocity (replication mode: Always).

@export var speed := 220.0

var hp := 100
var stealthed := false

@onready var sync: MultiplayerSynchronizer = $MultiplayerSynchronizer


func _enter_tree() -> void:
	set_multiplayer_authority(name.to_int())


func _physics_process(_delta: float) -> void:
	if not is_multiplayer_authority():
		return
	velocity = Input.get_vector("left", "right", "up", "down") * speed
	move_and_slide()


## Called on every peer by the ability system (an RPC the server validated).
## While stealthed, the other team must not receive this avatar's position.
func set_stealth(on: bool, enemy_peers: Array[int]) -> void:
	stealthed = on
	for peer in enemy_peers:
		sync.set_visibility_for(peer, not on)


## Called on the server by the projectile when it hits this avatar.
func take_hit(amount: int) -> void:
	if multiplayer.is_server():
		apply_damage.rpc(amount)


# Results come from the server only.
@rpc("authority", "call_local", "reliable")
func apply_damage(amount: int) -> void:
	hp -= amount
	if hp <= 0 and multiplayer.is_server():
		get_tree().get_first_node_in_group("round_controller").end_round(name.to_int())
