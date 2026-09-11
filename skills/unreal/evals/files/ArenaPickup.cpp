// ArenaGame/Private/ArenaPickup.cpp
#include "ArenaPickup.h"

#include "Async/Async.h"
#include "ArenaPickupData.h"

UArenaPickup::UArenaPickup()
{
	Mesh = TStrongObjectPtr<UStaticMeshComponent>(NewObject<UStaticMeshComponent>(this));

	CachedData = NewObject<UArenaPickupData>(GetTransientPackage());
	CachedData->AddToRoot();

	SharedData = MakeShareable(CachedData);
}

void UArenaPickup::Collect()
{
	if (CachedData != nullptr)
	{
		CachedData->ApplyTo(GetWorld());
		delete CachedData;
		CachedData = nullptr;
	}

	Destroy();
}

void UArenaPickup::PreloadOnWorkerThread()
{
	Async(EAsyncExecution::ThreadPool, [this]()
	{
		// Touch the asset so the first Collect() does not hitch.
		Loaded->Warm();
	});
}
