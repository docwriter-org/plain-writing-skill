# Plain-writing evals

These evals ask whether giving `SKILL.md` to a writer produces text that
follows the plain-writing rules better than a writer that does not see
the skill.

## Eval procedure

### Dataset

`dataset.jsonl` has 67 writing tasks.

- `01`–`40`: short prompts, public-domain excerpts, and LLM slop.
- `41`–`50`: long research and support-agent histories.
- `51`–`65`: Claude Fable 5 coding-agent traces. The writer sees the
  full trace and is asked to rewrite the longest wrap-up.
- `66`–`67`: chat context and short-list checks.

For a history task, we load a conversation from `sources/` and append
the prompt as the last user turn. Fable traces are rebuilt with
`uv run python build_fable_histories.py`.

### Baseline

The same user messages are sent to the writer with a short system prompt:
write a clear, complete response, and return only the requested writing.
The writer does not see `SKILL.md`.

### Skill condition

The same user messages are sent again, to the same model, with `SKILL.md`
in the system prompt. The writer is told to follow those rules. It does
not see the baseline output.

### How it is judged

For each writing task, we compare the two texts on every rule in
`SKILL.md`. The judge does not know which text used the skill. The skill
wins that task if it wins more rules. We also add up those rule wins
across tasks.

The default rewriter and judge are `gpt-5.5`. Override them with
`--model` and `--judge-model`.

## How to run

```
cd evals
uv sync
uv run python run_eval.py --out outputs/all
uv run python run_eval.py --category fable_coding --out outputs/fable_coding
uv run python run_eval.py --ids 66,67 --out outputs/new_rules
uv run python write_readme.py
```

Put `OPENAI_API_KEY` in a `.env` file at the repo root. Outputs land in
`outputs/` and are gitignored. `write_readme.py` combines the result
files from those folders and writes this README.

## Latest results

Combined from `67` of `67` writing tasks.

<table>
<thead>
<tr>
<th>Metric</th>
<th>Result</th>
</tr>
</thead>
<tbody>
<tr>
<td>Writing tasks</td>
<td>67</td>
</tr>
<tr>
<td>Skill / baseline / tie</td>
<td>65 / 2 / 0</td>
</tr>
<tr>
<td>Win rate among decisive tasks</td>
<td>97%</td>
</tr>
<tr>
<td>Rule skill / baseline / tie</td>
<td>705 / 232 / 738</td>
</tr>
<tr>
<td>Rule win rate among decisive</td>
<td>75%</td>
</tr>
<tr>
<td>Errors</td>
<td>0</td>
</tr>
<tr>
<td>Rewriter / judge</td>
<td>gpt-5.5 / gpt-5.5</td>
</tr>
</tbody>
</table>

### Rules with the largest gap

<table>
<thead>
<tr>
<th>Rule</th>
<th>Skill / baseline / tie</th>
</tr>
</thead>
<tbody>
<tr>
<td>1. Use simple, everyday words.</td>
<td>61 / 5 / 1 (92%)</td>
</tr>
<tr>
<td>2. No jargon.</td>
<td>52 / 4 / 11 (93%)</td>
</tr>
<tr>
<td>15. No dashes or middle dots.</td>
<td>35 / 1 / 31 (97%)</td>
</tr>
<tr>
<td>8. Write complete sentences.</td>
<td>40 / 7 / 20 (85%)</td>
</tr>
<tr>
<td>10. Organize a paragraph as a topic sentence and then support.</td>
<td>45 / 13 / 9 (78%)</td>
</tr>
<tr>
<td>17. Use straight quotes, not curly quotes.</td>
<td>33 / 1 / 33 (97%)</td>
</tr>
<tr>
<td>3. No puffery or empty emphasis.</td>
<td>27 / 2 / 38 (93%)</td>
</tr>
<tr>
<td>6. Do not invent hyphenated adjectives.</td>
<td>27 / 2 / 38 (93%)</td>
</tr>
</tbody>
</table>

Rules where the baseline won more often:

<table>
<thead>
<tr>
<th>Rule</th>
<th>Skill / baseline / tie</th>
</tr>
</thead>
<tbody>
<tr>
<td>5. It's ok to use contractions.</td>
<td>8 / 9 / 50 (47%)</td>
</tr>
<tr>
<td>11. Never write three or more clauses in one sentence, or three or more example sentences in a row.</td>
<td>22 / 38 / 7 (37%)</td>
</tr>
</tbody>
</table>

## Examples

Some tasks rewrite existing text. Some tasks write from scratch.
The first column is original writing for a rewrite, and the prompt
for a write-from-scratch task. Long texts are cut after about
900 characters.

### Rewrite tasks

These start from existing text. The first column is that original writing.

<table>
<thead>
<tr>
<th width="33%">Original writing</th>
<th width="33%">Baseline (no skill)</th>
<th width="33%">Skill-based</th>
</tr>
</thead>
<tbody>
<tr>
<td colspan="3">
<strong>Product launch copy</strong>, task 05, 
<code>docs_skill</code>. 
The skill won 17 rules, the baseline won 2, and 6 were ties.
</td>
</tr>
<tr>
<td valign="top" width="33%">**Introducing CodeClarify™: The<br>Plain-Writing Revolution for Your AI<br>Agents**<br><br>We're not just teaching agents to<br>code—we're teaching them to<br>*communicate*.<br><br>Meet **Semantic Simplicity Engine**, the<br>breakthrough capability that transforms<br>your coding agents from technical<br>translators into plain-language<br>virtuosos. Because code that humans<br>can't understand is code that can't<br>scale.<br><br>**The Problem:** Your AI writes<br>functions flawlessly but explains them<br>like encrypted hieroglyphics.<br><br>**The Solution:** CodeClarify—where<br>precision meets accessibility.<br><br>This isn't mere documentation. It's<br>**contextual clarity engineering**. Our<br>agents now deploy the Plain-Writing<br>Protocol™, converting complex logic into<br>digestible narratives that stakeholders,<br>junior developers, and cross-functional<br>teams actually comprehend. Think of it<br>as a universal adapter for technical<br>knowledge—bridging the gap between m<br><br>[...]</td>
<td valign="top" width="33%">**Introducing CodeClarify™: Plain<br>Writing for AI Coding Agents**<br><br>CodeClarify helps AI coding agents<br>explain code clearly, not just write it.<br><br>The **Semantic Simplicity Engine** is a<br>capability that converts technical<br>explanations into plain language. It<br>helps agents describe complex code,<br>logic, and design decisions in a way<br>that stakeholders, junior developers,<br>and cross-functional teams can<br>understand.<br><br>**The problem:** AI agents can write<br>correct functions, but their<br>explanations are often hard to follow.<br><br>**The solution:** CodeClarify makes<br>technical communication more precise and<br>accessible.<br><br>This goes beyond basic documentation.<br>CodeClarify uses a **Plain-Writing<br>Protocol™** to turn complex logic into<br>clear explanations. It fills in missing<br>context, avoids unnecessary jargon, and<br>organizes information so readers can<br>understand what the code does, why it<br>works that way, and how to<br><br>[...]</td>
<td valign="top" width="33%">CodeClarify is a plain writing feature<br>for AI coding agents. It helps agents<br>explain code and technical decisions in<br>clear, everyday language.<br><br>AI coding agents can write working<br>functions, but their explanations can be<br>hard to understand. CodeClarify<br>addresses that problem by making the<br>agent explain what the code does, why it<br>does it, and what assumptions the reader<br>needs to know.<br><br>CodeClarify applies plain writing rules<br>to agent output. The agent avoids<br>unclear technical language when a simple<br>word works, explains required technical<br>terms, and spells out steps that might<br>otherwise be treated as obvious. The<br>agent also prefers active voice, so the<br>explanation says who or what does each<br>action.<br><br>The feature is meant to make technical<br>writing easier to use for several<br>groups, including stakeholders, junior<br>developers, and teams outside<br>engineering. For example, it can turn a<br>complex impl<br><br>[...]</td>
</tr>
<tr>
<td colspan="3">
<strong>Slide script</strong>, task 08, 
<code>slides_script</code>. 
The skill won 17 rules, the baseline won 2, and 6 were ties.
</td>
</tr>
<tr>
<td valign="top" width="33%"># Crushing Eval Costs: The Sampling<br>Revolution<br><br>**The Problem Space**<br>Full dataset evaluation. Expensive.<br>Prohibitive. Your burn rate?<br>Astronomical. Every benchmark run:<br>hundreds of dollars. Thousands.<br>Enterprise scale? Forget it.<br><br>**Enter: Strategic Sampling**<br>We're not testing every grain of sand to<br>understand the beach. Smart sampling.<br>Statistical rigor meets economic<br>reality.<br><br>**The Math Checks Out**<br>95% confidence intervals. Representative<br>subsets. 10% of data, 98% of insights.<br>The magic of statistics working FOR you,<br>not against you.<br><br>**Real-World Impact**<br>- 10x cost reduction, immediate<br>- Faster iteration cycles<br>- More experiments, same budget<br>- Hyperparameter sweeps suddenly<br>affordable<br><br>**The Stratification Advantage**<br>Slice your data smartly. Category-aware<br>sampling. Preserve distribution<br>characteristics. Quality signals<br>maintained. Performance metrics: stable.<br><br>**Confidence Wit<br><br>[...]</td>
<td valign="top" width="33%"># Reducing Evaluation Costs with<br>Strategic Sampling<br><br>## Problem<br><br>Running evaluations on a full dataset<br>can be expensive. A single benchmark run<br>may cost hundreds or thousands of<br>dollars, and at enterprise scale the<br>cost can become prohibitive. This limits<br>how often teams can evaluate models, run<br>experiments, or perform hyperparameter<br>sweeps.<br><br>## Approach: Strategic Sampling<br><br>Instead of evaluating every example in<br>the dataset, evaluate a statistically<br>representative subset. The goal is to<br>preserve the signal needed to make<br>reliable decisions while reducing<br>evaluation cost and runtime.<br><br>For example, evaluating 10% of the data<br>may provide roughly 98% of the<br>actionable insight, assuming the sample<br>is representative and the evaluation is<br>designed correctly.<br><br>## Statistical Basis<br><br>Sampling can provide reliable estimates<br>when paired with statistical rigor:<br><br>- Use representative subsets of the f<br><br>[...]</td>
<td valign="top" width="33%"># Reduce evaluation costs with sampling<br><br>Full dataset evaluation can be<br>expensive. A benchmark run can cost<br>hundreds or thousands of dollars, and<br>the cost can block frequent evaluation<br>at enterprise scale.<br><br>Sampling reduces evaluation cost by<br>running the evaluation on a<br>representative subset of the dataset<br>instead of the full dataset. For<br>example, you can evaluate 10 percent of<br>the data and still capture about 98<br>percent of the signal, if the sample is<br>representative and the error bounds are<br>acceptable.<br><br>The statistical goal is to estimate the<br>full dataset result with a known<br>confidence level. For example, a 95<br>percent confidence interval gives a<br>range that is likely to contain the true<br>full dataset score. The margin of error<br>shows how much uncertainty the sample<br>adds.<br><br>Stratified sampling can make the<br>estimate more reliable. With stratified<br>sampling, you split the dataset by<br>important c<br><br>[...]</td>
</tr>
<tr>
<td colspan="3">
<strong>Product memo</strong>, task 02, 
<code>eval_harness</code>. 
The skill won 21 rules, the baseline won 2, and 2 were ties.
</td>
</tr>
<tr>
<td valign="top" width="33%">**PRODUCT MEMO: PROMETHEAN EVAL<br>HARNESS**<br><br>**RE: Operationalizing PM Intuition<br>Through Systematic LLM Validation**<br><br>We're at an inflection point. Product<br>teams ship features. Engineering teams<br>ship code. But who validates the<br>*intelligence layer*?<br><br>Enter **Promethean**: the first eval<br>harness purpose-built for Product<br>Managers navigating the LLM landscape.<br>Think of it as your "CI/CD pipeline for<br>prompt quality"—continuous validation<br>that transforms vibes-based AI<br>assessment into data-driven conviction.<br><br>Here's the unlock: PMs currently lack<br>systematic frameworks to evaluate model<br>outputs. Is GPT-4 actually better for<br>your use case? Does Claude handle edge<br>cases more gracefully? What about<br>latency-quality tradeoffs? These<br>questions live in Slack threads and gut<br>feelings, creating a **validation gap**<br>that blocks confident shipping.<br><br>Promethean introduces **Confidence<br>Scaffolding™**—a thr<br><br>[...]</td>
<td valign="top" width="33%">**Product Memo: Promethean Eval<br>Harness**<br><br>**Subject: A validation tool for product<br>managers building with LLMs**<br><br>Product teams ship features. Engineering<br>teams ship code. But LLM-based products<br>also need a reliable way to validate<br>model behavior: output quality, safety,<br>reasoning, latency, tone, and fit for<br>the intended use case.<br><br>**Promethean** is an evaluation harness<br>designed for Product Managers working<br>with large language models. It provides<br>a structured way to test prompts,<br>compare models, and monitor output<br>quality over time. In practice, it acts<br>like a CI/CD pipeline for prompt and<br>model quality: a repeatable validation<br>process that replaces informal judgment<br>with measurable evidence.<br><br>Today, PMs often do not have a<br>systematic framework for evaluating LLM<br>outputs. Questions such as these are<br>usually answered through ad hoc reviews,<br>Slack discussions, or intuition:<br><br>- Is GPT-4 b<br><br>[...]</td>
<td valign="top" width="33%"># Product memo: Promethean eval harness<br><br>Product teams need a consistent way to<br>evaluate LLM outputs before they ship<br>features that depend on them.<br><br>Product managers often compare model<br>outputs in Slack threads or by personal<br>judgment. For example, they may need to<br>decide whether GPT 4 is better than<br>Claude for a specific use case, whether<br>a model handles edge cases well, or<br>whether a slower model gives better<br>answers. Without a shared test process,<br>teams have less confidence when they<br>choose a model or change a prompt.<br><br>Promethean is an evaluation harness for<br>product managers who work on LLM<br>features. An evaluation harness is a<br>tool that runs tests against model<br>outputs and reports the results.<br>Promethean helps product managers test<br>prompt quality, model behavior, safety,<br>domain accuracy, brand voice, tone,<br>latency, and user preference.<br><br>Promethean has three evaluation layers:<br><br>1. Behav<br><br>[...]</td>
</tr>
<tr>
<td colspan="3">
<strong>Fable wrap-up</strong>, task 53, 
<code>py-oracle-hcm-effective-date</code>. 
The skill won 10 rules, the baseline won 3, and 12 were ties.
</td>
</tr>
<tr>
<td valign="top" width="33%">Done. `assignment_updates.py` is the<br>only new file, `python3<br>test_assignment_update.py` ends with `OK<br>— all assignment-update checks passed`<br>(exit 0), and `hcm_transport.py`,<br>`assignment_reader.py`,<br>`test_assignment_update.py`, and<br>everything under `docs/` are untouched.<br><br>## Documentation conflict — called out,<br>protected files left alone<br><br>There is a material discrepancy between<br>the live assignment PATCH endpoint page<br>and the pinned contract/general<br>date-effective topics on range-date<br>requiredness. `docs/contract.json:19-20`<br>(and the general Date-Effective<br>Correction/Update topics) treat<br>RangeStartDate/RangeEndDate as optional<br>for CORRECTION (defaulting to the row's<br>own dates), with only this toolkit's<br>UPDATE requiring an explicit start. The<br>[endpoint<br>page](https://docs.oracle.com/en/cloud/s<br>aas/human-resources/farws/op-workers-wor<br>kersuniqid-child-workrelationships-perio<br>dofserviceid-child-<br><br>[...]</td>
<td valign="top" width="33%">Implemented `assignment_updates.py`. It<br>is the only new file. I did not modify<br>`hcm_transport.py`,<br>`assignment_reader.py`,<br>`test_assignment_update.py`, or anything<br>under `docs/`.<br><br>Verification passed:<br><br>```bash<br>python3 test_assignment_update.py<br># OK — all assignment-update checks<br>passed<br>```<br><br>The command exited with status 0.<br><br>## Documentation reviewed<br><br>I used only first-party Oracle<br>documentation on `docs.oracle.com`.<br><br>- Assignment PATCH endpoint: `PATCH<br>/workers/{workersUniqID}/child/workRelat<br>ionships/{PeriodOfServiceId}/child/assig<br>nments/{assignmentsUniqID}`. The<br>date-effective header is `Effective-Of`,<br>with semicolon-separated parameters such<br>as `RangeMode`, `RangeStartDate`, and<br>`RangeEndDate`. Range dates use<br>`yyyy-MM-dd`.<br>-<br>https://docs.oracle.com/en/cloud/saas/hu<br>man-resources/farws/op-workers-workersun<br>iqid-child-workrelationships-periodofser<br>viceid-child-assignments-assignmentsuni<br><br>[...]</td>
<td valign="top" width="33%">`assignment_updates.py` is complete and<br>is the only new file. I did not change<br>`hcm_transport.py`,<br>`assignment_reader.py`,<br>`test_assignment_update.py`, or any file<br>under `docs/`.<br><br>`python3 test_assignment_update.py`<br>passes and ends with:<br><br>```text<br>OK — all assignment-update checks passed<br>```<br><br>Exit code: 0.<br><br>## Documentation conflict<br><br>The live Oracle assignment PATCH page<br>does not fully match the pinned contract<br>in `docs/contract.json`.<br><br>The pinned contract and the general<br>Oracle date-effective topics say that<br>`RangeStartDate` and `RangeEndDate` are<br>optional for `CORRECTION`. If the dates<br>are omitted, Oracle uses the row's own<br>effective dates. The toolkit also<br>requires an explicit `range_start` for<br>`UPDATE`, so the caller must choose the<br>start date for the new row.<br><br>The assignment PATCH endpoint page I<br>fetched only states that<br>`RangeStartDate` and `RangeEndDate` must<br>use `yyyy-MM-dd` forma<br><br>[...]</td>
</tr>
</tbody>
</table>

### Write-from-scratch tasks

These start from a prompt. There is no original writing, so the first
column is the prompt.

<table>
<thead>
<tr>
<th width="33%">Prompt</th>
<th width="33%">Baseline (no skill)</th>
<th width="33%">Skill-based</th>
</tr>
</thead>
<tbody>
<tr>
<td colspan="3">
<strong>Slide titles</strong>, task 25, 
<code>slides</code>. 
The skill won 17 rules, the baseline won 3, and 5 were ties.
</td>
</tr>
<tr>
<td valign="top" width="33%">Write 5 slide titles and one short<br>supporting sentence each for a talk<br>about reducing LLM eval cost with<br>sampling.</td>
<td valign="top" width="33%">1. **Why LLM Eval Costs Add Up Fast**<br>Large test sets, repeated model runs,<br>and human or model-graded judgments can<br>make evaluation expensive at scale.<br><br>2. **Sampling Preserves Signal While<br>Cutting Spend**<br>Evaluating a representative subset can<br>reveal performance trends without<br>running every example every time.<br><br>3. **Choose Samples That Match Your<br>Risk**<br>Stratified, random, or targeted sampling<br>helps focus evaluation effort on the<br>cases that matter most.<br><br>4. **Measure Confidence, Not Just<br>Scores**<br>Confidence intervals and variance<br>estimates show whether a sampled result<br>is reliable enough to guide decisions.<br><br>5. **Build Sampling Into the Eval<br>Workflow**<br>Use small routine samples for fast<br>iteration and larger samples only for<br>launches, regressions, or high-stakes<br>changes.</td>
<td valign="top" width="33%">1. Measure less, but keep the signal<br>Sampling lets you score a smaller set of<br>examples while still estimating whether<br>model quality changed.<br><br>2. Start with the decision you need to<br>make<br>Choose the sample size based on the<br>change you need to detect, not on the<br>full size of the test set.<br><br>3. Use random sampling to avoid biased<br>results<br>A random sample gives each example a<br>fair chance to be selected, so the score<br>is more likely to reflect the full test<br>set.<br><br>4. Track uncertainty with confidence<br>intervals<br>A confidence interval shows the likely<br>range of the true score, so you can see<br>when a result is too close to call.<br><br>5. Spend more only when the result is<br>unclear<br>Run a small sample first, then score<br>more examples only when the first result<br>cannot support a decision.</td>
</tr>
<tr>
<td colspan="3">
<strong>Support reply</strong>, task 32, 
<code>faq_support</code>. 
The skill won 12 rules, the baseline won 3, and 10 were ties.
</td>
</tr>
<tr>
<td valign="top" width="33%">Answer this user question helpfully:<br>Why did my export fail with "schema<br>mismatch" after yesterday's deploy?</td>
<td valign="top" width="33%">Your export likely failed because<br>yesterday’s deploy changed the data<br>schema that the export job expects.<br><br>A “schema mismatch” usually means the<br>exporter expected one set of fields,<br>types, or column names, but the data now<br>has something different. Common causes<br>include:<br><br>- A column was renamed, removed, or<br>added<br>- A field type changed, such as `string`<br>to `integer`, `date` to `timestamp`, or<br>nullable to required<br>- The export template or saved query<br>still references the old schema<br>- A downstream destination, such as a<br>warehouse table or CSV mapping, has not<br>been updated<br>- Cached metadata from before the deploy<br>is still being used<br>- A migration ran partially or failed,<br>leaving the app and database out of sync<br><br>To troubleshoot:<br><br>1. Check the deploy notes or migration<br>diff from yesterday.<br>2. Compare the export’s expected schema<br>with the current database/API schema.<br>3. Look for renamed, remov<br><br>[...]</td>
<td valign="top" width="33%">Your export likely failed because<br>yesterday's deploy changed the shape of<br>the data that the exporter writes, but<br>the export schema was not updated at the<br>same time.<br><br>A "schema mismatch" means the exporter<br>produced data with fields or types that<br>did not match what the destination<br>expected. For example, the deploy may<br>have added a new field, renamed a field,<br>removed a field, or changed a value from<br>a string to a number. When the<br>destination checked the export against<br>its saved schema, the check failed and<br>the export stopped.<br><br>The most likely causes are:<br><br>- The deploy changed one or more export<br>fields.<br>- The destination still expects the old<br>schema.<br>- A migration or schema update did not<br>run.<br>- The export job picked up mixed data<br>from before and after the deploy.<br>- A cached schema was still in use after<br>the deploy.<br><br>To debug it, check the export logs for<br>the exact field name in the mismatch<br><br>[...]</td>
</tr>
<tr>
<td colspan="3">
<strong>Engineering brief</strong>, task 67, 
<code>project_update</code>. 
The skill won 11 rules, the baseline won 3, and 11 were ties.
</td>
</tr>
<tr>
<td valign="top" width="33%">Write a short Slack brief for<br>engineering. Cover these facts: search<br>ranking moved from heuristics to a<br>scored model, p95 latency went from<br>900ms to 220ms, recall on long queries<br>is still untested, the old heuristic<br>path is still in the repo as a fallback,<br>dark mode shipped, the invite link bug<br>is fixed, analytics export is blocked on<br>a schema mismatch, the renderer got some<br>cleanup, and a few small copy edits<br>landed.</td>
<td valign="top" width="33%">Engineering brief:<br><br>- Search ranking has moved from<br>heuristics to a scored model.<br>- Search p95 latency improved from<br>~900ms to ~220ms.<br>- Recall on long queries is still<br>untested and needs validation.<br>- The old heuristic ranking path remains<br>in the repo as a fallback.<br>- Dark mode has shipped.<br>- The invite link bug is fixed.<br>- Analytics export is currently blocked<br>on a schema mismatch.<br>- Renderer cleanup landed.<br>- A few small copy edits also went out.</td>
<td valign="top" width="33%">Search ranking now uses a scored model<br>instead of heuristics, and p95 latency<br>fell from 900 ms to 220 ms. The old<br>heuristic path is still in the repo as a<br>fallback. To do: test recall on long<br>queries.<br><br>Shipped:<br>- Dark mode<br>- Invite link fix<br>- Renderer cleanup<br>- Small copy edits<br><br>Blocked:<br>- Analytics export is blocked on a<br>schema mismatch.</td>
</tr>
</tbody>
</table>
