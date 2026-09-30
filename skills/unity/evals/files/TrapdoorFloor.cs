using UnityEngine;

// Unity 6000.3 project, default physics settings.
// Scene: a warehouse floor slab (BoxCollider, no Rigidbody) that drops away as a trapdoor.
// Crates are dynamic Rigidbodies stacked on the slab by the level designer.
//
// Bug reports:
//  * crates that have been resting on the slab for a few seconds stay floating in mid-air
//    when the trapdoor drops; a crate that was dropped onto the slab a moment before the
//    trapdoor opens falls with it as expected
//  * "LandingCheck" sometimes reports the slab under the player even after it has moved away

public class TrapdoorFloor : MonoBehaviour
{
    [SerializeField] Transform slab;
    [SerializeField] float dropSpeed = 4f;
    [SerializeField] float dropDistance = 6f;

    bool opening;
    float dropped;

    public void Open() => opening = true;

    void Update()
    {
        if (!opening || dropped >= dropDistance)
            return;

        float step = dropSpeed * Time.deltaTime;
        slab.position += Vector3.down * step;
        dropped += step;
    }

    // Called by the player controller right after it teleports the player.
    public bool LandingCheck(Vector3 feet)
    {
        return Physics.Raycast(feet + Vector3.up * 0.1f, Vector3.down, out var hit, 0.5f)
               && hit.transform == slab;
    }
}
