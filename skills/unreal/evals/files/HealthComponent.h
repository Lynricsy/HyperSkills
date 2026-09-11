// ArenaGame/Public/HealthComponent.h
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "HealthComponent.generated.h"

USTRUCT(BlueprintType)
struct FDamageRecord
{
	GENERATED_BODY()

	UPROPERTY()
	float Amount = 0.f;

	UPROPERTY()
	float TimeSeconds = 0.f;
};

UCLASS(ClassGroup = (Arena), meta = (BlueprintSpawnableComponent))
class ARENAGAME_API UHealthComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UHealthComponent();

	UPROPERTY(ReplicatedUsing = OnRep_Health, BlueprintReadOnly, Category = "Health")
	float Health = 100.f;

	UPROPERTY(EditDefaultsOnly, Category = "Health")
	TObjectPtr<USoundBase> HitSound;

	UPROPERTY(Replicated, BlueprintReadOnly, Category = "Health")
	TArray<FDamageRecord> DamageLog;

	UFUNCTION()
	void OnRep_Health();

	// Called from the local player's weapon trace when it hits something.
	UFUNCTION(Client, Reliable)
	void ServerApplyDamage(float Amount);

	UFUNCTION(NetMulticast, Reliable)
	void MulticastPlayHitFx(FVector Location);

	// Called by the HUD when the local player takes falling damage.
	void LocalApplyDamage(float Amount);
};
