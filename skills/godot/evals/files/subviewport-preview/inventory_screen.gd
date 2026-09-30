extends Control
## Inventory screen. Opened on top of the running level (the level stays loaded underneath
## and keeps rendering); shows the equipped character model turning in a 3D preview panel.

@onready var _model_root: Node3D = $PreviewFrame/PreviewViewport/ModelRoot


func show_character(model_scene: PackedScene) -> void:
	for child in _model_root.get_children():
		child.queue_free()
	var model: Node3D = model_scene.instantiate()
	_model_root.add_child(model)


func _process(delta: float) -> void:
	_model_root.rotate_y(delta * 0.6)
