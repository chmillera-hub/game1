# Packet Received

A game in twelve months, and the companion to [Packet Loss](../packet-loss/). You play the information packet: one person's need for deeper connection, community and room to grow, plus the conditions behind it (isolation, overwork, rent, food, abuse of power).

Each month society offers four routes: two pieces of standard advice ("go to the gym", "try therapy", "just vote"…) and two outward channels (tell a friend, start a neighbor group chat, compare notes, mutual aid, organize…). Your goal is to be received by as many of the town's 1,000 people as you can before December ends.

Open `index.html` in a browser. Press 1–4 to pick a card.

## The lens

Every card shows the exact math of how many people that route lets you reach:

| Symbol | Meaning |
| --- | --- |
| *k* | people who hear you directly (some routes scale with your carriers) |
| φ | fidelity: the channel's fidelity × the share of your 8 fields still intact |
| *R* = *R*₀ · φ | how many others each listener passes you on to; a distorted message travels less |
| *E* = *k*(1 + *R* + *R*²) | expected contacts over two more generations |
| new = (*N* − *r*)(1 − e^(−*E*/*N*)) | expected new people, after overlap with the *r* who already have it |

Outcomes are drawn around that expectation (±25%), and risky routes roll their risk. A share of the new people become **carriers**, and carriers are what compare notes, mutual aid and organizing build on.

Each card also shows the four tests from Packet Loss, OUT × INTACT × SIDEWAYS × UPWARD. Reach is the score. Whether any route passed all four decides if the year ends with the conditions in play.

## Energy: work or perish

Energy drains by 2 every month. Standard advice restores it, which is real, but it almost never spreads the packet. Outward routes cost energy and compound. Once 20 carriers have your back they cover for you, and the drain drops to 1.

Practicing gratitude rewrites one field of your payload, so INTACT fails until you name the pattern. Naming restores all 8 fields and locks them.

## Balance

Over 3,000 simulated years per strategy (see `core.js`, which runs in Node as well as the browser):

| Strategy | Mean people reached | Organized and delivered |
| --- | ---: | ---: |
| Only standard advice | 5 | 0% |
| Random choices | ~210 | ~3% |
| Greedy for reach | ~610 | ~14% |
| Planning energy and network | ~750 | ~60% |

## Files

- `index.html`: the page, the board UI and the town map
- `core.js`: pure game logic covering options, the lens math, month events and resolution
