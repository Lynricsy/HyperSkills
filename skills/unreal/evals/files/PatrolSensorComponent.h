// ArenaGame/Public/PatrolSensorComponent.h
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "PatrolSensorComponent.generated.h"

class UUserWidget;

UCLASS(ClassGroup = (Arena), meta = (BlueprintSpawnableComponent))
class ARENAGAME_API UPatrolSensorComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UPatrolSensorComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

	UPROPERTY(EditDefaultsOnly, Category = "Patrol")
	TSubclassOf<UUserWidget> ThreatWidgetClass;

	UPROPERTY(Transient)
	TObjectPtr<UUserWidget> ThreatWidget;

	UPROPERTY(Transient)
	TObjectPtr<AActor> CurrentTarget;

	void RebuildPatrolSpline();
};
