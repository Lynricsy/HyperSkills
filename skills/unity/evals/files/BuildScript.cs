// Project path: Assets/CI/BuildScript.cs
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace CI
{
    public static class BuildScript
    {
        public static void BuildAndroid()
        {
            EditorUserBuildSettings.SwitchActiveBuildTarget(
                BuildTargetGroup.Android, BuildTarget.Android);

            var options = new BuildPlayerOptions
            {
                scenes = new[] { "Assets/Scenes/Boot.unity", "Assets/Scenes/Main.unity" },
                locationPathName = "artifacts/MyGame.apk",
                target = BuildTarget.Android,
                options = BuildOptions.Development | BuildOptions.AllowDebugging,
            };

            BuildPipeline.BuildPlayer(options);
            Debug.Log("BuildAndroid done");
        }
    }
}
