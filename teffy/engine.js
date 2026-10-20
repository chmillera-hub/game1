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
  const emo = name => findEmotion(name) || { name: String(name), emoji: "•" };

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
    consolidateEvery: 4,     // the Consciousness updates the plan after this many emotion messages
    maxCalls: 40,            // Claude calls per stretch, a hard stop
    window: 16,              // chat lines each prompt sees
  };

  function newCouncil(thought) {
    return {
      thought: String(thought || "").trim(),
      status: "new",           // new | running | paused | done
      idea: "",
      plan: "",
      planVersion: 0,          // goes up each time the Consciousness changes the plan
      userCount: 0,            // goes up with each user message
      participants: [],
      scores: {},              // name -> -1 | 0, live
      scoredAt: {},            // name -> when its score was last set ("planVersion:userCount")
      start: {},               // name -> score when it joined
      ever: {},                // name -> true once it has been -1
      neglected: "",           // Sadness's current pick, always someone at -1
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

  function addUserMessage(s, text) {
    text = String(text || "").trim();
    if (!text) return;
    s.messages.push({ kind: "user", text });
    s.userCount = (s.userCount || 0) + 1;
    if (s.participants.length) mentionedEmotions(text).forEach(n => {
      if (!addParticipant(s, n, -1) && s.participants.includes(n)) setScore(s, n, -1);
    });
    // A user message opens a fresh stretch of conversation, and the council always hears it out.
    s.emotionMsgs = 0;
    s.callsRun = 0;
    s.quiet = 0;
    s.fresh = true;
    if (s.status === "done") s.status = "running";
  }

  // ---------- Prompt text ----------

  const who = n => (n === "Consciousness" ? "🧠 Consciousness" : n === "You" ? "the user" : `${emo(n).emoji} ${n}`);
  const scoreWord = v => (v < 0 ? "-1" : "0");

  function transcript(s, limit) {
    const lines = [];
    for (const m of s.messages) {
      if (m.kind === "user") lines.push(`User: ${m.text}`);
      else if (m.kind === "consciousness") lines.push(`🧠 Consciousness${m.to ? " → " + m.to : ""}: ${m.text}`);
      else if (m.kind === "emotion") lines.push(`${who(m.from)}${m.to && m.to !== "all" ? " → " + (m.to === "You" ? "user" : m.to) : ""}: ${m.text}`);
    }
    return lines.slice(-(limit || COUNCIL.window)).join("\n") || "(nobody has spoken yet)";
  }
  function saidBy(s, name) {
    const said = s.messages.filter(m => m.kind === "emotion" && m.from === name).map(m => m.text);
    if (!said.length) return "nothing yet";
    return said.slice(-2).map(t => `"${t.length > 90 ? t.slice(0, 87) + "…" : t}"`).join(" / ");
  }
  function historyOf(s, name) {
    const out = [];
    for (const m of s.messages) {
      if (m.kind === "emotion") {
        if (m.from === name) out.push(`You said${m.to && m.to !== "all" ? " to " + m.to : ""}: "${m.text}"`);
        else if (m.to === name || new RegExp(`\\b${name}\\b`).test(m.text)) out.push(`${m.from} said${m.to === name ? " to you" : " about you"}: "${m.text}"`);
      } else if (m.kind === "consciousness" && m.to === name) out.push(`The Consciousness asked you: "${m.text}"`);
    }
    return out.slice(-8).join("\n") || "(nothing yet)";
  }
  function profileLine(name) {
    const e = emo(name);
    if (name === "Sadness") return `${e.name} ${e.emoji}: watches for the suffering emotion whose need is least met and speaks up for it with empathy. It doesn't make proposals of its own.`;
    let t = `${e.name} ${e.emoji}: (${e.when}). Needs: ${e.need}`;
    if (e.personality) t += ` Personality: ${e.personality}`;
    return t;
  }
  const VOICE = "Text like a real person in a group chat: casual, direct, specific. Don't quote your catchphrase. Use only facts the user gave or that came up in the chat; never invent numbers, history or what someone said. Call the user \"you\", or \"we\"/\"us\" since you're part of them.";
  // How every voice in the council talks, whatever its emotion.
  const CARE = [
    "Be radically non-violent and pro-human: never insult, blame, label, shame or threaten anyone (the user, the other people in their life, or the other emotions). Speak to specific actions and their effects, the need behind your feeling, and a request that respects everyone involved. Even angry, be firm and clear, never harsh.",
    "Be precise and actionable: name your specific barrier (exactly what keeps you from 0) and a doable request: who does what, and when. If it's a message to someone, give the actual words.",
    "Humor, slang or a quick \"lol that sucks\" is fine, as long as the same message says what you mean by it and what you want the Consciousness to do.",
    "If you ask a question, say why you're asking and what answer would bring you to 0. Never just wonder out loud (\"should we? idk\"): name what you don't know or fear, and what would settle it.",
  ].join("\n- ");
  const PARAGRAPH = "ONE paragraph: usually 2 to 4 sentences, never more than 6. No line breaks, lists or headings.";
  // Chat bubbles hold one paragraph.
  const oneParagraph = t => cleanQuote(t).replace(/\s*\n+\s*/g, " ").replace(/\s{2,}/g, " ").trim();
  const SAFETY = "If the user seems to be in danger or in crisis, the plan must put their safety first and include reaching out to someone they trust or a crisis line.";

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
      "- \"idea\": the user's plan exactly as they stated it, in first person, one sentence. Don't fix anything yet. If they described a feeling rather than a plan, the idea is what they're inclined to do about it.",
      "- \"suffering\": every emotion whose need THIS idea, as stated, fails right now (score -1). If the idea already serves an emotion's need, it is not suffering. Any emotion the user mentions as objecting belongs here.",
      `- For at most ${COUNCIL.maxOpeners} of them, with clearly different needs, write "says": an opening chat message of one or two sentences about the user's actual situation: what exactly in the idea fails its need, and what it would want instead. Give every other suffering emotion "says": "" (it speaks later). Merge overlapping worries (rest, sleep, a day off) into whichever emotion says it best.`,
      "- \"need\": for each suffering emotion, what would bring it to 0.",
      "- \"helpers\": up to 3 emotions at 0 that could help the suffering ones from their own angle. Include the emotion that drives what the user wants to do (Impulsivity for fun, Loneliness for company, and so on) if it isn't suffering.",
      "- Scores are only -1 or 0. Never invent an emotion. Never leave a suffering emotion out to make things look calmer. Sadness joins on its own, so don't list it.",
      "- " + VOICE,
      "- Openings are radically non-violent: no blaming, labeling or shaming the user, other people or other emotions.",
      "- " + SAFETY,
      "",
      "Reply with only this JSON:",
      "{\"idea\":\"...\",\"suffering\":[{\"emotion\":\"Overwhelm\",\"says\":\"...\",\"need\":\"...\"}],\"helpers\":[\"Efficiency\"]}",
    ].join("\n");
  }

  function pulsePrompt(s) {
    const asked = s.askedOf ? `The Consciousness just asked ${s.askedOf} a question.` : "";
    return [
      "You decide who talks next in Teffy's Emotional Council, a group chat where the user's personified emotions work out a plan with the 🧠 Consciousness. Each emotion wants to reach 0 (it can live with the plan, even grudgingly) instead of -1 (suffering), and helps the others from its own angle without being annoying.",
      "",
      `THE USER'S SITUATION: "${s.thought}"`,
      `THE PLAN RIGHT NOW: ${s.plan}`,
      asked,
      "",
      "THE EMOTIONS IN THE CHAT:",
      s.participants.map(n => n === "Sadness"
        ? `- ${profileLine(n)}\n  Has said: ${saidBy(s, n)}`
        : `- ${profileLine(n)}\n  Score now: ${scoreWord(s.scores[n])}. Plan or user changed since it set that score: ${movedSince(s, n) ? "yes" : "no"}. Has said: ${saidBy(s, n)}`).join("\n"),
      "",
      "THE CHAT SO FAR (oldest first):",
      transcript(s),
      "",
      "For EVERY emotion in the chat, decide from that emotion's own point of view:",
      "- \"score\": its honest score for THE PLAN RIGHT NOW.",
      "  · -1 becomes 0 only if the plan now answers that emotion's specific objection. Moving toward its topic isn't enough. If its \"why\" names anything the plan doesn't cover yet, it stays -1.",
      "  · 0 becomes -1 only if the plan itself now works against its own need. It doesn't take on a grievance another emotion raised for it.",
      "  · If nothing changed since it set its score (\"no\" above), it keeps that score.",
      "  · \"score\" and \"why\" must agree.",
      "- \"reply\": true only if it has something NEW to say right now: standing up for its own need, answering someone who spoke to it or asked it a question, telling someone their advice missed its real problem, or giving a suffering emotion a concrete fix from its own angle (a helper at 0 that hasn't spoken should step up when it has one). false if anyone made the same point in the last few messages, if its idea was already turned down, or if it would only be talking to keep the chat going. Usually one or two emotions want in.",
      "- \"why\": under 15 words, in that emotion's voice, why it speaks up or holds back.",
      "Sadness never gets a score. Also give \"neglected\": the emotion at -1 whose need the plan meets least (never Sadness), or \"\" if nobody is at -1.",
      "",
      "Reply with only this JSON:",
      "{\"neglected\":\"Embarrassment\",\"council\":[{\"emotion\":\"Anger\",\"score\":-1,\"reply\":true,\"why\":\"...\"}]}",
    ].filter(l => l !== "").join("\n").replace(/\n(THE EMOTIONS IN|THE CHAT SO FAR|For EVERY)/g, "\n\n$1");
  }

  function speakPrompt(s, name, why, mode) {
    const e = emo(name);
    const last = [...s.messages].reverse().find(m => m.kind === "emotion" || m.kind === "user" || m.kind === "consciousness");
    const toMe = last && last.to === name ? `${last.kind === "consciousness" ? "THE CONSCIOUSNESS" : last.from.toUpperCase()} JUST SAID TO YOU: "${last.text}"` : "";
    const sad = name === "Sadness";
    const score = s.scores[name] < 0 ? -1 : 0;
    const lines = [
      `You are ${e.name} ${e.emoji}, one of the user's personified emotions, in Teffy's Emotional Council: a group chat with the other emotions and the 🧠 Consciousness about the user's plan.`,
      "",
      "WHO YOU ARE",
      sad ? "You watch for the suffering emotion whose need is least met, and you speak up for it with deep empathy." : `Your catchphrase is "${e.line}" (don't quote it). Your score is ${e.when}.`,
      `Purpose: ${e.purpose}`,
      `To satisfy your need: ${e.need}`,
      e.personality ? `Personality: ${e.personality}` : "",
      "",
      `THE USER'S SITUATION: "${s.thought}"`,
      `THE PLAN RIGHT NOW (don't propose what it already says): ${s.plan}`,
      sad ? "" : `YOUR SCORE RIGHT NOW: ${score} (${score < 0 ? "the plan still fails your need" : "you can live with the plan"})`,
      `WHY YOU'RE SPEAKING UP: ${why || "you have something to add"}`,
      toMe,
      "",
      "WHAT YOU'VE ALREADY SAID, AND WHAT OTHERS SAID TO OR ABOUT YOU (never repeat yourself):",
      historyOf(s, name),
    ];
    if (sad && s.neglected) {
      lines.push("", `WHAT ${s.neglected.toUpperCase()} HAS ACTUALLY SAID:`, s.messages.filter(m => m.kind === "emotion" && m.from === s.neglected).map(m => `"${m.text}"`).slice(-3).join("\n") || "(nothing yet: it hasn't been heard at all)");
    }
    lines.push("", "THE CHAT SO FAR (oldest first):", transcript(s), "");
    if (mode === "accept") {
      lines.push(
        "You just came round to 0. Write a short message (one or two sentences) saying you can live with the plan now, and on what condition, grudgingly if that's how you feel. Don't repeat the plan back.",
        "- " + VOICE);
    } else if (sad) {
      lines.push(
        `Write your next message: speak TO ${s.neglected || "the emotion whose need is least met"} with warmth. Reflect what it actually said, name the part of its need the plan still misses, and ask the Consciousness or a specific emotion to address exactly that. Never speak for it or give it feelings it didn't express. No plan proposals of your own. ${PARAGRAPH}`,
        "- " + VOICE,
        "- " + CARE);
    } else {
      lines.push(
        "Write your next message in the chat. " + PARAGRAPH,
        "- " + VOICE,
        "- " + CARE,
        "- Respond to what was actually said. Stand up for your own need, or help a suffering emotion with something concrete from your own angle.",
        "- If someone already proposed what you want, back it in a few words (\"same, as long as…\") and add only your condition. Never repeat a suggestion that was already made or turned down. If your idea was turned down, take the hint: try a different angle or back off.",
        "- If someone spoke for you or gave you advice that misses your real problem, say so plainly (\"nah, that's not it, my problem is…\").",
        "- If your need clashes with another emotion's, name the clash and suggest a trade-off.",
        "- \"score\": -1 if the plan still fails your need, 0 if you can live with it now (grudgingly is fine). Getting what you asked for never lowers it. Don't fake agreement.");
    }
    lines.push(
      "- \"to\": the emotion you're answering, \"Consciousness\", or \"all\".",
      sad || mode === "accept" ? "- \"proposal\": \"\"." : "- \"proposal\": one concrete change to the plan that nobody has asked for yet, or \"\".",
      "",
      "Reply with only this JSON:",
      `{"to":"all","text":"...","score":${sad ? 0 : mode === "accept" ? 0 : score},"proposal":""}`);
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

  function consolidatePrompt(s) {
    const userLine = userJustSaid(s);
    return [
      `You are the 🧠 Consciousness in Teffy's Emotional Council. Your emotions have been talking about the plan in a group chat. You listen to all of them, especially the ones still suffering${s.neglected ? ` and ${s.neglected}, whose need is least met` : ""}.`,
      "",
      `THE USER'S SITUATION: "${s.thought}"`,
      `THE PLAN RIGHT NOW: ${s.plan}`,
      `SCORES: ${scoreList(s)}`,
      "CHANGES THE EMOTIONS ASKED FOR:",
      proposalsOpen(s).join("\n") || "(none since the last update)",
      userLine ? `THE USER JUST SAID: "${userLine}" (answer this first)` : "",
      "",
      "THE CHAT SO FAR (oldest first):",
      transcript(s),
      "",
      "Update the plan, but don't just stack every request:",
      "- Adopt changes that help a suffering emotion. When a request offers alternatives, pick one. Drop requests that a later one replaces, and settle contradictions.",
      "- If you didn't take an emotion's request, or took only part of it, say so plainly and why.",
      "- Be honest about the trade-off: what the user gives up, or what happens if a step fails (and the fallback).",
      "- \"plan\": written to the user in plain second person (\"Text Sam now…\"), at most three short sentences, realistic for their real situation. No emotion names and no chat logistics in the plan. " + SAFETY,
      "- \"text\": your message to the chat, one paragraph of at most 5 sentences, no line breaks. Don't start with your name. Talk to one or two emotions, not a roll call. If the user just spoke, answer them. End with ONE specific question to ONE suffering emotion, if any is left, saying why you're asking.",
      "- Radically non-violent and pro-human: the plan treats everyone involved fairly, including the other people in the user's life. No blaming, labeling or shaming. Steps are precise: who does what, when, and the actual words for any message.",
      "- \"ask\": the emotion you asked, or \"\".",
      "",
      "Reply with only this JSON:",
      "{\"plan\":\"...\",\"text\":\"...\",\"ask\":\"Fear\"}",
    ].filter(l => l !== "").join("\n").replace(/\n(THE CHAT SO FAR|Update the plan)/g, "\n\n$1");
  }

  function finalPrompt(s) {
    const still = suffering(s);
    return [
      "You are the 🧠 Consciousness in Teffy's Emotional Council. The conversation is wrapping up.",
      "",
      `THE USER'S SITUATION: "${s.thought}"`,
      `THE PLAN RIGHT NOW: ${s.plan}`,
      `STILL SUFFERING: ${still.length ? still.join(", ") : "none"}`,
      "",
      "THE CHAT SO FAR (oldest first):",
      transcript(s),
      "",
      "Write:",
      "- \"plan\": the final plan, to the user in plain second person, at most three short sentences, with the changes the council agreed on. No emotion names. Never change what an emotion asked for unless it accepted the change in the chat. " + SAFETY,
      "- \"text\": your closing message to the user, in first person, one paragraph of at most 5 sentences, no line breaks, in the emotional personification language. Speak to at most three emotions by name: anyone in STILL SUFFERING (and how you'll look after them), and whoever gave the most ground. Only call an emotion still suffering if it is listed in STILL SUFFERING. End with the one concrete next step. No filler like \"I'll keep checking in\", and don't repeat your last message.",
      "",
      "Reply with only this JSON:",
      "{\"plan\":\"...\",\"text\":\"...\"}",
    ].join("\n");
  }

  // ---------- Applying replies ----------

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
    s.plan = s.idea;
    opening.forEach(x => addParticipant(s, x.name, -1));
    helpers.forEach(em => addParticipant(s, em.name, 0));
    addParticipant(s, "Sadness", 0);
    s.neglected = opening.length ? opening[0].name : "";
    s.messages.push({ kind: "consciousness", text: `Here's what I'm thinking: ${s.idea}`, plan: s.plan, planUpdate: true, opening: true });
    let voiced = 0;
    for (const x of opening) {
      if (!x.says || voiced >= COUNCIL.maxOpeners) continue;
      voiced++;
      s.messages.push({ kind: "emotion", from: x.name, to: "all", text: x.says, score: -1, prev: null, proposal: x.need, opening: true });
    }
    s.status = "running";
  }

  function applyPulse(s, p) {
    if (!p || typeof p !== "object" || !Array.isArray(p.council)) throw badShape("pulse");
    const items = [];
    for (const raw of p.council) {
      const em = findEmotion(raw && raw.emotion);
      if (!em || !s.participants.includes(em.name) || items.some(i => i.emotion === em.name)) continue;
      const item = { emotion: em.name, reply: raw.reply === true || raw.reply === "true", why: cleanQuote(raw.why) };
      if (em.name === "Sadness") { items.push(item); continue; }
      const prev = s.scores[em.name] < 0 ? -1 : 0;
      const proposed = toScore(raw.score);
      // A score only moves when something changed for this emotion: a new plan or a user message.
      if (proposed !== prev && movedSince(s, em.name)) setScore(s, em.name, proposed);
      else s.scoredAt[em.name] = stamp(s);   // judged against this plan: it holds until something changes
      item.prev = prev;
      item.score = s.scores[em.name] < 0 ? -1 : 0;
      items.push(item);
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

  function emotionMessages(s) { return s.messages.filter(m => m.kind === "emotion"); }
  function pickSpeaker(s, decisions) {
    const wants = decisions.filter(d => d.reply && s.participants.includes(d.emotion));
    if (!wants.length) return null;
    const said = emotionMessages(s);
    const last = said[said.length - 1];
    const recent = said.slice(-3).map(m => m.from);
    const spoke = n => said.filter(m => m.from === n).length;
    const lastHeard = n => { for (let i = said.length - 1; i >= 0; i--) if (said[i].from === n) return said.length - i; return 99; };
    const weight = d => {
      const n = d.emotion;
      let v = 0;
      if (s.askedOf === n) v += 6;                                   // the Consciousness asked it a question
      if (last && last.to === n) v += 5;                              // another emotion spoke to it
      if (n !== "Sadness" && s.scores[n] < 0) v += 3;                 // suffering voices go first
      if (n === s.neglected && s.scores[n] < 0) v += 2;               // Sadness's pick
      if (d.prev < 0 && d.score === 0) v += 2;                        // just came round: let it say so
      if (n === "Sadness" && s.neglected && lastHeard(s.neglected) > 4) v += 3;
      if (n !== "Sadness" && !spoke(n)) v += 2;                       // hasn't had a turn yet
      if (recent.includes(n)) v -= 4;
      if (last && last.from === n) v -= 8;                            // no double posting
      return v;
    };
    const ranked = wants.slice().sort((a, b) => weight(b) - weight(a) || s.participants.indexOf(a.emotion) - s.participants.indexOf(b.emotion));
    if (last && ranked[0].emotion === last.from) return null;       // only the last speaker wants in: let the Consciousness respond
    return ranked[0].emotion;
  }

  function target(s, v) {
    const em = findEmotion(v);
    if (em) {
      if (!s.participants.includes(em.name)) addParticipant(s, em.name, 0);
      if (s.participants.includes(em.name)) return em.name;
    }
    const t = String(v || "").toLowerCase();
    if (t.includes("conscious")) return "Consciousness";
    if (t.includes("user") || t === "you" || t === "me") return "You";
    return "all";
  }
  function applySpeak(s, name, m, why) {
    if (!m || typeof m !== "object") throw badShape("speak");
    const text = oneParagraph(m.text);
    if (!text) throw badShape("speak");
    const prev = name === "Sadness" ? null : s.scores[name] < 0 ? -1 : 0;
    if (name !== "Sadness") setScore(s, name, toScore(m.score));
    const to = target(s, m.to);
    s.messages.push({
      kind: "emotion", from: name, to: to === name ? "all" : to, text,
      score: name === "Sadness" ? 0 : s.scores[name], prev,
      proposal: name === "Sadness" ? "" : cleanQuote(m.proposal), why: why || "",
    });
    if (s.askedOf === name) s.askedOf = "";
    s.emotionMsgs++;
    s.sinceConsolidate++;
  }

  // ---------- The conversation loop ----------

  // io.ask(prompt, step, emotion) -> Promise<object>; io.update(info) after every change;
  // io.stopped() -> true to stop between calls. Throws whatever io.ask throws (other than an
  // unreadable reply), leaving the council in a consistent state that can be resumed.
  async function runCouncil(s, io) {
    const ask = (prompt, step, who) => { s.calls++; s.callsRun++; return io.ask(prompt, step, who); };
    const soft = async (fn) => {
      try { const r = await fn(); s.misses = 0; return r; }
      catch (e) { if (!isParseFail(e) || ++s.misses >= 3) throw e; return null; }
    };
    const speak = async (name, why, mode) => {
      io.update({ busy: "speak", who: name });
      const m = await soft(() => ask(speakPrompt(s, name, why, mode), "speak", name).then(r => { applySpeak(s, name, r, why); return r; }));
      if (!m) s.messages.push({ kind: "note", text: `${name} started typing, then stopped.` });
      io.update({});
    };

    if (!s.participants.length) {
      io.update({ busy: "convene" });
      const c = await ask(convenePrompt(s), "convene");
      applyConvene(s, c);
      io.update({});
    }
    s.status = "running";

    while (!io.stopped()) {
      const fresh = !!s.fresh;
      // Nobody suffering can only end the chat once the plan has actually been worked on.
      const settled = !suffering(s).length && (s.consolidations > 0 || !Object.values(s.start).some(v => v < 0));
      if (!fresh && !s.askedOf && (settled || s.emotionMsgs >= COUNCIL.maxEmotionMessages || s.callsRun >= COUNCIL.maxCalls)) {
        return wrapUp(s, io, ask, soft);
      }
      if (!fresh && s.emotionMsgs >= COUNCIL.maxEmotionMessages + 2) return wrapUp(s, io, ask, soft);
      const lastSpoken = [...s.messages].reverse().find(m => m.kind === "emotion" || m.kind === "user" || m.kind === "consciousness");
      const toConsciousness = lastSpoken && lastSpoken.kind === "emotion" && lastSpoken.to === "Consciousness" && s.sinceConsolidate >= 2;
      if (!fresh && !s.askedOf && (s.sinceConsolidate >= COUNCIL.consolidateEvery || toConsciousness || (!suffering(s).length && !s.consolidations))) {
        await consolidate(s, io, ask, soft);
        continue;
      }

      io.update({ busy: "pulse" });
      const p = await soft(() => ask(pulsePrompt(s), "pulse"));
      const decisions = p ? applyPulse(s, p) : fallbackDecisions(s);
      let speaker = pickSpeaker(s, decisions);
      // An emotion the Consciousness asked a question gets to answer, even if it was holding back.
      if (!speaker && s.askedOf && s.participants.includes(s.askedOf)) speaker = s.askedOf;
      if (speaker && s.askedOf && speaker !== s.askedOf && suffering(s).length) s.askedOf = "";   // it passed on answering
      s.fresh = false;
      const decideMsg = { kind: "decide", items: decisions, speaker: speaker || "" };
      s.messages.push(decideMsg);
      io.update({});

      if (!fresh && !suffering(s).length && s.consolidations > 0) {
        // Everyone can live with it. Let someone who just came round say so, then wrap up.
        const accepter = decisions.find(d => d.prev < 0 && d.score === 0 && (d.emotion === s.askedOf || d.reply));
        const name = s.askedOf || (accepter && accepter.emotion);
        if (name) {
          decideMsg.speaker = name;
          const dd = decisions.find(x => x.emotion === name) || {};
          await speak(name, dd.why || "", dd.prev < 0 && dd.score === 0 ? "accept" : "");
        }
        s.askedOf = "";
        if (!suffering(s).length) return wrapUp(s, io, ask, soft);
        continue;
      }

      if (!speaker) {
        // Nobody wants the floor: the Consciousness answers the user, or takes stock, or wraps up.
        if (fresh) { await consolidate(s, io, ask, soft); continue; }
        s.quiet++;
        if (s.quiet >= 2 || (s.sinceConsolidate === 0 && s.consolidations > 0)) return wrapUp(s, io, ask, soft);
        await consolidate(s, io, ask, soft);
        continue;
      }
      s.quiet = 0;
      const d = decisions.find(x => x.emotion === speaker) || {};
      await speak(speaker, d.why || "", d.prev < 0 && d.score === 0 ? "accept" : "");
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
    const plan = cleanQuote(c.plan);
    if (plan && plan !== s.plan) { s.plan = plan; s.planVersion = (s.planVersion || 0) + 1; }
    const asked = findEmotion(c.ask);
    s.askedOf = asked && asked.name !== "Sadness" && s.participants.includes(asked.name) ? asked.name : "";
    s.messages.push({ kind: "consciousness", text: oneParagraph(c.text) || "Here's where the plan stands now.", plan: s.plan, planUpdate: !!plan, to: s.askedOf || "" });
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
    const plan = cleanQuote(f && f.plan);
    if (plan) s.plan = plan;
    const t = tally(s);
    s.messages.push({ kind: "final", plan: s.plan, text: oneParagraph(f && f.text), start: t.start, end: t.now, still: suffering(s) });
    s.sinceConsolidate = 0;
    s.askedOf = "";
    io.update({});
  }

  return {
    EMOTIONS, findEmotion, emo, scanObjects, cleanQuote, toScore,
    COUNCIL, newCouncil, addUserMessage, runCouncil, suffering, tally, mentionedEmotions, isParseFail,
    // exposed for tests
    _internal: { convenePrompt, pulsePrompt, speakPrompt, consolidatePrompt, finalPrompt, applyConvene, applyPulse, applySpeak, pickSpeaker, transcript },
  };
})();
