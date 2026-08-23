---
name: review
description: Review existing writing with four rule-group subagents, then fix every fail.
---

Run the review command in `skills/plain-writing/SKILL.md`.

Review the previous agent response, or the text or file path after this
command. Do not rewrite yet. First launch four reviewer subagents in the
same turn, one per rule group. Wait for their findings. Fix every fail.
If the writing lives in a file, edit that file. If it was a chat reply,
return only the rewrite.
