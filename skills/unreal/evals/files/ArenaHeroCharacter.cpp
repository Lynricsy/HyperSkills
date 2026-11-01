// ArenaHeroCharacter.cpp - UE 5.8, listen-server multiplayer.
// Input works for the listening host, but on remote clients the character
// does not respond to any input.
#include "ArenaHeroCharacter.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputMappingContext.h"
#include "InputTriggers.h"

void AArenaHeroCharacter::BeginPlay()
{
    Super::BeginPlay();

    if (APlayerController* PC = Cast<APlayerController>(GetController()))
    {
        if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
                ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
        {
            Subsystem->AddMappingContext(DefaultMappingContext, 0);
        }
    }
}

void AArenaHeroCharacter::SetupPlayerInputComponent(UInputComponent* InputComponent)
{
    Super::SetupPlayerInputComponent(InputComponent);

    if (UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(InputComponent))
    {
        EIC->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AArenaHeroCharacter::Move);
        EIC->BindAction(LookAction, ETriggerEvent::Triggered, this, &AArenaHeroCharacter::Look);
        // IA_DashCombo uses a UInputTriggerCombo (Dodge -> Dodge -> Forward) set up in IMC_Default.
        EIC->BindAction(DashComboAction, ETriggerEvent::Triggered, this, &AArenaHeroCharacter::Dash);
    }
}

// Planned "Rebind controls" menu: copy IMC_Default, edit the key in the copy's
// Mappings array at runtime and re-add it with a higher priority.
void AArenaHeroCharacter::RebindJump(const FKey& NewKey)
{
    UInputMappingContext* Copy = DuplicateObject(DefaultMappingContext, this);
    for (FEnhancedActionKeyMapping& Mapping : const_cast<TArray<FEnhancedActionKeyMapping>&>(Copy->GetMappings()))
    {
        if (Mapping.Action == JumpAction)
        {
            Mapping.Key = NewKey;
        }
    }
    if (APlayerController* PC = Cast<APlayerController>(GetController()))
    {
        ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer())
            ->AddMappingContext(Copy, 10);
    }
}
