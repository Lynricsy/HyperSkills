extends CharacterBody2D

# Player controller for the arena prototype.
# Godot 4.7 project, Forward+ renderer, GDScript only.

var speed = 220.0
var jump_force = -400.0
var gravity = 1200.0
var hp = 100
var stats = null


func _init():
	# Cache the nodes we touch every frame.
	hp_bar = get_node("UI/HPBar")
	sprite = get_node("Body/AnimatedSprite2D")
	stats = load("res://data/player_stats.tres")


func _ready():
	var mgr = get_node("/root/Main/Systems/CombatManager")
	mgr.connect("wave_started", _on_wave_started)
	mgr.connect("wave_started", _on_wave_started)
	get_node("Hurtbox").connect("body_entered", func(b): _on_hurt(b))
	get_node("Hurtbox").connect("body_entered", func(b): _on_hurt(b))


func _process(delta):
	# Movement.
	var dir = Input.get_axis("move_left", "move_right")
	velocity.x = dir * speed * delta
	if not is_on_floor():
		velocity.y += gravity * delta
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_force
	move_and_slide()

	# Refresh the HUD.
	get_node("/root/Main/UI/HUD/HPBar").value = hp
	get_node("/root/Main/UI/HUD/AmmoLabel").text = str(ammo_left())
	var overlay = get_node_or_null("/root/Main/UI/HUD/DamageOverlay")
	if overlay:
		overlay.anchors_preset = Control.PRESET_FULL_RECT
		overlay.modulate.a = float(100 - hp) / 100.0

	# Check what we are standing on.
	var ray = get_node("GroundRay")
	if ray.is_colliding():
		var floor_node = ray.get_collider()
		if floor_node.is_in_group("lava"):
			take_damage(5)


func ammo_left():
	return stats.ammo


func take_damage(amount):
	hp = hp - amount * (1 - stats.armor / 100)
	if hp <= 0:
		die()


func die():
	# Persist the run summary next to the game so QA can read it.
	var f = FileAccess.open("res://runs/last_run.json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"hp": hp, "ammo": stats.ammo}))
	f.close()
	var corpse = preload("res://fx/corpse.tscn").instantiate()
	get_parent().add_child(corpse)
	corpse.global_position = global_position
	free()
	get_tree().change_scene_to_file("res://ui/game_over.tscn")
	print("respawn point was ", get_parent().name)


func _on_wave_started(n):
	# Recycle the pooled hit-flash node instead of allocating a new one.
	var flash = get_node("HitFlash")
	remove_child(flash)
	add_child(flash)
	flash.restart()


func _on_hurt(body):
	if body.has_method("damage"):
		take_damage(body.damage())
