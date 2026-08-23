/**
 * Pi writing-pass hook. Keep the classifier in sync with
 * skills/plain-writing/hooks/review_followup.py.
 *
 * After a writing pass, queue the same follow-up the Cursor, Claude, and
 * Codex hooks send. Skills and /review prompts still work if this
 * extension is disabled.
 */

export const FOLLOWUP =
  "Run /plain-writing review on your last response. Launch four reviewer " +
  "subagents, one per rule group, in the same turn. Wait for their " +
  "findings. Fix every fail. Then reply with only the rewrite.";

const WRITING_RE =
  /(\/plain-writing|\bdeslopify\b|\brewrite\b|\bdraft\b|\bmemo\b|\bsummary\b|\breport\b|plain writing|review this writing|write (?:a |an |the )?(?:doc|docs|readme|memo|email|summary|report|update|post|essay|letter)\b)/i;

const CODING_RE =
  /(\b(implement|refactor|debug|compile|lint|typecheck)\b|\bfix (the )?(bug|error|test|regex|hook|script|function|parser|build)\b|\b(git commit|git push|merge conflict|stack trace|unit test)\b)/i;

const CODE_FENCE_RE = /```[\s\S]*?```/g;
const MIN_WRITING_CHARS = 240;

export function codeFraction(text) {
  const value = text || "";
  const fenced = [...value.matchAll(CODE_FENCE_RE)].reduce(
    (sum, match) => sum + match[0].length,
    0,
  );
  return fenced / Math.max(value.length, 1);
}

export function isWritingPass(userText, assistantText) {
  const hook = (process.env.PLAIN_WRITING_REVIEW_HOOK || "").toLowerCase();
  if (hook === "1" || hook === "always" || hook === "true") {
    return true;
  }
  const assistant = (assistantText || "").trim();
  const user = (userText || "").trim();
  if (assistant.length < MIN_WRITING_CHARS) {
    return false;
  }
  if (user === FOLLOWUP || user.includes("/plain-writing review")) {
    return false;
  }
  if (codeFraction(assistant) >= 0.35) {
    return false;
  }
  const userWantsWriting = WRITING_RE.test(user);
  const userWantsCoding = CODING_RE.test(user);
  if (userWantsCoding && !userWantsWriting) {
    return false;
  }
  if (userWantsWriting) {
    return true;
  }
  if (codeFraction(assistant) === 0 && assistant.length >= 500) {
    if (/\b(committed|pushed|pull request|diff|tests pass)\b/i.test(assistant)) {
      return false;
    }
    return true;
  }
  return false;
}

export function messageText(message) {
  if (!message) {
    return "";
  }
  if (typeof message === "string") {
    return message;
  }
  const content = message.content ?? message.text ?? message.prompt;
  if (typeof content === "string") {
    return content;
  }
  if (!Array.isArray(content)) {
    return "";
  }
  return content
    .map((item) => {
      if (typeof item === "string") {
        return item;
      }
      if (item && (item.type === "text" || item.type === "input_text")) {
        return item.text || "";
      }
      return "";
    })
    .filter(Boolean)
    .join("\n");
}

function selfTest() {
  const errors = [];
  const check = (name, ok) => {
    if (!ok) {
      errors.push(name);
    }
  };

  const writingSample =
    "Search ranking now uses a scored model instead of heuristics, and p95 " +
    "latency fell from 900 ms to 220 ms. The old heuristic path is still in " +
    "the repo as a fallback. To do: test recall on long queries. Dark mode " +
    "shipped, and the invite link bug is fixed. Analytics export is still " +
    "blocked on a schema mismatch.";

  check(
    "draft request is a writing pass",
    isWritingPass("Draft a project update for engineering.", writingSample),
  );
  check(
    "bug fix is not a writing pass",
    !isWritingPass(
      "Fix the bug in parse_criteria.",
      "The parser skipped extra headings. I changed the regex and added a test.\n\n" +
        "```python\nCRITERION_RE = re.compile('x')\n```\n",
    ),
  );
  check(
    "code-heavy reply is not a writing pass",
    !isWritingPass(
      "Show me the new hook.",
      "Here is the script.\n\n```python\n" +
        "print('x')\n".repeat(40) +
        "```\n\n```python\n" +
        "print('y')\n".repeat(40) +
        "```\n",
    ),
  );
  check(
    "short status is not a writing pass",
    !isWritingPass("Write a memo.", "Done."),
  );
  check(
    "review follow-up is not a writing pass",
    !isWritingPass(FOLLOWUP, "A".repeat(300)),
  );
  check(
    "message text joins text parts",
    messageText({
      role: "assistant",
      content: [
        { type: "text", text: "Hello" },
        { type: "text", text: "world" },
      ],
    }) === "Hello\nworld",
  );

  if (errors.length) {
    console.error("self-test failed:");
    for (const error of errors) {
      console.error(`- ${error}`);
    }
    return 1;
  }
  console.log("self-test passed: pi writing-pass extension");
  return 0;
}

export default function (pi) {
  let lastUser = "";
  let lastAssistant = "";
  let followedUp = false;

  const considerFollowUp = (ctx) => {
    if (followedUp) {
      return;
    }
    if (ctx?.hasPendingMessages?.()) {
      return;
    }
    if (!isWritingPass(lastUser, lastAssistant)) {
      return;
    }
    followedUp = true;
    try {
      pi.sendUserMessage(FOLLOWUP, { deliverAs: "followUp" });
    } catch {
      pi.sendUserMessage(FOLLOWUP);
    }
  };

  pi.on("before_agent_start", (event) => {
    const prompt = messageText(event) || String(event?.prompt || "");
    if (prompt.trim()) {
      lastUser = prompt;
    }
  });

  pi.on("turn_end", (event) => {
    const text = messageText(event?.message);
    if (text.trim()) {
      lastAssistant = text;
    }
  });

  pi.on("agent_end", (event) => {
    if (lastAssistant.trim()) {
      return;
    }
    const messages = event?.messages || [];
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      const message = messages[i];
      const role = String(message?.role || "").toLowerCase();
      if (role === "assistant" || role === "model") {
        const text = messageText(message);
        if (text.trim()) {
          lastAssistant = text;
          break;
        }
      }
    }
  });

  pi.on("agent_settled", (_event, ctx) => {
    considerFollowUp(ctx);
  });
}

const invokedDirectly = process.argv[1] && process.argv[1].endsWith("plain-writing-review.js");
if (invokedDirectly && process.argv.includes("--self-test")) {
  process.exit(selfTest());
}
