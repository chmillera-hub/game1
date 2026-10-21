"""Part 2 narration: patterns and speed."""
SCENES = [
    ("title", [
        "This is part two of shaking a rainbow.",
        "Last time, the prism just vibrated back and forth. This time, we move it along shapes: circles, squares, triangles and stars.",
        "And we change the speed, from five times a second up to a hundred, to see how the picture changes.",
    ]),
    ("eye", [
        "First, a word about your eye.",
        "Your vision doesn't take instant snapshots. Each flash of light lingers for a few hundredths of a second, and the simulation models that.",
        "So a dot going round five times a second looks like a comet with a fading tail.",
        "At twenty times a second, the tail reaches all the way round, but one side is still brighter than the other.",
        "At fifty and at a hundred, it's simply a steady ring.",
        "The video is slowed down ten times so you can follow the motion, but the blurring is computed at real speed.",
    ]),
    ("circle", [
        "Now the real thing: a mercury lamp, which gives a few pure colors, shining through a prism that moves in a small circle.",
        "At five times a second, each spectral line is a little comet chasing its own tail.",
        "Watch the directions. The violet comet on the far left goes round clockwise, while the green and yellow comets go counter-clockwise. Same prism, same circle, opposite directions.",
        "The bright blue line never goes round at all. It sits at its minimum-deviation angle, so it just swings up and down along a curve.",
        "At twenty times a second, the comets close into loops. At fifty and a hundred, every line has drawn a complete, steady shape, and the direction can no longer be seen.",
        "Notice the shapes aren't circles anymore. The prism stretches and bends each color's circle differently, into D shapes that mirror each other.",
    ]),
    ("square", [
        "Next, white light, with the prism moving around a square.",
        "At five times a second, you can see the whole rainbow slide around the corners of the square.",
        "At twenty, the square closes, but it pulses, with one edge brighter than the other.",
        "At fifty and a hundred, it's rock steady. The top and bottom edges become two bright rainbow stripes, because the rainbow slides along itself while the prism moves sideways.",
        "The left and right edges smear every color up and down into a faint curtain between them, and where the curtains of different colors overlap, they mix into new shades.",
    ]),
    ("star", [
        "Here's a star, drawn by moving the light source instead of the prism.",
        "At five times a second, you only see one or two strokes of the star at a time.",
        "At twenty, the whole star is there, but it flickers as the bright part runs around it.",
        "At fifty and above, each spectral line has drawn its own complete, steady star.",
        "The stars aren't identical. The violet ones are wider, because violet is more sensitive to the angle of the light.",
    ]),
    ("camera", [
        "Filming this is a different story. Here's what a phone camera at thirty frames per second would record, played at real speed.",
        "At twenty times a second, each frame catches only a third of a lap, so you see short arcs that jump around.",
        "At thirty times a second, the shaking matches the frame rate exactly. Every frame catches the same half of the circle, and the motion seems to freeze.",
        "At fifty, most of the loop shows up, with a gap that wanders around. At a hundred, each frame holds more than a full lap, so the shape looks complete.",
    ]),
    ("gallery", [
        "Here's the whole gallery at a hundred times a second, the speed where your eye sees a steady picture.",
        "Circle, square and triangle. Every shape survives the trip through the prism, but each spectral line gets its own copy, shifted along the spectrum and stretched sideways by a different amount.",
        "The star and the figure eight work the same way, and where the green and yellow copies cross, their light adds up to a lime color.",
        "With white light, the circles of every color pile on top of each other into a glowing rainbow tube. Only the red end still shows a clear ring.",
    ]),
    ("size", [
        "Does the size of the shape matter? Very much.",
        "A small square, half a degree each way, just thickens the rainbow into a band with bright edges.",
        "At one and a half degrees, the band opens into a box: two rainbow stripes on top and bottom, and a faint curtain in between.",
        "At three degrees, each color's square is wider than the gap between colors, so they overlap far along the spectrum, and a pink stripe appears in the middle where red and blue land together.",
    ]),
    ("corners", [
        "Finally, how the prism goes round the corners.",
        "At steady speed, the outline is evenly bright, with magenta in the middle where the ends of the rainbow overlap.",
        "If the prism slows down into each corner, the way a real motor would, the corners glow, because the light lingers there.",
        "And if it snaps from corner to corner, the outline disappears. You see four separate rainbows, two per row, overlapping into magenta.",
    ]),
    ("summary", [
        "So, what changes when you shake a rainbow in patterns?",
        "Below about twenty times a second, you see the rainbow moving. By fifty, your eye joins the motion into steady shapes, and going faster changes nothing.",
        "After that, what matters is the shape, its size, and how it moves through the corners.",
        "And because the prism bends each color differently, every color draws its own version of the shape. Sometimes it even goes round the other way.",
    ]),
]
