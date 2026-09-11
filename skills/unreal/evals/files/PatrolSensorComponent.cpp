// ArenaGame/Private/PatrolSensorComponent.cpp
#include "PatrolSensorComponent.h"

#include "Blueprint/UserWidget.h"
#include "Components/TextBlock.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"

UPatrolSensorComponent::UPatrolSensorComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UPatrolSensorComponent::BeginPlay()
{
	Super::BeginPlay();

	ThreatWidget = CreateWidget<UUserWidget>(GetWorld(), ThreatWidgetClass);
	ThreatWidget->AddToViewport();
}

void UPatrolSensorComponent::TickComponent(float DeltaTime, ELevelTick TickType,
	FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// Find every possible target, every frame.
	TArray<AActor*> Found;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), ACharacter::StaticClass(), Found);

	AActor* Nearest = nullptr;
	float NearestDistance = TNumericLimits<float>::Max();

	for (AActor* Candidate : Found)
	{
		ACharacter* AsCharacter = Cast<ACharacter>(Candidate);
		if (AsCharacter == nullptr)
		{
			continue;
		}

		// Line of sight against complex collision on the skeletal mesh.
		FHitResult Hit;
		FCollisionQueryParams Params;
		Params.bTraceComplex = true;
		GetWorld()->LineTraceSingleByChannel(
			Hit,
			GetOwner()->GetActorLocation(),
			AsCharacter->GetActorLocation(),
			ECC_Visibility,
			Params);

		const float Distance = FVector::Dist(GetOwner()->GetActorLocation(),
			AsCharacter->GetActorLocation());
		if (!Hit.bBlockingHit && Distance < NearestDistance)
		{
			NearestDistance = Distance;
			Nearest = AsCharacter;
		}
	}

	CurrentTarget = Nearest;

	// Push the HUD text every frame.
	if (UTextBlock* Label = Cast<UTextBlock>(ThreatWidget->GetWidgetFromName(TEXT("ThreatLabel"))))
	{
		Label->SetText(FText::FromString(
			FString::Printf(TEXT("Threat: %s (%.0f m)"),
				Nearest ? *Nearest->GetName() : TEXT("none"),
				NearestDistance / 100.f)));
	}

	// Keep the patrol route in sync with the navmesh version of the path.
	RebuildPatrolSpline();
}
