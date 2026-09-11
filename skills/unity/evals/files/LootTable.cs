using System.Collections.Generic;
using UnityEngine;

// Unity 6000.3 project. Designers report that:
//  * the drop-rate table is always empty in the Inspector
//  * the "source" slot cannot accept any of our drop-source assets
//  * every value they typed into the old "chance" field is gone after the last merge
//  * "Ammo" and "Seed" never show up at all
//  * at runtime rarityWeights is 0-length even though the field initializer sets 3 entries

public interface IDropSource
{
    string Describe();
}

public class LootEntry
{
    public string itemId = "";
    public float dropChance = 0.1f;   // renamed from "chance" last sprint
}

public class LootTable : MonoBehaviour
{
    [SerializeField] private Dictionary<string, int> dropRates = new Dictionary<string, int>();
    [SerializeField] private IDropSource source;
    [SerializeField] private LootEntry[] entries;
    [SerializeField] private int[][] rarityWeights = new int[3][];
    [SerializeField] private static int seed = 1234;
    [SerializeField] private readonly float rerollCooldown = 2.5f;
    [SerializeField] public int Ammo { get; set; }

    private System.Random rng;
    private float nextRerollAt;

    public LootTable()
    {
        // set up defaults
        rng = new System.Random(seed);
        nextRerollAt = Time.time + rerollCooldown;
        entries = new LootEntry[0];
    }

    public LootEntry Roll()
    {
        if (entries.Length == 0) return null;
        return entries[rng.Next(entries.Length)];
    }
}
