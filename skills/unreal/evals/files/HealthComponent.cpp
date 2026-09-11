// ArenaGame/Private/HealthComponent.cpp
#include "HealthComponent.h"

#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"

UHealthComponent::UHealthComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UHealthComponent::OnRep_Health()
{
	if (Health <= 0.f)
	{
		GetOwner()->SetActorHiddenInGame(true);
	}
}

void UHealthComponent::ServerApplyDamage_Implementation(float Amount)
{
	Health -= Amount;
	DamageLog.Add(FDamageRecord{Amount, GetWorld()->GetTimeSeconds()});

	MulticastPlayHitFx(GetOwner()->GetActorLocation());
}

void UHealthComponent::MulticastPlayHitFx_Implementation(FVector Location)
{
	UGameplayStatics::PlaySoundAtLocation(this, HitSound, Location);
}

void UHealthComponent::LocalApplyDamage(float Amount)
{
	Health -= Amount;
	OnRep_Health();
}
