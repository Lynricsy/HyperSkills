// ArenaGame/ArenaGame.Build.cs
using UnrealBuildTool;

public class ArenaGame : ModuleRules
{
	public ArenaGame(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"UMG",
			"Slate",
			"SlateCore",
			"UnrealEd",
			"AssetTools",
			"Niagara",
			"GameplayTags"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
		});
	}
}
