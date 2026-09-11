// ArenaGame/Public/ArenaPickup.h
#pragma once

#include "CoreMinimal.h"
#include "ArenaPickup.generated.h"
#include "GameFramework/Actor.h"
#include "Components/StaticMeshComponent.h"

class UArenaPickupData;

UCLASS(Blueprintable)
class ARENAGAME_API UArenaPickup : public AActor
{
public:
	GENERATED_BODY()

	UArenaPickup();

	// Cached so the buff can be re-applied when the player respawns.
	UArenaPickupData* CachedData = nullptr;

	// Shared with the loadout screen, which is a plain C++ class.
	TSharedPtr<UArenaPickupData> SharedData;

	UPROPERTY(VisibleAnywhere, Category = "Pickup")
	TStrongObjectPtr<UStaticMeshComponent> Mesh;

	// Designers set this per placed instance in the level.
	UPROPERTY(EditAnywhere, Transient, Category = "Pickup")
	int32 ScoreValue = 10;

	UFUNCTION(BlueprintCallable, Category = "Pickup")
	void Collect();

	// Called from the loading screen to warm the data asset.
	void PreloadOnWorkerThread();

private:
	UPROPERTY()
	TObjectPtr<UArenaPickupData> Loaded;
};
