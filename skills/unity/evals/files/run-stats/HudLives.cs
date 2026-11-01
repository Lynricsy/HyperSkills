// Assets/Scripts/UI/HudLives.cs - lives counter on the in-game HUD (one per gameplay scene).
using TMPro;
using UnityEngine;

public class HudLives : MonoBehaviour
{
    [SerializeField] private RunStats stats;
    [SerializeField] private TMP_Text label;

    private void Start()
    {
        RunStats.LivesChanged += OnLivesChanged;
        stats.BeginRun();
        label.text = stats.lives.ToString();
    }

    private void OnLivesChanged(int lives)
    {
        label.text = lives.ToString();
    }
}
