"""Pose presets for the diner (limb targets in the character frame: hip origin, y down).

Both characters sit in a booth; the table top's far edge is ~72 units above the hips,
so resting hands sit around y -60..+20. Kai is drawn mirrored, so +x points toward Hale
for both of them. The far arm is the one nearer the other person.
"""

SEATED = dict(hide_legs=True, near_foot=(60.0, 10.0), far_foot=(90.0, 10.0))

HALE_POSES = {
    "rest": dict(near_hand_pos=(56.0, -18.0), far_hand_pos=(164.0, -30.0), far_hand_front=True),
    "rest_low": dict(near_hand_pos=(50.0, -8.0), far_hand_pos=(120.0, -14.0), far_hand_front=True),
    "cuffs": dict(near_hand_pos=(36.0, 26.0), far_hand_pos=(160.0, -28.0), far_hand_front=True, slump=0.3),
    "explain": dict(near_hand_pos=(56.0, -18.0), far_hand_pos=(160.0, -150.0), far_hand="open", far_front=True),
    "hand_mouth": dict(near_hand_pos=(22.0, -214.0), far_hand_pos=(150.0, -26.0), far_hand_front=True, slump=0.35),
    "lean_in": dict(near_hand_pos=(78.0, -16.0), far_hand_pos=(160.0, -24.0), far_hand_front=True, lean=0.12),
    "sorry": dict(near_hand_pos=(64.0, -16.0), far_hand_pos=(140.0, -22.0), far_hand_front=True, lean=0.08, slump=0.4),
    "offer_hand": dict(near_hand_pos=(56.0, -18.0), far_hand_pos=(262.0, -196.0), far_hand="open", far_front=True,
                       lean=0.2),
    "fist": dict(near_hand_pos=(56.0, -18.0), far_hand_pos=(239.0, -200.0), far_hand="fist", far_front=True, lean=0.22),
    "stand": dict(standing=True, near_hand_pos=(30.0, 30.0), far_hand_pos=(70.0, 20.0), far_hand_front=True),
    "fist_ready": dict(near_hand_pos=(56.0, -18.0), far_hand_pos=(205.0, -190.0), far_hand="fist", far_front=True,
                       lean=0.18),
    "push_belt": dict(near_hand_pos=(-118.0, 22.0), far_hand_pos=(150.0, -24.0), far_hand_front=True, lean=-0.06),
    "chin": dict(near_hand_pos=(40.0, -196.0), near_hand="fist", far_hand_pos=(150.0, -24.0), far_hand_front=True,
                 lean=0.06, slump=0.2),
    "talk_hand": dict(near_hand_pos=(56.0, -18.0), far_hand_pos=(176.0, -118.0), far_hand="open", far_front=True,
                      lean=0.06),
}

KAI_POSES = {
    "pour": dict(standing=True, near_hand_pos=(98.0, -32.0), near_hand="mitten", pot=True, pot_tilt=0.55,
                 far_hand_pos=(20.0, 50.0), lean=0.18),
    "pour_done": dict(standing=True, near_hand_pos=(46.0, -70.0), near_hand="mitten", pot=True, pot_tilt=0.0,
                      far_hand_pos=(20.0, 50.0), lean=0.05),
    "rest": dict(near_hand_pos=(44.0, -16.0), far_hand_pos=(104.0, -24.0), far_hand_front=True),
    "sketch": dict(near_hand_pos=(60.0, 14.0), near_hand="pencil", far_hand_pos=(122.0, 8.0), far_hand="open",
                   far_hand_front=True, lean=0.1, slump=0.15),
    "explain": dict(near_hand_pos=(44.0, -16.0), far_hand_pos=(150.0, -150.0), far_hand="open", far_front=True),
    "arms_crossed": dict(near_hand_pos=(58.0, -96.0), far_hand_pos=(-6.0, -104.0), far_front=True, slump=0.15),
    "tense": dict(near_hand_pos=(56.0, -10.0), far_hand_pos=(116.0, -14.0), near_hand="fist", far_hand="fist",
                  far_hand_front=True, slump=0.1),
    "fist": dict(near_hand_pos=(44.0, -16.0), far_hand_pos=(218.0, -195.0), far_hand="fist", far_front=True, lean=0.3),
    "fist_wait": dict(near_hand_pos=(44.0, -16.0), far_hand_pos=(190.0, -186.0), far_hand="fist", far_front=True,
                      lean=0.24),
    "hold_pot": dict(near_hand_pos=(-18.0, -52.0), pot=True, pot_tilt=0.0, far_hand_pos=(104.0, -24.0),
                     far_hand_front=True),
    "set_pot": dict(near_hand_pos=(-84.0, -26.0), pot=True, pot_tilt=0.0, far_hand_pos=(104.0, -24.0),
                    far_hand_front=True),
    "set_pot_rel": dict(near_hand_pos=(-84.0, -26.0), far_hand_pos=(104.0, -24.0), far_hand_front=True),
    "witness": dict(near_hand_pos=(-150.0, -120.0), near_hand="open", far_hand_pos=(104.0, -24.0), far_hand_front=True),
    "hand_chest": dict(near_hand_pos=(44.0, -16.0), far_hand_pos=(30.0, -132.0), far_hand="open", far_front=True,
                       slump=0.05),
    "plant": dict(near_hand_pos=(44.0, -16.0), far_hand_pos=(132.0, -14.0), far_hand="open", far_hand_front=True,
                  lean=0.08),
    "talk_hand": dict(near_hand_pos=(44.0, -16.0), far_hand_pos=(160.0, -120.0), far_hand="open", far_front=True,
                      lean=0.05),
}


def pose_for(char_name, key):
    from rig import default_pose
    p = default_pose()
    table = HALE_POSES if char_name == "hale" else KAI_POSES
    spec = table[key]
    if not spec.get("standing"):
        p.update(SEATED)
    else:
        p.update(hide_legs=True)
    p.update(spec)
    return p
