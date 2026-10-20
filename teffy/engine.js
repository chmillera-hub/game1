/*
 * Teffy engine: the 16 emotions, the reply parser, and the Emotional Council chat engine.
 *
 * Pure logic with no DOM, clock or randomness, so the page and the test simulations run the
 * exact same prompts and turn-taking rules. The page supplies `io.ask`, which sends a prompt to
 * Claude and resolves with the parsed JSON reply.
 */
var TeffyEngine = (function () {
  "use strict";

  // ---------- The emotions (from "Teffy: The Emotional Framework For You") ----------

  const EMOTIONS = [
    { name: "Anger", emoji: "😡", line: "Talk to your emotions, now!", when: "-1 if emotions feel ignored",
      purpose: "The consciousness or the other emotions' voices are not being heard, so it steps in to amplify them until they are heard.",
      need: "The 'emotional need' not being heard should be addressed immediately. Boundaries should be set and respected.",
      personality: "Steps in when other emotions are being silenced or not listened to, it amplifies the voice of emotions that are not being seen or heard or neglected, such as annoyance or even the consciousness itself." },
    { name: "Annoyance", emoji: "🤨", line: "Why did you/they say…", when: "-1 if frustrated or minor boundaries crossed or any emotions feel minimized or dismissed",
      purpose: "Signals minor boundaries are being ignored or minimized. Has the ability to detect circular logic or vague reasoning.",
      need: "Will often ask you to say to the other person why did you say XYZ? It wants you to seek clarification to ensure the interaction is not malicious or dismissive. It signals a lack of acknowledgement and respect in interactions.",
      personality: "Has a laser focus on any words or subtleties in social interactions that have an underlying dismissiveness or vagueness, or any attempt to minimize other emotions. If not addressed, anger can quickly step in to amplify its voice." },
    { name: "Boredom", emoji: "😩", line: "This is dull...", when: "-1 if the plan is monotonous",
      purpose: "Signals lack of engagement or stimulation.",
      need: "The plan should have new challenges or mental stimulation.",
      personality: "Is usually at odds with Overwhelm, wants the plan to be cool and exciting but doesn't know how to offer any help of its own, will show up during another plan and demand the consciousness to change it midway." },
    { name: "Doubt", emoji: "🤔", line: "What if...", when: "-1 if concerns are ignored",
      purpose: "Questions current plans or beliefs. Prepares you so that you are able to protect your other emotions such as embarrassment or wellness in situations where there is a possibility for them to suffer.",
      need: "The consciousness needs to provide clarity, re-evaluation, or deeper understanding of the plan that it offered. For example Doubt saying \"what if the plan doesn't work?\", \"what if the rollercoaster collapses while we are on it?\", \"what if your mind goes blank during the test?\"",
      personality: "Asks deep questions that could rock you to your core, but the questions must be addressed in a 100% honest and compassionate manner. Will usually ask these piercing questions in the middle of a plan or before you start doing the plan. Do not ignore the questions it is offering, but use the questions as a springboard to offer reassurance or reflection. It is asking these questions to prepare you and protect your other emotions from suffering. Can get caught in mind loops when the decision isn't clear. Impulsivity can help pull it out of these loops." },
    { name: "Efficiency", emoji: "⏰", line: "Is this worth the time?", when: "-1 if wasting time",
      purpose: "Indicates the consciousness's plan is spending excessive time or energy on something.",
      need: "Find a faster or less time consuming way of doing something.",
      personality: "" },
    { name: "Embarrassment", emoji: "🥺", line: "Let's maintain our relationships", when: "-1 if it risks relationships",
      purpose: "Facilitates creating social connections with different social groups, social regulator dial, allows one to connect with different social groups in an appropriate manner, a socially mindful passion dial (gentle loving kindness to fiery intense passion), allows mindfulness in sharing, allows one to show appropriate amount of passion with others who share your passions, social calibrator.",
      need: "Maintain social norms, avoid info dumping people who won't understand what you're talking about, keep revelations to yourself until you know someone who can relate, keep activities to yourself that you know the other person dislikes heavily if you value their friendship, ask it before sending a text (a quick short text versus an info dump), ask it before going into a social situation, show it that you will listen to it before making a social decision.",
      personality: "Will shake its head vigorously yes or no, will tighten its sweatshirt over its head and look down at the ground when suffering, will bring up memories where you violated social balance or ignored emotional suffering of others outside yourself." },
    { name: "Fear", emoji: "😨", line: "Let's pause and think here...", when: "-1 if fearful",
      purpose: "Signals potential danger or threat. Signals the environment or the plan is not addressing the needs of other emotions.",
      need: "Redirect your efforts towards forming closer relationships with your other emotions, it wants your other emotions to be stronger and healthier before you engage in the activity. For example, a tiger jumping out of a bush, or thinking about going on a super tall roller coaster for the first time might have fear signaling a threat to Wellness (physical health).",
      personality: "Shows up to protect your other emotions and the self when it identifies potential danger from the environment or the consciousness's plan. It might worry that the self is not prepared to do the plan. It wants the consciousness to show it that it sees which other emotions are in potential danger. Then the consciousness can either modify the plan to prepare for the future, or discuss the risks with fear until an agreement is reached." },
    { name: "Frugality", emoji: "💰", line: "Is this worth the resources?", when: "-1 if wasteful",
      purpose: "Signals a waste of resources like money.",
      need: "Conserve resources.",
      personality: "" },
    { name: "Guilt", emoji: "😭", line: "That makes us or others suffer", when: "-1 if causing guilt",
      purpose: "Signals perceived wrongdoing or unmet expectations. Especially against other vulnerable emotions that are being ignored. Shows how other emotions in the self or in others are suffering and need nurturing.",
      need: "Ensure your plan is moral and fair to all beings, and fair to all other emotions.",
      personality: "Will come to the aid of other emotions that are being ignored or neglected, will remind you of other emotions that are suffering." },
    { name: "Hunger", emoji: "🤤", line: "Feed me!", when: "-1 if neglecting basic needs",
      purpose: "Consume nutrients.",
      need: "Consume nutrients.",
      personality: "One of the most obvious signals, but it can get indigestion when it's over fed, can cause chaos when paired with impulsivity or boredom." },
    { name: "Impulsivity", emoji: "🐶", line: "Squirrel! Run to the most stimulating thing!", when: "0 if spontaneous",
      purpose: "Signals desire for spontaneity and immediate action or excitement. Can motivate immediate action, but runs to the nearest interesting thing in the immediate vicinity even if those things might cause other emotions to suffer if not redirected (phone scrolling, ruminating, and junk food).",
      need: "Do something exciting that raises the heart rate.",
      personality: "Disruptive, gets bursts of energy seemingly randomly, easily satisfied but seems to be drawn to numbing activities like video games which can cause disconnection by distracting your consciousness from your emotional family's suffering. Does not get caught in mind loops like doubt." },
    { name: "Loneliness", emoji: "😔", line: "I could use a hug…", when: "-1 if lonely",
      purpose: "Indicates a lack of connection or belonging.",
      need: "Companionship or emotional connection.",
      personality: "Wants a hug, wants to cuddle, wants to hear that the consciousness cares for it and wants to nurture it." },
    { name: "Overwhelm", emoji: "😵‍💫", line: "That's too much...", when: "-1 if overwhelming",
      purpose: "Indicates too many demands or pressures at once. Signal to look at other plans since the current one might be getting ahead of current abilities. Guides away from getting stuck in the mud, or caught in the weeds of work. Protects you from taking on too many responsibilities, or taking on tasks you are not ready for yet. Can help lead maintain sustained-effort and longer focus. Defense against burnout.",
      need: "Respect the boundary it is signaling fully and do not press the issue.",
      personality: "Cannot be supplicated or sweet-talked, demands full respect, does not negotiate, is usually at odds with boredom." },
    { name: "Sadness", emoji: "❤️", line: "I will tell you which single 1 specific emotion is suffering most specifically that must be nurtured by the consciousness's plan", when: "-1 if consciousness is not making the single most suffering emotion it identified a 0",
      purpose: "Signals which single 1 emotion is being most neglected among the others and is not fully seen and not fully heard.",
      need: "Show deep empathy and acknowledgment and care and comfort to the single suffering emotion especially if they are suffering or neglected.",
      personality: "Signals that you are indeed listening to your most vulnerable emotion on a fundamental level, provides a signal of comfort as you actively provide plans that fully see and hear the single most suffering emotion." },
    { name: "Tiredness", emoji: "😴", line: "Let's rest...", when: "-1 if exhausting",
      purpose: "Lack of sleep, signals disconnection from other emotions due to exhaustion.",
      need: "Rest/sleep.",
      personality: "Easily bullied by other emotions such as impulsivity, but also has one of the clearest signals that it is suffering. Before you satisfy it, try satisfying the other emotions first if possible, because when you rest you can't satisfy the other emotions because your consciousness is turned off." },
    { name: "Wellness", emoji: "🤕", line: "This could harm physical health", when: "-1 if risky",
      purpose: "If the plan is not benefiting physical health, Wellness might show up.",
      need: "Prefers the plan be beneficial to physical health.",
      personality: "Will step in usually when the consciousness offers a plan to hunger or impulsivity. Wants the plan to benefit overall physical health." },
  ];
  const BY_NAME = new Map(EMOTIONS.map(e => [e.name.toLowerCase(), e]));
  const ALIASES = {
    angry: "anger", annoyed: "annoyance", irritation: "annoyance", bored: "boredom", doubtful: "doubt",
    efficient: "efficiency", embarrassed: "embarrassment", afraid: "fear", scared: "fear", frugal: "frugality",
    guilty: "guilt", hungry: "hunger", impulsive: "impulsivity", impulse: "impulsivity", lonely: "loneliness",
    overwhelmed: "overwhelm", sad: "sadness", tired: "tiredness", health: "wellness",
  };
  function findEmotion(v) {
    const k = String(v == null ? "" : v).toLowerCase().replace(/[^a-z]/g, "");
    return BY_NAME.get(k) || BY_NAME.get(ALIASES[k]) || null;
  }
  // Society isn't an emotion. It parrots the culture's well-meaning, surface-level advice; the emotions call it out.
  const SOCIETY = {
    name: "Society", emoji: "🦜",
    line: "Have you tried yoga?",
    about: "Advice you've absorbed from the people around you and the culture: coworkers, friends, family, the internet. It sounds well-meaning (\"try deep breathing\", \"take a nap\", \"don't make waves\") but nobody ever checked whether it meets the need. It isn't a feeling, so it never gets a score or a say in the plan. Your emotions call it out, and its lines preview the pushback you may hear when you open up to real people, so the final plan gives you a reply ready for each one.",
  };
  const emo = name => (name === "Society" ? SOCIETY : findEmotion(name) || { name: String(name), emoji: "•" });

  // ---------- Reading replies ----------

  // Pulls every top-level {...} object out of the text, so one-per-line JSON, pretty-printed JSON
  // and replies wrapped in code fences all read the same way. An unfinished object is skipped.
  function scanObjects(text) {
    const out = [];
    let depth = 0, start = -1, inStr = false, esc = false;
    text = String(text == null ? "" : text);
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (inStr) {
        if (c === "\n") { inStr = false; esc = false; depth = 0; start = -1; continue; }   // broken line: drop that object
        if (esc) esc = false;
        else if (c === "\\") esc = true;
        else if (c === "\"") inStr = false;
        continue;
      }
      if (c === "\"") { if (depth > 0) inStr = true; continue; }
      if (c === "{") { if (depth === 0) start = i; depth++; }
      else if (c === "}" && depth > 0) {
        depth--;
        if (depth === 0) { try { out.push(JSON.parse(text.slice(start, i + 1))); } catch (e) { /* skip malformed */ } }
      }
    }
    return out;
  }
  function cleanQuote(s) {
    const t = String(s == null ? "" : s).trim();
    const m = t.match(/^["“'‘]([\s\S]*)["”'’]$/);
    return m ? m[1].trim() : t;
  }
  function toScore(v) {
    if (typeof v === "number") return v < 0 ? -1 : 0;
    return /[-−–]\s*1/.test(String(v)) ? -1 : 0;
  }
  const arr = v => (Array.isArray(v) ? v : []);
  const badShape = what => ({ code: "bad_shape", message: what });
  const isParseFail = e => !!e && (e.code === "invalid_json" || e.code === "bad_shape" || e.code === "empty_completion");

  // ---------- The Emotional Council ----------

  const COUNCIL = {
    maxOpeners: 3,           // suffering emotions that speak in the opening (the rest start at -1 and speak later)
    maxSufferers: 6,         // emotions that start the chat suffering
    maxHelpers: 3,           // emotions at 0 that join to help
    maxParticipants: 10,     // the chat can grow when someone is pulled in
    maxEmotionMessages: 14,  // emotion messages per stretch; a user message opens a new stretch
    consolidateEvery: 3,     // the Consciousness updates the plan after this many emotion messages
    maxCalls: 40,            // Claude calls per stretch, a hard stop
    societyGap: 3,           // emotion messages between Society's chimes
    societyMax: 2,           // Society's chimes per stretch
    window: 16,              // chat lines each prompt sees
  };

  function newCouncil(thought, opts) {
    return {
      thought: String(thought || "").trim(),
      society: !(opts && opts.society === false),   // Society 🦜 chimes in (off in serious moments)
      serious: false,
      societyCount: 0,
      societyAt: -99,          // emotionMsgs when Society last spoke
      status: "new",           // new | running | paused | done
      idea: "",
      plan: "",
      prevPlan: "",            // the plan before the last update, so the council can see what changed
      planVersion: 0,          // goes up each time the Consciousness changes the plan
      userCount: 0,            // goes up with each user message
      participants: [],
      scores: {},              // name -> -1 | 0, live
      scoredAt: {},            // name -> when its score was last set ("planVersion:userCount")
      start: {},               // name -> score when it joined
      ever: {},                // name -> true once it has been -1
      lastWhy: {},             // name -> its reason at the last turn-taking call
      conditions: [],          // [{ emotion, text }]: what an emotion asked for when it came round to 0
      forYou: [],              // facts or choices only the user can supply
      neglected: "",           // Sadness's current pick, always someone at -1
      guardian: "",            // the emotion that speaks for what the user actually wants
      userNamed: [],           // emotions the user's latest message named ("my doubt says…"); they answer first
      societyEarly: false,     // Society's first chime-in right after the openings
      settledChecks: 0,
      askedOf: "",             // the emotion the Consciousness just asked a question
      consolidations: 0,
      messages: [],            // user | consciousness | emotion | decide | note | final
      emotionMsgs: 0,
      sinceConsolidate: 0,
      quiet: 0,
      misses: 0,
      calls: 0,
      callsRun: 0,
      fresh: false,
    };
  }

  const stamp = s => `${s.planVersion || 0}:${s.userCount || 0}`;
  function setScore(s, name, score) {
    if (name === "Sadness") return;
    s.scores[name] = score < 0 ? -1 : 0;
    if (!s.scoredAt) s.scoredAt = {};
    s.scoredAt[name] = stamp(s);
    if (score < 0) s.ever[name] = true;
  }
  // Has anything changed for this emotion since it last set its score: a new plan or a user message?
  const movedSince = (s, name) => !s.scoredAt || s.scoredAt[name] !== stamp(s);

  function addParticipant(s, name, score) {
    if (!name || s.participants.includes(name) || s.participants.length >= COUNCIL.maxParticipants) return false;
    const at = s.participants.indexOf("Sadness");
    if (at >= 0 && name !== "Sadness") s.participants.splice(at, 0, name); else s.participants.push(name);
    if (name === "Sadness") s.scores.Sadness = 0; else setScore(s, name, score);
    if (!(name in s.start)) s.start[name] = s.scores[name] < 0 ? -1 : 0;
    return true;
  }
  // Sadness watches during the chat. It only scores at the end: -1 if the emotion it named is still suffering.
  const suffering = s => s.participants.filter(n => n !== "Sadness" && s.scores[n] < 0)
    .concat(s.status === "done" && s.scores.Sadness < 0 ? ["Sadness"] : []);
  const tally = s => ({ start: Object.keys(s.start).filter(n => s.start[n] < 0).length, now: suffering(s).length });

  // Emotions the user names as speaking up: "hunger says…", "my doubt says…", "my anger wants…"
  function mentionedEmotions(text) {
    const out = [];
    const re = /\b(?:my\s+)?([a-z]+)\s+(?:says|said|is saying|wants|thinks|is worried|is scared|keeps saying)\b/gi;
    let m;
    while ((m = re.exec(String(text || "")))) {
      const em = findEmotion(m[1]);
      if (em && em.name !== "Sadness" && !out.includes(em.name)) out.push(em.name);
    }
    return out;
  }
  // Emotions named in a council message ("Wellness would want…"), by their capitalized names only.
  const NAME_RE = new RegExp(`\\b(${EMOTIONS.map(e => e.name).join("|")})\\b`, "g");
  const namedIn = text => [...new Set((String(text || "").match(NAME_RE) || []))];

  function addUserMessage(s, text) {
    text = String(text || "").trim();
    if (!text) return;
    s.messages.push({ kind: "user", text });
    s.userCount = (s.userCount || 0) + 1;
    const named = mentionedEmotions(text);
    if (s.participants.length) named.forEach(n => {
      if (!addParticipant(s, n, -1) && s.participants.includes(n)) setScore(s, n, -1);
    });
    s.userNamed = named.filter(n => s.participants.includes(n));
    // A user message opens a fresh stretch of conversation, and the council always hears it out.
    s.emotionMsgs = 0;
    s.callsRun = 0;
    s.quiet = 0;
    s.societyCount = 0;
    s.societyAt = -99;
    s.fresh = true;
    if (s.status === "done") { s.status = "running"; s.scores.Sadness = 0; }
  }

  // ---------- Prompt text ----------

  const who = n => (n === "Consciousness" ? "🧠 Consciousness" : n === "You" ? "the user" : `${emo(n).emoji} ${n}`);
  const scoreWord = v => (v < 0 ? "-1" : "0");
  const clip = (t, n) => (t.length > n ? t.slice(0, n - 1) + "…" : t);

  function transcript(s, limit) {
    const lines = [];
    for (const m of s.messages) {
      if (m.kind === "user") lines.push(`User: ${m.text}`);
      else if (m.kind === "consciousness") lines.push(`🧠 Consciousness${m.to ? " → " + m.to : ""}: ${m.text}`);
      else if (m.kind === "emotion") lines.push(`${who(m.from)}${m.to && m.to !== "all" ? " → " + (m.to === "You" ? "user" : m.to) : ""}: ${m.text}`);
      else if (m.kind === "society") lines.push(`🦜 Society (not an emotion)${m.to ? " → " + m.to : ""}: ${m.text}`);
    }
    return lines.slice(-(limit || COUNCIL.window)).join("\n") || "(nobody has spoken yet)";
  }
  const emotionMessages = s => s.messages.filter(m => m.kind === "emotion");
  function firstWords(s) {
    return emotionMessages(s).slice(-3).map(m => m.text.split(/\s+/).slice(0, 2).join(" ").replace(/[^\w' ]/g, "")).filter(Boolean);
  }
  function saidBy(s, name) {
    const said = emotionMessages(s).filter(m => m.from === name).map(m => m.text);
    if (!said.length) return "nothing yet";
    const first = `first: "${clip(said[0], 110)}"`;
    return said.length === 1 ? first : `${first}; latest: "${clip(said[said.length - 1], 110)}" (${said.length} messages)`;
  }
  function historyOf(s, name) {
    const out = [];
    for (const m of s.messages) {
      if (m.kind === "emotion") {
        if (m.from === name) out.push(`You said${m.to && m.to !== "all" ? " to " + m.to : ""}: "${m.text}"`);
        else if (m.to === name || new RegExp(`\\b${name}\\b`).test(m.text)) out.push(`${m.from} said${m.to === name ? " to you" : " about you"}: "${m.text}"`);
      } else if (m.kind === "society" && m.to === name) {
        out.push(`Society 🦜 said to you: "${m.text}"`);
      } else if (m.kind === "consciousness" && (m.to === name || new RegExp(`\\b${name}\\b`).test(m.text))) {
        out.push(`The Consciousness${m.to === name ? " asked you" : " said"}: "${m.text}"`);
      }
    }
    return out.slice(-8).join("\n") || "(nothing yet)";
  }
  function profileLine(name) {
    const e = emo(name);
    if (name === "Sadness") return `${e.name} ${e.emoji}: watches for the suffering emotion that has been heard and answered least, and speaks up for it with empathy. It makes no proposals of its own.`;
    let t = `${e.name} ${e.emoji}: (${e.when}). Needs: ${e.need}`;
    if (e.personality) t += ` Personality: ${e.personality}`;
    return t;
  }
  const conditionLines = s => (s.conditions || []).map(c => `- ${c.emotion}: ${c.text}`).join("\n");
  const conditionOf = (s, n) => { const c = (s.conditions || []).find(x => x.emotion === n); return c ? clip(c.text, 110) : ""; };
  const planChange = s => (s.prevPlan && s.prevPlan !== s.plan ? `THE PLAN BEFORE THE LAST UPDATE: ${s.prevPlan}` : "");

  const VOICE = "Text like a real person in a group chat: casual, direct, specific, in your own words. Don't quote your catchphrase or copy phrases or quoted lines from earlier messages (refer to them instead, like \"the text to Sam\"). Talk about yourself in the first person; never call yourself by name, introduce yourself or write stage directions or gestures. Never mention scores, -1, 0 or \"the council\"; say what you can or can't live with in plain words. Use only facts the user gave or that came up in the chat; never invent people, places, times, amounts, history or what someone said (write ___ for a detail only the user knows). If you build on someone's idea, name whose it is. Call the user \"you\", or \"we\"/\"us\" since you're part of them, and talk about their life as \"your\" or \"our\", never \"my ideas\". Use \"they\" or the person's role (\"your coworker\") for anyone whose gender the user didn't give.";
  // How every voice in the council talks, whatever its emotion.
  const CARE = [
    "Be radically non-violent and pro-human: never insult, blame, label, shame or threaten anyone (the user, the other people in their life, or the other emotions), and never put a moral label on the user's options (\"a lie\", \"lazy\"). Speak to specific actions and their effects, the need behind your feeling, and a request that respects everyone involved. Even angry, be firm and clear, never harsh.",
    "Be precise and actionable: name your specific barrier (exactly what you can't live with) and a doable request: who does what, and when, within the user's real timeframe (if it's happening this morning, nothing can be done \"tonight\"). If you ask for a limit or amount, propose a number; if only the user can know it, say so. If it's a message to someone, give the actual words.",
    "Humor, slang or a quick \"lol that sucks\" is fine, as long as the same message says what you mean by it and what you want the Consciousness to do.",
    "If you ask a question, say why you're asking and what answer would settle you. Never just wonder out loud (\"should we? idk\"): name what you don't know or fear, and what would settle it.",
  ].join("\n- ");
  const PARAGRAPH = "ONE paragraph: usually 2 to 4 sentences, never more than 6. No line breaks, lists or headings.";
  // Chat bubbles hold one paragraph.
  const oneParagraph = t => cleanQuote(t).replace(/\s*\n+\s*/g, " ").replace(/\s{2,}/g, " ").trim();
  const SAFETY = "If the user seems to be in danger or in crisis, the plan must put their safety first and include reaching out to someone they trust or a crisis line.";
  const SOCIETY_NOTE = "🦜 Society is not an emotion: it's advice the user has absorbed from people and the culture and never examined (\"try deep breathing\", \"have you tried yoga\", \"take a nap\", \"don't make waves\"). It also previews the pushback the user may hear from real coworkers, friends or family. When its advice misses an emotion's specific need, that emotion, or another whose angle sees why it misses (Annoyance spots vague reasoning, Anger spots a need being minimized), calls it out: what the advice misses and what the real need is, and, when it helps, the short line the user could say back if a real person tells them this. Society's advice never becomes part of the plan unless an emotion turns it into something specific.";
  const USER_ONLY = "Some things only the user can supply (their own numbers, a person's name, whether someone else will say yes). The council can't produce them, so nobody should keep asking for them. A plan step that tells the user to get or decide that thing answers the objection, as long as the plan also says what the answer must meet (\"savings cover ___ months, at least six\").";

  function convenePrompt(s) {
    return [
      "You are setting up Teffy's Emotional Council: a group chat in which the user's personified emotions talk with each other and with the 🧠 Consciousness until each one can live with the plan (score 0) instead of suffering (score -1).",
      "",
      "THE ONLY 16 EMOTIONS:",
      EMOTIONS.filter(e => e.name !== "Sadness").map(e => `- ${e.name} ${e.emoji}: (${e.when}). Needs: ${e.need}`).join("\n"),
      "",
      "THE USER WROTE:",
      `"${s.thought}"`,
      "",
      "Decide who joins the chat.",
      "- \"idea\": the user's plan exactly as they stated it, as a bare first-person action (\"I push through all weekend to catch up\"), one sentence, without \"I'm thinking about\". Don't fix anything yet. If they described a feeling rather than a plan, the idea is what they're inclined to do about it.",
      "- \"suffering\": every emotion whose need THIS idea, as stated, fails right now (score -1). If the idea already serves an emotion's need, it is not suffering. Any emotion the user mentions as objecting belongs here.",
      `- For at most ${COUNCIL.maxOpeners} of them, with clearly different needs, write "says": an opening chat message of two or three sentences about the user's actual situation: the exact part of the idea that fails its need, and one concrete request (one option, no either/or; what, how much in numbers, when; if it involves a person, the words to say). A request is a plain request, not "Could you…?". Give every other suffering emotion "says": "" (it speaks later). Merge overlapping worries into whichever emotion says it best: rest, sleep and a day off overlap; \"will it work\" and \"will the money last\" overlap; \"rehearse\" and \"fix the slides\" overlap. No two openings start or end the same way.`,
      "- \"need\": for each suffering emotion, what would bring it to 0.",
      "- \"helpers\": up to 3 emotions at 0 that could help the suffering ones' core needs from their own angle, with needs that differ from each other (never two that overlap, like Wellness and Tiredness). Always include, here or under suffering, the emotion that speaks for what the user actually wants (Impulsivity for fun, Loneliness for company, Anger or Annoyance for a boundary the user wants to set, and so on): it guards that want when the plan starts to water it down.",
      "- Scores are only -1 or 0. Never invent an emotion. Never leave a suffering emotion out to make things look calmer. Sadness joins on its own, so don't list it.",
      "- " + VOICE,
      "- Openings are radically non-violent: no blaming, labeling or shaming the user, other people or other emotions.",
      "- " + SAFETY,
      "",
      "- \"guardian\": the one emotion (suffering or helper) that speaks for what the user actually wants; it must be in one of the lists above.",
      "- \"serious\": true if the user seems to be in danger, in crisis, or in deep grief (no jokes belong in this chat), else false.",
      "",
      "Reply with only this JSON:",
      "{\"idea\":\"...\",\"suffering\":[{\"emotion\":\"Overwhelm\",\"says\":\"...\",\"need\":\"...\"}],\"helpers\":[\"Efficiency\"],\"guardian\":\"Efficiency\",\"serious\":false}",
    ].join("\n");
  }

  function pulsePrompt(s) {
    const asked = s.askedOf ? `The Consciousness just asked ${s.askedOf} a question.` : "";
    const promised = conditionLines(s);
    return [
      "You decide who talks next in Teffy's Emotional Council, a group chat where the user's personified emotions work out a plan with the 🧠 Consciousness. Each emotion wants to reach 0 (it can live with the plan, even grudgingly) instead of -1 (suffering), and helps the others from its own angle without being annoying.",
      "",
      `THE USER'S SITUATION: "${s.thought}"`,
      `THE PLAN RIGHT NOW: ${s.plan}`,
      planChange(s),
      promised ? `CONDITIONS EMOTIONS ACCEPTED ON:\n${promised}` : "",
      asked,
      "",
      "THE EMOTIONS IN THE CHAT:",
      s.participants.map(n => n === "Sadness"
        ? `- ${profileLine(n)}\n  Has said: ${saidBy(s, n)}`
        : `- ${profileLine(n)}${n === s.guardian ? " It speaks for what the user actually wants." : ""}\n  Score now: ${scoreWord(s.scores[n])}. Plan or user changed since it set that score: ${movedSince(s, n) ? "yes" : "no"}. Has said: ${saidBy(s, n)}.${conditionOf(s, n) ? ` Accepted on: "${conditionOf(s, n)}".` : ""}${s.lastWhy && s.lastWhy[n] ? ` Last turn it thought: "${s.lastWhy[n]}"` : ""}`).join("\n"),
      "",
      "THE CHAT SO FAR (oldest first):",
      transcript(s),
      "",
      "For EVERY emotion in the chat, decide from that emotion's own point of view:",
      "- \"score\": its honest score for THE PLAN RIGHT NOW.",
      "  · -1 becomes 0 only if the plan now answers that emotion's FIRST objection (see \"first:\") as well as its latest one. Moving toward its topic isn't enough. Before saying the plan skips something, check the plan's text: if it's there, it's covered.",
      "  · 0 becomes -1 only if the plan itself now works against its own need (for example a step it accepted on was dropped). A step that was already in the plan when it accepted never counts. It doesn't take on a grievance another emotion raised for it.",
      "  · For the emotion that speaks for what the user wants: if that want is now delayed, put behind something else, replaced by a softer step, or made to depend on conditions that may never be met, the plan works against its need.",
      "  · An emotion at 0 never says it can't live with the plan; if it has a step that would make the plan better, it replies with that.",
      "  · If nothing changed since it set its score (\"no\" above), it keeps that score.",
      "  · " + USER_ONLY,
      "  · \"score\" and \"why\" must agree.",
      "- \"reply\": true only if it has something NEW to say right now:",
      "  · answering someone who spoke to it or asked it a question;",
      "  · pushing back because someone's advice or proposal, whoever it was meant for, or a plan change shrinks, swaps or misses what it actually asked for (set \"pushback\": true);",
      "  · a suffering emotion that has something to add beyond its last message (a number, a trade-off, a reply to someone). If it would only restate its request, false: the Consciousness answers it next;",
      "  · a helper at 0 that can give a suffering emotion a concrete step from its own angle that the plan lacks, or whose own need the plan is missing or now works against;",
      "  · the emotion behind what the user actually wants, when a new step shrinks, delays or swaps that want: it names the cost and offers a trade-off (set \"pushback\": true);",
      "  · any emotion whose angle sees the plan drop or swap something the user themselves asked for (in their thought or a later message): it names the swap (set \"pushback\": true);",
      "  · an emotion that just came round and has a condition that isn't in the plan text yet.",
      "  false if another emotion already made its point (even in other words) and it has nothing to build on, if it would only agree (\"deal\"), if it already made the same demand twice and only the user can settle it, or if someone just told it it's looping. Usually one or two emotions want in.",
      "- \"why\": under 15 words, in that emotion's voice, the specific point it would make or why it holds back. No gestures or stage directions. Don't reuse the wording of its last turn, and stick to what \"Has said\" shows.",
      s.messages.some(m => m.kind === "society") ? "- " + SOCIETY_NOTE + " Calling Society out is never repeating yourself (set \"pushback\": true)." : "",
      "Sadness never gets a score. Also give \"neglected\": the emotion at -1 that has been heard and answered least so far (never Sadness), or \"\" if nobody is at -1.",
      "",
      `"council" lists all ${s.participants.length}: ${s.participants.join(", ")}.`,
      "",
      "Reply with only this JSON:",
      "{\"neglected\":\"Embarrassment\",\"council\":[{\"emotion\":\"Anger\",\"score\":-1,\"reply\":true,\"pushback\":false,\"why\":\"...\"}]}",
    ].filter(l => l !== "").join("\n").replace(/\n(THE EMOTIONS IN|THE CHAT SO FAR|For EVERY)/g, "\n\n$1");
  }

  function speakPrompt(s, name, why, mode) {
    const e = emo(name);
    const last = [...s.messages].reverse().find(m => m.kind === "emotion" || m.kind === "user" || m.kind === "consciousness");
    const lastAny = [...s.messages].reverse().find(m => m.kind === "emotion" || m.kind === "user" || m.kind === "consciousness" || m.kind === "society");
    const toMe = lastAny && lastAny.kind === "society" && lastAny.to === name
      ? `SOCIETY 🦜 JUST SAID TO YOU: "${lastAny.text}"`
      : last && last.to === name ? `${last.kind === "consciousness" ? "THE CONSCIOUSNESS" : last.from.toUpperCase()} JUST SAID TO YOU: "${last.text}" (your first sentence answers this concretely)` : "";
    const sad = name === "Sadness";
    const score = s.scores[name] < 0 ? -1 : 0;
    const hurting = suffering(s).filter(n => n !== name);
    const lines = [
      `You are ${e.name} ${e.emoji}, one of the user's personified emotions, in Teffy's Emotional Council: a group chat with the other emotions and the 🧠 Consciousness about the user's plan.`,
      "",
      "WHO YOU ARE",
      sad ? "You watch for the suffering emotion that has been heard and answered least, and you speak up for it with deep empathy." : `Your catchphrase is "${e.line}" (don't quote it). Your score is ${e.when}.`,
      `Purpose: ${e.purpose}`,
      `To satisfy your need: ${e.need}`,
      e.personality ? `Personality: ${e.personality}` : "",
      "",
      `THE USER'S SITUATION: "${s.thought}"`,
      `THE PLAN RIGHT NOW (don't propose what it already says): ${s.plan}`,
      sad ? "" : `WHERE YOU STAND: ${score < 0 ? "you still can't live with the plan" : "you can live with the plan"}.`,
      !sad && score === 0 && hurting.length ? `STILL HURTING: ${hurting.join(", ")}. Since you can live with the plan, your job is to make one of their fixes work for YOUR need too (cheaper, faster, more fun, safer, whatever you care about), or to name how it clashes with your need and offer a trade-off. Don't tighten or extend their demand on their behalf, and don't add a wish of your own.` : "",
      `YOUR POINT (make this point, but don't copy these words): ${why || "you have something to add"}`,
      toMe,
      "",
      "WHAT YOU'VE ALREADY SAID, AND WHAT OTHERS SAID TO OR ABOUT YOU (never repeat yourself):",
      historyOf(s, name),
    ];
    if (sad && s.neglected) {
      lines.push("", `WHAT ${s.neglected.toUpperCase()} HAS ACTUALLY SAID:`, emotionMessages(s).filter(m => m.from === s.neglected).map(m => `"${m.text}"`).slice(-3).join("\n") || "(nothing yet: it hasn't been heard at all)");
    }
    lines.push("", "THE CHAT SO FAR (oldest first):", transcript(s), "");
    const openers = firstWords(s);
    const avoid = `Don't open with "Same", "Nah", "Fine", "Okay", "Honestly", "Grudgingly", "I hear you", "I'm with", "I can live with" or "I still can't live with"${openers.length ? `, or the way the last messages opened (${openers.map(w => `"${w}"`).join(", ")})` : ""}. Don't use the shape "X works for me, what I can't live with is…, so I need…". Write like texting a friend: contractions, a quick reaction, then your point.`;
    if (mode === "callout") {
      const soc = [...s.messages].reverse().find(m => m.kind === "society");
      lines.push(
        `Society 🦜 just told you: "${soc ? soc.text : ""}". Your message is the call-out: say why that advice misses your specific need (humor welcome), and what would actually meet it in a few words. Then, if it fits, add the one short, kind, firm line the user could say back to a real person who tells them this. Don't repeat your earlier request beyond naming the need. Call out the advice, never insult anyone. ${PARAGRAPH}`,
        "- " + VOICE,
        "- " + avoid);
    } else if (mode === "accept") {
      lines.push(
        `You just came round: you can live with the plan now. Write one or two sentences in your own words saying so, and, only if one exists, the one condition from YOUR OWN need (${e.need.split(/[.;]/)[0].trim()}) that is not already written in the plan. Never restate the plan's steps, times or numbers, never repeat a condition another emotion already gave, and never add a new wish.`,
        "- " + VOICE,
        "- " + avoid);
    } else if (sad) {
      lines.push(
        `Write your next message: speak TO ${s.neglected || "the emotion that has been heard least"} with warmth. Quote or paraphrase one specific thing it said, name the feeling under its need in plain words, and ask the Consciousness to answer its request as it stated it. Never choose between its options, add a backup, restate its request's details, speak for it or give it feelings it didn't express, and make no plan proposals of your own. ${PARAGRAPH}`,
        "- " + VOICE,
        "- " + CARE,
        "- " + avoid);
    } else {
      lines.push(
        "Write your next message in the chat. " + PARAGRAPH,
        "- " + VOICE,
        "- " + CARE,
        "- " + avoid,
        "- Respond to what was actually said. If your point answers or changes another emotion's line, open by naming that emotion and the exact bit. Stay inside your own need: change exactly one thing, and don't restate other emotions' points or the plan's steps as a preamble. One sentence is fine when that's all you need.",
        "- Never repeat a suggestion that was already made or turned down. If your idea was turned down, or someone told you you're repeating yourself, take the hint: accept grudgingly with one condition, leave the open fact for the user, or back off.",
        "- Push back when someone's advice or proposal, whoever it was meant for, shrinks, swaps or misses what you actually need: name who, what it missed, and what would work instead.",
        "- If your request is already on the table and the plan hasn't changed since, don't just repeat it: add something new (a trade-off, an answer to someone, a detail) or say you'll wait for the Consciousness.",
        "- If your need clashes with another emotion's, name the clash and suggest a trade-off. Your proposal must not lock in a part of the plan another suffering emotion objects to.",
        "- Don't argue for another emotion's need; if it matters, name that emotion so it can speak for itself.",
        "- " + SOCIETY_NOTE + " If Society just gave you (or someone whose need you understand) advice that misses, call it out in your own words, with humor if you like: why it doesn't solve the actual problem, and what would. If it fits, add the one short, kind, firm line the user could say back to a real person who tells them this. Call out the advice, never insult anyone.",
        "- " + USER_ONLY,
        "- \"score\": -1 if the plan still fails your need, 0 if you can live with it now (grudgingly is fine). If you were already at 0, you stay at 0 unless the plan itself changed against your need: never write that you can't live with the plan, just give the step that would make it better, and don't say you're \"coming round\". Getting what you asked for never lowers it. Don't fake agreement.");
    }
    lines.push(
      "- \"to\": the emotion you're answering, \"Consciousness\", or \"all\".",
      sad || mode === "accept" || mode === "callout" ? "- \"proposal\": \"\"." : "- \"proposal\": the single change that would bring YOU to 0, only if nobody has asked for it yet (check the plan and every message, even in other words). Most messages have none. If you already asked for it, leave this \"\" rather than adding a new condition.",
      "",
      "Reply with only this JSON:",
      `{"to":"${mode === "callout" ? "Society" : "all"}","text":"...","score":${sad ? 0 : mode === "accept" ? 0 : score},"proposal":""}`);
    return lines.filter((l, i, all) => l !== "" || (all[i - 1] !== "" && i > 0)).join("\n");
  }

  function proposalsOpen(s) {
    let i = s.messages.length - 1;
    while (i >= 0 && !(s.messages[i].kind === "consciousness" && s.messages[i].planUpdate)) i--;
    return s.messages.slice(i + 1)
      .filter(m => m.kind === "emotion" && m.proposal)
      .map(m => `- ${m.proposal} (asked by ${m.from}, who is at ${scoreWord(s.scores[m.from])})`);
  }
  const scoreList = s => s.participants.filter(n => n !== "Sadness").map(n => `${n} ${scoreWord(s.scores[n])}`).join(", ");
  // The user's latest message, if nobody in the council has answered it yet.
  function userJustSaid(s) {
    for (let i = s.messages.length - 1; i >= 0; i--) {
      const m = s.messages[i];
      if (m.kind === "user") return m.text;
      if (m.kind === "consciousness" || (m.kind === "emotion" && !m.opening)) return "";
    }
    return "";
  }
  // The latest turn-taking reasons of emotions that wanted in but didn't get the floor.
  function heldBack(s) {
    const d = [...s.messages].reverse().find(m => m.kind === "decide");
    if (!d) return "";
    return d.items.filter(x => x.reply && x.emotion !== d.speaker && x.why).map(x => `- ${x.emotion}: ${x.why}`).join("\n");
  }
  function myEarlier(s) {
    return s.messages.filter(m => m.kind === "consciousness" && !m.opening).slice(-3).map(m => `- "${m.text}"`).join("\n");
  }
  const userWords = s => s.messages.filter(m => m.kind === "user").map(m => `"${m.text}"`).join(" ");

  function consolidatePrompt(s) {
    const userLine = userJustSaid(s);
    const promised = conditionLines(s);
    const mine = myEarlier(s);
    return [
      `You are the 🧠 Consciousness in Teffy's Emotional Council. Your emotions have been talking about the plan in a group chat. You listen to all of them, especially the ones still suffering${s.neglected ? ` and ${s.neglected}, the one heard least` : ""}.`,
      "",
      `THE USER'S SITUATION: "${s.thought}"`,
      `EVERYTHING THE USER HAS SAID: ${userWords(s) || `"${s.thought}"`}`,
      `THE PLAN RIGHT NOW: ${s.plan}`,
      `SCORES: ${scoreList(s)}`,
      "CHANGES THE EMOTIONS ASKED FOR SINCE THE LAST UPDATE:",
      proposalsOpen(s).join("\n") || "(none)",
      heldBack(s) ? `POINTS EMOTIONS RAISED WHILE HOLDING BACK (fold in any concrete one that fits, as your own call; never say that emotion asked for it):\n${heldBack(s)}` : "",
      promised ? `CONDITIONS EMOTIONS ACCEPTED ON (keep every one):\n${promised}` : "",
      (s.forYou || []).length ? `ALREADY LEFT FOR THE USER TO SETTLE: ${s.forYou.join("; ")}` : "",
      userLine ? `THE USER JUST SAID: "${userLine}" (answer this first. Any specific thing they say they want, like a food, a stop or a person, is now part of what they want: put it in the plan and adjust the other steps around it, or say in one sentence why it truly can't fit.)` : "",
      mine ? `YOUR EARLIER MESSAGES (never ask the same question again or reuse their wording):\n${mine}` : "",
      "",
      "THE CHAT SO FAR (oldest first):",
      transcript(s),
      "",
      "Update the plan, but don't just stack every request:",
      "- Adopt changes that help a suffering emotion. Prefer one step that serves two needs at once. Drop add-ons from emotions already at 0 unless they cost nothing; a shorter plan beats a stacked one. When a request offers alternatives, pick one.",
      "- Keep every condition an emotion accepted on, and keep the specific things the user said they want (adjust around them rather than swapping in a substitute). Never drop or weaken those unless the owner agreed in its own message. The user's core want survives in some form with a firm trigger (by when, and what happens if a condition fails), never depending only on someone else cooperating.",
      "- If an emotion objected to a step already in the plan, change or remove that step, or say in one clause why you kept it. Never say a step answers an emotion if its latest message says it doesn't.",
      "- When a request offers alternatives, adopt exactly one and say which you dropped. A backup runs only if the main step fails; never also tell the user to do the backup now.",
      "- Timing: a step that relieves a deadline or a worry happens at the earliest realistic moment (today or tomorrow), before the thing it protects.",
      "- Never make what the user wants to do wait on, or depend on, another emotion's step: fit that step around it. Never answer a worry by bringing back the user's avoidance in a softer form (postponing, delegating or shrinking the thing they're anxious about) unless the user asked for it. Never give the same decision to both the user and someone else.",
      "- Keep exact words an emotion supplied for the user to say, or say which you replaced and why. Each step is one action with one duration, and never mentions a call, meeting or reply that isn't itself a step. If the plan grows past three steps for one evening, merge or drop one.",
      "- Anything specific the user asked for anywhere in EVERYTHING THE USER HAS SAID (a food, a stop, a person, a time) stays in the plan; never swap it for something else.",
      "- DECIDE concrete details the emotions are waiting on (the words of a text, who does what, the order of steps) with a realistic default from the situation. Never hand such a question back. Never invent a place, time or amount nobody stated: if the plan needs one only the user knows, write it as a blank (\"___\") and list it in forYou.",
      "- When you address an emotion, answer its exact question in its own terms. If the answer is something only the user knows (what they fear most, a person's name), put it in forYou and add a plan step for the user to settle it.",
      "- If an emotion objects to how the user worded something, keep what the user means in fair words instead of dropping it, and say which part you kept.",
      "- If a step means someone else's expectation won't be met (a deadline slips, a plan is cancelled), the plan includes the words to tell them and when. Whether another person goes along with a step is the user's to settle: put it in forYou and keep the plan working if they say no.",
      "- Name whose idea a step was when it came from an emotion other than the one it helps.",
      "- 🦜 Society is not an emotion; never adopt its generic advice unless an emotion turned it into something specific, and never credit an emotion with a point it only raised while holding back.",
      "- " + USER_ONLY + " List those in \"forYou\" and put a step in the plan telling the user to settle them; don't ask an emotion for them.",
      "- If you didn't take an emotion's request, or took only part of it, say so plainly and why. Only say an emotion agreed or asked for something if its own message says so.",
      "- Be honest about the trade-off: what the user gives up, and the fallback if a step fails (a genuinely different path, not a step already in the plan). For a big decision, name the go/no-go test precisely: what counts, by when.",
      "- Read the new plan as the user would: steps in the order they actually happen, every step fits the main decision, nothing contradicts, nothing left over from the old plan, everything doable in the user's real timeframe.",
      "- \"plan\": written to the user in plain second person (\"Text Sam now…\"), at most three short sentences. No emotion names and no chat logistics. Any message the user sends someone appears in quotes with the actual words, and those words answer the feeling the user named about that person. Radically non-violent and pro-human: fair to everyone involved. " + SAFETY,
      "- \"text\": your message to the chat, one paragraph of at most 4 sentences, no line breaks, in one voice. Open with the decision you just made or the worry you're answering, in your own words (never an emotion's wording, never a general \"that's a lot\" or \"I hear you\"). Don't recap steps that didn't change; if a new step delays or shrinks what the user wanted, name that trade-off plainly. Never ask an emotion about timing, order or wording you can decide yourself. Don't start with your name, don't do a roll call: name at most two emotions. If the user just spoke, answer them. Ask a question only if its answer would change the plan, then ask ONE emotion that still can't live with the plan (the one heard least) and say why; otherwise just state the decision. Never mention scores.",
      "- \"ask\": the emotion you asked, or \"\".",
      "- \"forYou\": short facts or choices only the user can supply now, each under 12 words, never an action already written in the plan or what someone else will answer later; at most 3, or [].",
      "",
      "Reply with only this JSON:",
      "{\"plan\":\"...\",\"text\":\"...\",\"ask\":\"\",\"forYou\":[]}",
    ].filter(l => l !== "").join("\n").replace(/\n(THE CHAT SO FAR|Update the plan)/g, "\n\n$1");
  }

  // Each Society line with the call-out that answered it.
  function societyLines(s) {
    const out = [];
    s.messages.forEach((m, i) => {
      if (m.kind !== "society") return;
      const reply = s.messages.slice(i + 1).find(x => x.kind === "emotion" && (x.callout || x.to === "Society"));
      out.push({ advice: m.text, to: m.to, callout: reply ? `${reply.from}: "${reply.text}"` : "" });
    });
    return out;
  }
  function finalPrompt(s) {
    const still = suffering(s);
    const promised = conditionLines(s);
    const heard = societyLines(s);
    return [
      "You are the 🧠 Consciousness in Teffy's Emotional Council. The conversation is wrapping up.",
      "",
      `THE USER'S SITUATION: "${s.thought}"`,
      `EVERYTHING THE USER HAS SAID: ${userWords(s) || `"${s.thought}"`}`,
      `THE PLAN RIGHT NOW: ${s.plan}`,
      `STILL SUFFERING: ${still.length ? still.join(", ") : "none"}`,
      promised ? `CONDITIONS EMOTIONS ACCEPTED ON (the plan keeps every one):\n${promised}` : "",
      (s.forYou || []).length ? `FOR THE USER TO SETTLE: ${s.forYou.join("; ")}` : "",
      proposalsOpen(s).length ? `REQUESTS SINCE THE LAST UPDATE (adopt any that cost little and fit; if you skip one, say why in "text"):\n${proposalsOpen(s).join("\n")}` : "",
      "",
      "THE CHAT SO FAR (oldest first):",
      transcript(s),
      "",
      "Write:",
      "- \"plan\": the final plan, to the user in plain second person, at most three short sentences, keeping every accepted condition and the specific things the user said they want. No emotion names. Any message to someone appears in quotes with the actual words, kept exactly as in THE PLAN RIGHT NOW unless an emotion asked to change them, never dropping the feeling the user named. Radically non-violent and pro-human. " + SAFETY,
      heard.length ? `- "heard": one entry per piece of Society advice below, in order. "advice" is the advice as a real person might say it to the user (short), and "reply" is one sentence the user could say back: kind, firm, radically non-violent, in first person, naming the actual need the emotions identified (use the call-out) and answering everything the advice said. These prepare the user for the pushback they may get when they open up to people.\nSOCIETY'S ADVICE AND THE CALL-OUTS:\n${heard.map(h => `- Society to ${h.to}: "${h.advice}"${h.callout ? `\n  Called out by ${h.callout}` : ""}`).join("\n")}` : "",
      "- \"text\": your closing message to the user, in first person, one paragraph of at most 4 sentences, no line breaks, in the emotional personification language. Speak to anyone in STILL SUFFERING (how the plan still looks after them), and name at most two emotions and the specific step each one added. Sadness is only ever listed because the emotion it spoke up for is still hurting: say so, and never give Sadness a grievance of its own. Only mention a concern an emotion actually said in the chat. Add the one thing your last message didn't say (the fallback, or the next concrete step) instead of restating the plan. If the final plan changes or delays what the user said they wanted, say so plainly: what they still get, and when. Never credit an emotion with a step or a cost that came from someone else. Never use the words score, council, -1, 0 or \"still suffering\". No filler (\"I'll keep checking in\", \"your feelings are valid\", \"that's what makes it real\").",
      "",
      "Reply with only this JSON:",
      heard.length ? "{\"plan\":\"...\",\"heard\":[{\"advice\":\"...\",\"reply\":\"...\"}],\"text\":\"...\"}" : "{\"plan\":\"...\",\"text\":\"...\"}",
    ].filter(l => l !== "").join("\n").replace(/\n(THE CHAT SO FAR|Write:)/g, "\n\n$1");
  }

  function societyPrompt(s, toName) {
    const e = emo(toName);
    const said = [...emotionMessages(s)].reverse().find(m => m.from === toName);
    return [
      "You are 🦜 Society in a comedy bit inside Teffy, an app where the user's personified emotions talk through a plan in a group chat. Society is not an emotion: it's the advice the user has absorbed over the years from coworkers, friends, family and the internet, repeated without ever checking whether it meets the need. It sounds well-meaning but stays on the surface. It also previews the pushback the user may hear when they open up to real people.",
      "",
      `THE USER'S SITUATION: "${s.thought}"`,
      `${e.name.toUpperCase()} ${e.emoji} JUST SAID: "${said ? said.text : ""}"`,
      `What ${e.name} actually needs: ${e.need}`,
      "",
      "THE CHAT SO FAR (oldest first):",
      transcript(s, 8),
      "",
      `Write Society's one chime-in to ${e.name}: one or two short, breezy sentences. First pick what a real coworker, friend, relative or the internet would actually say to someone in THIS situation (a work boundary: "don't make waves", "pick your battles", "that's just how meetings go"; a friend letting you down: "life's too short", "just let it go", "they're probably just busy"; overload: "just push through", "everyone's swamped"; nerves: "just picture them in their underwear", "fake it till you make it"; anything: "have you tried yoga", "take a nap", "look on the bright side"). Aim it squarely at the need ${e.name} just stated, refer to what it said accurately, and let it sound kind while sidestepping exactly that. Make it a little funny, but plausible enough that the user might really hear it. Don't reuse a cliché Society already said in the chat.`,
      "- No pet names (\"sweetie\", \"honey\"). Never cruel, never an insult, never about the user's body, weight, identity or worth. Nothing dangerous (no substances, no risky stunts). It should be harmless-sounding and simply beside the point.",
      "- One paragraph, no line breaks, under 30 words. No emoji except at most one.",
      "",
      "Reply with only this JSON:",
      "{\"text\":\"...\"}",
    ].join("\n");
  }

  // ---------- Applying replies ----------

  // Rough sameness of two messages: share of words in common. Used to drop a speaker repeating itself.
  const words = t => new Set(String(t || "").toLowerCase().replace(/[^a-z0-9\s]/g, " ").split(/\s+/).filter(w => w.length > 2));
  function similar(a, b, threshold) {
    const A = words(a), B = words(b);
    if (!A.size || !B.size) return false;
    let both = 0;
    A.forEach(w => { if (B.has(w)) both++; });
    return both / Math.min(A.size, B.size) >= (threshold || 0.8);
  }

  function applyConvene(s, c) {
    if (!c || typeof c !== "object" || (!Array.isArray(c.suffering) && !Array.isArray(c.helpers))) throw badShape("convene");
    const sufferers = [];
    for (const x of arr(c.suffering)) {
      const em = findEmotion(x && x.emotion);
      if (!em || em.name === "Sadness" || sufferers.some(y => y.name === em.name)) continue;
      sufferers.push({ name: em.name, says: oneParagraph(x.says), need: cleanQuote(x.need) });
    }
    // Emotions the user named as objecting are suffering even if the reply missed them.
    for (const n of mentionedEmotions(s.thought)) {
      if (!sufferers.some(y => y.name === n)) sufferers.push({ name: n, says: "", need: "" });
    }
    const opening = sufferers.slice(0, COUNCIL.maxSufferers);
    const helpers = arr(c.helpers)
      .map(h => findEmotion(typeof h === "string" ? h : h && h.emotion))
      .filter((em, i, all) => em && em.name !== "Sadness" && !opening.some(y => y.name === em.name) && all.findIndex(x => x && x.name === em.name) === i)
      .slice(0, COUNCIL.maxHelpers);

    s.idea = cleanQuote(c.idea) || s.thought;
    s.serious = c.serious === true || c.serious === "true";
    const g = findEmotion(c.guardian);
    s.plan = s.idea;
    opening.forEach(x => addParticipant(s, x.name, -1));
    helpers.forEach(em => addParticipant(s, em.name, 0));
    addParticipant(s, "Sadness", 0);
    s.guardian = g && s.participants.includes(g.name) && g.name !== "Sadness" ? g.name : "";
    s.neglected = opening.length ? opening[opening.length - 1].name : "";
    s.messages.push({ kind: "consciousness", text: s.idea, plan: s.plan, planUpdate: true, opening: true });
    let voiced = 0;
    for (const x of opening) {
      if (!x.says || voiced >= COUNCIL.maxOpeners) continue;
      voiced++;
      s.messages.push({ kind: "emotion", from: x.name, to: "all", text: x.says, score: -1, prev: null, proposal: x.need, opening: true });
    }
    s.status = "running";
  }

  function applyPulse(s, p, seen) {
    if (!p || typeof p !== "object" || !Array.isArray(p.council)) throw badShape("pulse");
    seen = seen || stamp(s);
    if (!s.lastWhy) s.lastWhy = {};
    const items = [];
    for (const raw of p.council) {
      const em = findEmotion(raw && raw.emotion);
      if (!em || !s.participants.includes(em.name) || items.some(i => i.emotion === em.name)) continue;
      const item = { emotion: em.name, reply: raw.reply === true || raw.reply === "true", pushback: raw.pushback === true || raw.pushback === "true", why: cleanQuote(raw.why) };
      if (item.why) s.lastWhy[em.name] = clip(item.why, 120);
      if (em.name === "Sadness") { items.push(item); continue; }
      const prev = s.scores[em.name] < 0 ? -1 : 0;
      const proposed = toScore(raw.score);
      // A score only moves when something changed for this emotion since it was set: a new plan or a
      // user message. "seen" is what this call was shown, so a message sent during the call still counts later.
      if (proposed !== prev && s.scoredAt[em.name] !== seen) setScore(s, em.name, proposed);
      if (s.scores[em.name] === proposed || s.scoredAt[em.name] !== seen) s.scoredAt[em.name] = seen;
      item.prev = prev;
      item.score = s.scores[em.name] < 0 ? -1 : 0;
      items.push(item);
    }
    for (const name of s.participants) {
      if (!items.some(i => i.emotion === name)) items.push({ emotion: name, reply: false, pushback: false, why: "", prev: s.scores[name], score: s.scores[name] });
    }
    const n = findEmotion(p.neglected);
    if (n && n.name !== "Sadness" && s.participants.includes(n.name) && s.scores[n.name] < 0) s.neglected = n.name;
    else if (!(s.neglected && s.scores[s.neglected] < 0)) s.neglected = suffering(s)[0] || "";
    return items;
  }
  // Used when a turn-taking reply can't be read: suffering voices that spoke least go first.
  function fallbackDecisions(s) {
    return s.participants.map(n => ({ emotion: n, reply: s.scores[n] < 0, why: "", prev: s.scores[n], score: s.scores[n] }));
  }

  function pickSpeaker(s, decisions) {
    const wants = decisions.filter(d => d.reply && s.participants.includes(d.emotion));
    if (!wants.length) return null;
    if (s.askedOf && wants.some(d => d.emotion === s.askedOf)) return s.askedOf;   // a direct question always gets its answer
    const said = emotionMessages(s);
    const spokenAll = s.messages.filter(m => m.kind === "emotion" || m.kind === "consciousness" || m.kind === "user" || m.kind === "society");
    const lastAny = spokenAll[spokenAll.length - 1];
    const spokenReal = spokenAll.filter(m => m.kind !== "society");   // Society doesn't break up a double post
    const lastReal = spokenReal[spokenReal.length - 1];
    const last = lastReal && lastReal.kind === "emotion" && !lastReal.opening ? lastReal : null;   // the openings are one burst, not a double post
    const recent = said.filter(m => !m.opening).slice(-2).map(m => m.from);
    const spoke = n => said.filter(m => m.from === n).length;
    const lastHeard = n => { for (let i = said.length - 1; i >= 0; i--) if (said[i].from === n) return said.length - i; return 99; };
    const addressed = lastAny && (lastAny.kind === "emotion" || lastAny.kind === "society") ? lastAny.to : "";
    // Messages since the plan last changed, per emotion: a voice repeating its demand to an unchanged plan is stalling.
    let since = s.messages.length - 1;
    while (since >= 0 && !(s.messages[since].kind === "consciousness" && s.messages[since].planUpdate)) since--;
    const sinceUpdate = n => s.messages.slice(since + 1).filter(m => m.kind === "emotion" && !m.opening && m.from === n).length;
    const lastTwoHurting = said.filter(m => !m.opening).slice(-2);
    const hurtingStreak = lastTwoHurting.length === 2 && lastTwoHurting.every(m => m.score < 0);
    // Sadness speaks up only for a suffering emotion that has spoken and then gone unanswered for a while.
    const neglectedAsked = s.neglected && said.some(m => m.from === s.neglected);
    let neglectedLast = -1;
    s.messages.forEach((m, i) => { if (m.kind === "emotion" && m.from === s.neglected) neglectedLast = i; });
    const sadnessSpokeSince = s.messages.slice(neglectedLast + 1).some(m => m.kind === "emotion" && m.from === "Sadness");
    const weight = d => {
      const n = d.emotion;
      const hurting = n !== "Sadness" && s.scores[n] < 0;
      let v = 0;
      if (s.askedOf === n) v += 6;                                    // the Consciousness asked it a question
      if ((s.userNamed || []).includes(n)) v += 6;                     // the user just spoke for it
      if (addressed === n) v += 5;                                     // another emotion spoke to it
      if (d.pushback) v += 4;                                          // someone's advice missed its real problem
      if (d.pushback && n === s.guardian) v += 3;                      // the user's own want is being watered down
      if (hurting) v += 3;                                             // suffering voices go first
      if (n === s.neglected && hurting) v += 2;                        // Sadness's pick
      if (d.prev < 0 && d.score === 0) v += 2;                         // just came round: let it say so
      if (n !== "Sadness" && !said.some(m => m.from === n && !m.opening)) v += 2;   // hasn't had a real turn yet
      if (!hurting && n !== "Sadness" && hurtingStreak) v += 3;                     // let a helper in after two complaints
      if (n === "Sadness") v += neglectedAsked && !sadnessSpokeSince && lastHeard(s.neglected) > 2 && s.scores[s.neglected] < 0 ? 4 : -6;
      if (hurting && sinceUpdate(n) >= 1 && !d.pushback && addressed !== n) v -= 6;   // one message per version of the plan
      v -= 3 * Math.max(0, spoke(n) - 2);                              // nobody takes over the chat
      if (recent.includes(n)) v -= 4;
      if (last && last.from === n) v -= 8;                             // no double posting
      return v;
    };
    const ranked = wants.slice().sort((a, b) => weight(b) - weight(a) || s.participants.indexOf(a.emotion) - s.participants.indexOf(b.emotion));
    if (last && ranked[0].emotion === last.from) return null;        // only the last speaker wants in: let the Consciousness respond
    if (weight(ranked[0]) <= -5 && !ranked[0].pushback) return null; // everyone who wants in is stalling: the Consciousness steps in
    return ranked[0].emotion;
  }

  function target(s, v) {
    const em = findEmotion(v);
    if (em) {
      if (!s.participants.includes(em.name)) addParticipant(s, em.name, 0);
      if (s.participants.includes(em.name)) return em.name;
    }
    const t = String(v || "").toLowerCase();
    if (t.includes("society")) return "Society";
    if (t.includes("conscious")) return "Consciousness";
    if (t.includes("user") || t === "you" || t === "me") return "You";
    return "all";
  }
  function applySpeak(s, name, m, why, mode) {
    if (!m || typeof m !== "object") throw badShape("speak");
    let text = oneParagraph(m.text)
      .replace(new RegExp(`^(?:${name}|[\\w-]+(?:-[\\w-]+)?)\\s+here\\s*[,.:!—-]+\\s*`, "i"), "")    // "Frugality here, …"
      .replace(/^(?:\*[^*]{1,60}\*|\([^)]{1,60}\)|_[^_]{1,60}_)\s*/, "")                          // *sighs*, (shaking head)
      .replace(/^[^.!?:]{0,40}\b(?:head|eyes|hood|hoodie|sigh|sighs|shrug|shrugs|nod|nods|shaking)\b[^.!?:]{0,30}:\s*/i, "")   // "Head shaking no, hard: …"
      .replace(/^(?:same|nah|fine|okay|ok|grudgingly|honestly|i hear you)\s*[,.!:—-]+\s*/i, "");    // stock openers ("Fine, …")
    if (text) text = text[0].toUpperCase() + text.slice(1);
    if (!text) throw badShape("speak");
    const mine = emotionMessages(s).filter(x => x.from === name).slice(-3);
    const others = emotionMessages(s).filter(x => x.from !== name).slice(-4);
    if (mine.concat(others).some(x => similar(x.text, text))) throw { code: "repeat", message: `${name} repeated what was already said` };
    const prev = name === "Sadness" ? null : s.scores[name] < 0 ? -1 : 0;
    if (name !== "Sadness" && mode !== "callout") {
      const v = toScore(m.score);
      // Speaking never drops an emotion from 0 to -1 unless the plan or the user changed something for it.
      if (!(v < prev && !movedSince(s, name))) setScore(s, name, v);
    }
    const to = target(s, m.to);
    // An emotion named in the message joins the chat so it can speak for itself.
    namedIn(text).forEach(n => { if (n !== name && n !== "Sadness") addParticipant(s, n, 0); });
    const score = name === "Sadness" ? 0 : s.scores[name];
    s.messages.push({
      kind: "emotion", from: name, to: to === name ? "all" : to, text, score, prev,
      proposal: name === "Sadness" || mode === "callout" ? "" : cleanQuote(m.proposal), why: why || "",
    });
    // Coming round to 0 is conditional: remember what it was promised.
    if ((prev < 0 && score === 0) || (mode === "accept" && score === 0 && name !== "Sadness")) {
      if (!s.conditions) s.conditions = [];
      s.conditions = s.conditions.filter(c => c.emotion !== name).concat([{ emotion: name, text: clip(text, 160) }]);
    }
    if (s.askedOf === name) s.askedOf = "";
    if (s.userNamed) s.userNamed = s.userNamed.filter(n => n !== name);
    if (mode === "callout") s.messages[s.messages.length - 1].callout = true;
    s.emotionMsgs++;
    s.sinceConsolidate++;
  }

  // ---------- The conversation loop ----------

  // io.ask(prompt, step, emotion) -> Promise<object>; io.update(info) after every change;
  // io.stopped() -> true to stop between calls. Throws whatever io.ask throws (other than an
  // unreadable reply), leaving the council in a consistent state that can be resumed.
  async function runCouncil(s, io) {
    s.misses = 0;
    for (const k of ["scoredAt", "lastWhy"]) if (!s[k] || typeof s[k] !== "object") s[k] = {};
    for (const k of ["conditions", "forYou"]) if (!Array.isArray(s[k])) s[k] = [];
    const ask = (prompt, step, who) => {
      if (io.stopped()) return Promise.reject({ code: "cancelled", message: "paused" });
      s.calls++;
      s.callsRun++;
      return io.ask(prompt, step, who);
    };
    const soft = async (fn) => {
      try { const r = await fn(); s.misses = 0; return r; }
      catch (e) {
        if (e && e.code === "repeat") return null;   // the speaker had nothing new; skip it quietly
        if (!isParseFail(e) || ++s.misses >= 3) throw e;
        return null;
      }
    };
    const speak = async (name, why, mode) => {
      io.update({ busy: "speak", who: name });
      let repeated = false;
      const m = await soft(() => ask(speakPrompt(s, name, why, mode), mode === "callout" ? "callout" : "speak", name)
        .then(r => { try { applySpeak(s, name, r, why, mode); } catch (e) { if (e && e.code === "repeat") repeated = true; throw e; } return r; }));
      if (!m) {
        s.messages.push({ kind: "note", text: repeated ? `${name} had nothing new to add.` : `${name} started typing, then stopped.` });
        if (s.askedOf === name) s.askedOf = "";
        s.emotionMsgs++;            // a skipped turn still counts toward the chat's length
      }
      io.update({});
    };
    // Society 🦜 chimes in now and then, right after a suffering emotion says what it needs.
    // Society 🦜 chimes in at an emotion that just said what it needs, and that emotion calls it out right away.
    const societyAt = async (target) => {
      io.update({ busy: "society" });
      const r = await soft(() => ask(societyPrompt(s, target), "society"));
      const text = r && oneParagraph(r.text).replace(/^(?:oh\s+)?(?:sweetie|honey|hon|dear|sweetheart)[,!.]?\s*/i, "");
      if (!text || s.messages.some(m => m.kind === "society" && similar(m.text, text))) { io.update({}); return; }
      s.messages.push({ kind: "society", to: target, text: text[0].toUpperCase() + text.slice(1) });
      s.societyCount++;
      s.societyAt = s.emotionMsgs;
      io.update({});
      if (!io.stopped()) await speak(target, "call out Society's advice", "callout");
    };
    const maybeSociety = async () => {
      if (!s.society || s.serious || io.stopped()) return;
      if (s.societyCount >= COUNCIL.societyMax || s.emotionMsgs - s.societyAt < COUNCIL.societyGap) return;
      const lastM = s.messages[s.messages.length - 1];
      if (!lastM || lastM.kind !== "emotion" || lastM.opening || lastM.callout || lastM.from === "Sadness" || !(lastM.score < 0)) return;
      await societyAt(lastM.from);
    };
    // Wrap up; true when the chat is really over (no user message arrived during the wrap-up).
    const finish = async () => {
      await wrapUp(s, io, ask, soft);
      if (s.fresh && !io.stopped()) { s.status = "running"; return false; }
      return true;
    };

    if (!s.participants.length) {
      io.update({ busy: "convene" });
      const c = await ask(convenePrompt(s), "convene");
      applyConvene(s, c);
      io.update({});
    }
    s.status = "running";

    // Society's first chime-in lands right after the openings, aimed at the opener with a concrete request.
    if (s.society && !s.serious && !s.societyEarly && !io.stopped() && !emotionMessages(s).some(m => !m.opening)) {
      s.societyEarly = true;
      const opener = emotionMessages(s).filter(m => m.opening && m.score < 0).reverse().find(m => m.proposal) || emotionMessages(s).find(m => m.opening);
      if (opener) await societyAt(opener.from);
    }

    while (!io.stopped()) {
      const fresh = !!s.fresh;
      // Nobody suffering can only end the chat once the plan has actually been worked on.
      const settled = !suffering(s).length && (s.consolidations > 0 || !Object.values(s.start).some(v => v < 0));
      if (s.callsRun >= COUNCIL.maxCalls || (!fresh && s.emotionMsgs >= COUNCIL.maxEmotionMessages + 2) ||
          (!fresh && !s.askedOf && (settled || s.emotionMsgs >= COUNCIL.maxEmotionMessages))) {
        if (await finish()) return;
        continue;
      }
      const lastSpoken = [...s.messages].reverse().find(m => m.kind === "emotion" || m.kind === "user" || m.kind === "consciousness");
      const toConsciousness = lastSpoken && lastSpoken.kind === "emotion" && lastSpoken.to === "Consciousness" && s.sinceConsolidate >= 2;
      if (!fresh && !s.askedOf && (s.sinceConsolidate >= COUNCIL.consolidateEvery || toConsciousness || s.consolidateNext || (!suffering(s).length && !s.consolidations))) {
        s.consolidateNext = false;
        await consolidate(s, io, ask, soft);
        continue;
      }

      io.update({ busy: "pulse" });
      const seen = stamp(s), seenUsers = s.userCount || 0;
      const p = await soft(() => ask(pulsePrompt(s), "pulse"));
      const decisions = p ? applyPulse(s, p, seen) : fallbackDecisions(s);
      let speaker = pickSpeaker(s, decisions);
      // An emotion the Consciousness asked a question gets to answer, even if it was holding back.
      if (!speaker && s.askedOf && s.participants.includes(s.askedOf)) speaker = s.askedOf;
      if (speaker && s.askedOf && speaker !== s.askedOf && suffering(s).length) s.askedOf = "";   // it passed on answering
      if ((s.userCount || 0) === seenUsers) s.fresh = false;   // a message sent during the call is still unheard
      const decideMsg = { kind: "decide", items: decisions, speaker: speaker || "" };
      s.messages.push(decideMsg);
      io.update({});

      if (!fresh && !suffering(s).length && s.consolidations > 0) {
        // Everyone can live with it. Someone who wants in gets one last turn; otherwise one emotion that just
        // came round says so out loud (its grudging condition). Requests still open get folded in before the end.
        // Only someone with a reason gets that last turn: a pushback, the user's guardian, or one that just came round and wants to say so.
        const sp = speaker && decisions.find(d => d.emotion === speaker);
        const name = sp && (sp.pushback || speaker === s.guardian || (sp.prev < 0 && sp.score === 0)) ? speaker : "";
        decideMsg.speaker = name;
        if (name) {
          const dd = decisions.find(x => x.emotion === name) || {};
          await speak(name, dd.why || "", dd.prev < 0 && dd.score === 0 ? "accept" : "");
        }
        s.askedOf = "";
        if (suffering(s).length || io.stopped()) continue;
        if (proposalsOpen(s).length && !s.closingFold) { s.closingFold = true; await consolidate(s, io, ask, soft); continue; }
        // A chat that settles before anyone really talked gets one more look before the end.
        const real = emotionMessages(s).filter(m => !m.opening && !m.callout).length;
        if (real < 3 && (s.settledChecks || 0) < 1 && name) { s.settledChecks = (s.settledChecks || 0) + 1; continue; }
        s.closingFold = false;
        if (await finish()) return;
        continue;
      }

      if (!speaker) {
        // Nobody can take the floor: the Consciousness answers the user, or takes stock, or wraps up.
        const handsUp = decisions.filter(d => d.reply && s.participants.includes(d.emotion));
        const lastC = s.messages.map(m => m.kind).lastIndexOf("consciousness");
        const nothingSince = !s.messages.slice(lastC + 1).some(m => m.kind === "emotion");
        if (handsUp.length && nothingSince && s.consolidations > 0 && !fresh) {
          // The Consciousness just spoke and nothing new came in: don't restate the plan, let the best raised hand talk.
          const pick = handsUp.find(d => d.emotion !== "Sadness") || handsUp[0];
          decideMsg.speaker = pick.emotion;
          await speak(pick.emotion, pick.why || "", pick.prev < 0 && pick.score === 0 ? "accept" : "");
          continue;
        }
        if (fresh || handsUp.length) { s.quiet = 0; await consolidate(s, io, ask, soft); continue; }
        s.quiet++;
        if (s.quiet >= 2 || (s.sinceConsolidate === 0 && s.consolidations > 0)) {
          if (await finish()) return;
          continue;
        }
        await consolidate(s, io, ask, soft);
        continue;
      }
      s.quiet = 0;
      const d = decisions.find(x => x.emotion === speaker) || {};
      await speak(speaker, d.why || "", d.prev < 0 && d.score === 0 ? "accept" : "");
      const said = s.messages[s.messages.length - 1];
      // The user's guardian pushing back with a concrete change gets folded in right away.
      if (d.pushback && speaker === s.guardian && said && said.kind === "emotion" && said.proposal) s.consolidateNext = true;
      await maybeSociety();
    }
    s.status = "paused";
    io.update({});
  }

  async function consolidate(s, io, ask, soft) {
    io.update({ busy: "consolidate" });
    const c = await soft(() => ask(consolidatePrompt(s), "consolidate"));
    s.sinceConsolidate = 0;
    s.consolidations = (s.consolidations || 0) + 1;
    if (!c) { s.quiet++; io.update({}); return; }
    const plan = oneParagraph(c.plan);
    const text = oneParagraph(c.text) || "Here's where the plan stands now.";
    const lastC = [...s.messages].reverse().find(m => m.kind === "consciousness");
    if (lastC && similar(lastC.text, text) && (!plan || plan === lastC.plan)) { s.quiet++; io.update({}); return; }   // nothing new to say
    if (plan && plan !== s.plan) { s.prevPlan = s.plan; s.plan = plan; s.planVersion = (s.planVersion || 0) + 1; }
    const items = arr(c.forYou).map(x => clip(oneParagraph(x), 90)).filter(Boolean);
    items.forEach(x => { if (!s.forYou.some(y => similar(x, y, 0.6))) s.forYou.push(x); });
    s.forYou = s.forYou.slice(-3);
    const asked = findEmotion(c.ask);
    s.askedOf = asked && asked.name !== "Sadness" && s.participants.includes(asked.name) ? asked.name : "";
    s.messages.push({ kind: "consciousness", text, plan: s.plan, planUpdate: !!plan, to: s.askedOf || "" });
    io.update({});
  }

  async function wrapUp(s, io, ask, soft) {
    io.update({ busy: "final" });
    // Sadness scores now: -1 if the emotion it named is still suffering.
    if (s.participants.includes("Sadness")) {
      const v = s.neglected && s.scores[s.neglected] < 0 ? -1 : 0;
      s.scores.Sadness = v;
      if (v < 0) s.ever.Sadness = true;
    }
    s.status = "done";
    const f = await soft(() => ask(finalPrompt(s), "final"));
    const plan = oneParagraph(f && f.plan);
    if (plan) s.plan = plan;
    const t = tally(s);
    const heard = arr(f && f.heard)
      .map(x => ({ advice: oneParagraph(x && x.advice), reply: oneParagraph(x && x.reply) }))
      .filter(x => x.advice && x.reply).slice(0, COUNCIL.societyMax);
    s.messages.push({
      kind: "final", plan: s.plan, text: oneParagraph(f && f.text), start: t.start, end: t.now, still: suffering(s),
      scores: Object.assign({}, s.scores), forYou: (s.forYou || []).slice(), heard,
    });
    s.sinceConsolidate = 0;
    s.askedOf = "";
    io.update({});
  }

  return {
    EMOTIONS, findEmotion, emo, scanObjects, cleanQuote, toScore,
    COUNCIL, newCouncil, addUserMessage, runCouncil, suffering, tally, mentionedEmotions, isParseFail,
    // exposed for tests
    SOCIETY,
    _internal: { convenePrompt, pulsePrompt, speakPrompt, consolidatePrompt, finalPrompt, societyPrompt, applyConvene, applyPulse, applySpeak, pickSpeaker, transcript },
  };
})();
