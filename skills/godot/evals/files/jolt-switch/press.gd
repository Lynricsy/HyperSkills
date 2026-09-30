extends RigidBody3D
## Hydraulic press in the vault puzzle. Code drives it down as a kinematic body; when it
## touches the StaticBody3D named "Anvil" it stops and tells the puzzle it was pressed.

signal pressed

@export var speed := 0.6


func _ready() -> void:
	freeze = true
	freeze_mode = RigidBody3D.FREEZE_MODE_KINEMATIC
	contact_monitor = true
	max_contacts_reported = 4
	body_entered.connect(_on_body_entered)


func _physics_process(delta: float) -> void:
	global_position.y -= speed * delta


func _on_body_entered(body: Node) -> void:
	if body.name == "Anvil":
		speed = 0.0
		pressed.emit()
