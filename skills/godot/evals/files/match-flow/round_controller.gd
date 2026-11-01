extends Node

## Lives in res://levels/arena.tscn as "RoundController" (group "round_controller").
## Not an autoload: it is part of the level scene.

const RESULTS := "res://ui/results.tscn"


func end_round(loser_peer: int) -> void:
	get_tree().change_scene_to_file(RESULTS)
	# Hand the result to the results screen we just switched to.
	var results := get_tree().current_scene as ResultsScreen
	results.show_loser(loser_peer)
