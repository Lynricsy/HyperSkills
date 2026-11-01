// Assets/Scripts/Run/RunStats.cs - Unity 6000.3.
// Project Settings > Editor > Enter Play Mode Options: "Reload Domain" is OFF (faster iteration).
using System;
using UnityEngine;

[CreateAssetMenu(menuName = "Run/Run Stats")]
public class RunStats : ScriptableObject
{
    [SerializeField] private int startingLives = 3;

    [NonSerialized] public int lives;
    [NonSerialized] public int kills;

    public static event Action<int> LivesChanged;
    private static int s_runsStarted;

    // Domain reload is off, so [RuntimeInitializeOnLoadMethod] would never run again
    // after the first Play session - reset here instead.
    private void OnEnable()
    {
        lives = startingLives;
        kills = 0;
    }

    public void BeginRun()
    {
        s_runsStarted++;
        Debug.Log($"Run #{s_runsStarted} starting with {lives} lives");
    }

    public void LoseLife()
    {
        lives--;
        LivesChanged?.Invoke(lives);
    }
}
