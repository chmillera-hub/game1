"""The rhyming read-aloud version of "Bunny Girl and Wolf Dog".

Each scene shows one illustration. Each page is one spoken chunk and one
caption card. `say` is what the voice reads (it may carry pronunciation hints
like "[Mooky](/mˈuki/)"); `show` is the caption text. `pause` is the silence
after the page, in seconds.
"""

TITLE = "Bunny Girl and Wolf Dog"

SCENES = [
    dict(id="title", pages=[
        dict(show="Bunny Girl and Wolf Dog!", pause=0.7),
    ]),
    dict(id="bunny", pages=[
        dict(show="Here's a little story, short and sweet, about a girl you'll love to meet!", pause=0.45),
        dict(show="Her name is Bunny Girl! She always wears a hat with bunny ears... imagine that!", pause=0.45),
        dict(show="She loves to pretend she's a bunny too.", pause=0.25),
        dict(show="Hop! Hop! Hop! Just like bunnies do!", pause=0.9),
    ]),
    dict(id="park", pages=[
        dict(show="Bunny Girl and her mom take their dogs to play at the doggy park... hip, hip, hooray!", pause=0.45),
        dict(show="There's Cosmo, Pettie, and Luna... hi! And Mooky and Buddy come zooming by!",
             say="There's Cosmo, Pettie, and Luna... hi! And [Mooky](/mˈuki/) and Buddy come zooming by!",
             pause=0.9),
    ]),
    dict(id="invisible", pages=[
        dict(show="At the park, Wolf Dog waits for her each day. They love each other! They laugh and play!", pause=0.45),
        dict(show="But Wolf Dog is shy... so shy, you see, he made himself invisible as can be!", pause=0.45),
        dict(show="Only Bunny Girl can see him, it's true!", pause=0.3),
        dict(show="Can you spot him? Peek-a-boo!", pause=0.9),
    ]),
    dict(id="hug", pages=[
        dict(show="Bunny Girl wished her mom and her dogs could play... but they couldn't see Wolf Dog. He was hidden away!", pause=0.45),
        dict(show="Then she had an idea... a great big hug! A squeezy, cozy, snuggle-bug hug!", pause=0.45),
        dict(show="“I love you, Wolf Dog, yes I do! One of my best friends... is you!”",
             say="I love you, Wolf Dog, yes I do! One of my best friends... is you!", pause=0.5),
        dict(show="And suddenly...", pause=1.9),
    ]),
    dict(id="poof", pages=[
        dict(show="POOF!", pause=0.7),
        dict(show="Wolf Dog appeared for all to see! The doggies ran up, as happy as can be!", pause=0.45),
        dict(show="They jumped and they played, and they ran all about. No longer shy... Wolf Dog came out!", pause=0.9),
    ]),
    dict(id="family", pages=[
        dict(show="From then on, in every kind of weather, Bunny Girl and Wolf Dog were always together.", pause=0.45),
        dict(show="With Mom and the doggies, big and small, Wolf Dog was part of the family, after all!", pause=0.9),
    ]),
    dict(id="end", pages=[
        dict(show="So if you have a friend who's shy, give them a big hug, and say hi!", pause=0.45),
        dict(show="A little love goes a long, long way...", pause=0.3),
        dict(show="The End! Now let's go out and play!", pause=1.6),
    ]),
]

DOG_NAMES = ["Cosmo", "Pettie", "Luna", "Mooky", "Buddy"]
