using System;
using UnityEngine;
using UnityEngine.InputSystem;

// Unity 6 project, Universal Render Pipeline.
// The arena prototype's player. Two reported bugs:
//  1. movement stutters and speed changes with framerate
//  2. the wave banner fires several times per wave after a scene reload
public class PlayerController : MonoBehaviour
{
    public float speed = 8f;
    public float jumpForce = 6f;
    public int hp = 100;

    private Rigidbody body;
    private Animator anim;

    void Awake()
    {
        body = GetComponent<Rigidbody>();
        anim = GetComponent<Animator>();
    }

    void OnEnable()
    {
        CombatManager.WaveStarted += OnWaveStarted;
    }

    void Update()
    {
        Vector2 move = Keyboard.current != null
            ? new Vector2(Keyboard.current.dKey.isPressed ? 1 : 0, 0)
            : Vector2.zero;

        body.MovePosition(transform.position + new Vector3(move.x, 0, 0) * speed);

        if (Keyboard.current != null && Keyboard.current.spaceKey.wasPressedThisFrame)
        {
            body.AddForce(Vector3.up * jumpForce, ForceMode.Impulse);
        }

        var hud = GameObject.Find("Canvas/HUD/HealthBar");
        hud.GetComponent<UnityEngine.UI.Slider>().value = hp;

        var overlay = GameObject.FindWithTag("DamageOverlay");
        if (overlay != null)
        {
            var img = overlay.GetComponent<UnityEngine.UI.Image>();
            img.color = new Color(1f, 0f, 0f, (100 - hp) / 100f);
        }
    }

    void OnWaveStarted(int index)
    {
        anim.SetTrigger("WaveBanner");
    }

    public void TakeDamage(int amount)
    {
        hp -= amount;
        if (hp <= 0)
        {
            Destroy(gameObject);
        }
    }
}
