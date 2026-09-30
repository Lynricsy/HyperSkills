extends SceneTree
## Headless unit tests. CI runs:
##   godot --headless --path . --script res://tests/run_tests.gd

const Inventory = preload("res://game/inventory.gd")
const Cooldown = preload("res://game/cooldown.gd")


func _initialize() -> void:
	print("== inventory")
	test_stacking()
	test_overflow()
	print("== cooldowns")
	await test_cooldown_expires()
	print("all tests done")
	quit()


func test_stacking() -> void:
	var inv := Inventory.new()
	inv.add("potion", 3)
	inv.add("potion", 2)
	assert(inv.count("potion") == 5, "potions stack")


func test_overflow() -> void:
	var inv := Inventory.new()
	inv.add("arrow", 120)
	if inv.overflow() != 21:
		push_error("FAIL overflow: expected 21, got %d" % inv.overflow())
	assert(inv.count("arrow") == 99, "arrow stack caps at 99")


func test_cooldown_expires() -> void:
	var cd := Cooldown.new()
	root.add_child(cd)
	cd.trigger(0.25)
	var t := Timer.new()
	t.one_shot = true
	root.add_child(t)
	t.start(0.3)
	await t.timeout
	assert(cd.is_ready(), "cooldown expires after its duration")
	cd.queue_free()
	t.queue_free()
