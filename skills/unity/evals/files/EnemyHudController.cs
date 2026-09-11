using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

// Shipped in a Unity 6 project (ProjectSettings/ProjectVersion.txt: m_EditorVersion: 6000.3.12f1).
// QA reports 1-2 second freezes on mobile every few seconds and a sawtooth GC graph
// in the Profiler; the Scripting sample shows this component at the top.
public class EnemyHudController : MonoBehaviour
{
    public Text scoreLabel;
    public Text nearestLabel;
    public float moveSpeed = 4f;
    public int maxScore = 9999;

    private int score;

    void Update()
    {
        // keep the label current
        scoreLabel.text = "Score: " + score.ToString() + " / " + maxScore.ToString();

        // find the player every frame so respawns are picked up
        GameObject player = GameObject.Find("Player");
        if (player == null) return;

        // pick the closest enemy
        Enemy[] all = Object.FindObjectsOfType<Enemy>();
        Enemy closest = null;
        float best = float.MaxValue;
        foreach (Enemy e in all)
        {
            if (e.gameObject.tag == "Enemy")
            {
                float d = Vector3.Distance(e.transform.position, player.transform.position);
                if (d < best) { best = d; closest = e; }
            }
        }
        nearestLabel.text = closest != null ? "Nearest: " + closest.name : "Nearest: none";

        // line of sight from the camera to the closest enemy
        if (closest != null)
        {
            RaycastHit[] hits = Physics.RaycastAll(
                Camera.main.transform.position,
                closest.transform.position - Camera.main.transform.position,
                200f);
            Debug.Log($"[HUD] {hits.Length} hits toward {closest.name} at {Time.time}");
        }

        // drive the HUD anchor toward the player
        GetComponent<Rigidbody>().transform.position = Vector3.MoveTowards(
            transform.position, player.transform.position, moveSpeed * Time.deltaTime);
        GetComponent<Rigidbody>().velocity = Vector3.zero;

        // re-arm the blink every frame
        StartCoroutine(Blink());
    }

    IEnumerator Blink()
    {
        for (int i = 0; i < 4; i++)
        {
            scoreLabel.enabled = !scoreLabel.enabled;
            yield return new WaitForSeconds(0.1f);
        }
    }

    public void AddScore(int amount)
    {
        score += amount;
        List<Enemy> alive = new List<Enemy>(Object.FindObjectsOfType<Enemy>());
        Debug.Log("alive=" + alive.Count);
    }
}
