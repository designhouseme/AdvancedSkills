# Design House Skills

[Polska wersja](README.md)

Open skills for AI agents from [Design House](https://designhouse.me). We build websites, automations, video and apps for Polish businesses, and these skills are a simplified version of the process we use to build sites in [Żywa Strona](https://zywastrona.designhouse.me): from researching the company, through the plan and copy, to the code and an independent review.

They work in Claude, ChatGPT/Codex, Cursor, Copilot, Gemini CLI and other tools that support the [Agent Skills](https://agentskills.io) standard.

This is the English version of the skills, in the [`skills-en/`](skills-en/) folder. It follows the same rules as the Polish set in [`skills/`](skills/) and has the same version numbers. Install one language set, not both: the two sets do the same jobs and would compete to trigger.

| Skill | Type | What it does |
|---|---|---|
| [`company-research`](skills-en/company-research/SKILL.md) | standalone | Verifiable research on a specific company: identity, scope of services, customer voice, proof, a claims register with sources |
| [`business-website`](skills-en/business-website/SKILL.md) | chain (orchestrator) | Takes you from a pasted company description to a finished website |
| [`website-plan`](skills-en/website-plan/SKILL.md) | stage 2 | The customer's decision, 4–7 sections, the hero and copy tied to proof |
| [`website-build`](skills-en/website-build/SKILL.md) | stage 3 | Codes the site from the plan and checks the render |
| [`website-review`](skills-en/website-review/SKILL.md) | stage 4 | Independent review with a STATUS and at most 5 fixes |
| [`ui-without-slop`](skills-en/ui-without-slop/SKILL.md) | standalone | Removes typical AI UI decorations (dots in buttons and tags, pills, eyebrows, gradient text) and replaces them with design decisions |

`company-research` and `ui-without-slop` work on their own. `company-research` is also the first stage of the chain, and `ui-without-slop` is used by the build and review stages.

The site copy is written in the language of the business's customers, so the English skills can also produce a site in Polish or German. If the language isn't clear, the skills use the language of your input and record it as an assumption.

## How the chain works

```
company description
   │
   ▼
business-website ──► company-research ──► website-plan ──► [approval] ──► website-build ──► website-review
                     brief/01-research    brief/02-plan                   code + brief/screenshots   brief/03-review
                                                                                ▲                         │
                                                                                └── NEEDS_CHANGES (max 2 rounds)
```

- **State lives in `brief/` files, not in the conversation's memory.** The process can be interrupted and resumed in a new session: the orchestrator looks for the first missing file.
- **One checkpoint:** after the plan, the agent shows the H1, sections and CTA and waits for approval. Say "no questions" to skip it.
- **Review in a fresh context:** where the environment can start a subagent, the review is done by an agent that didn't see the build.
- **Fixes go back to the right stage:** copy and section order to website-plan, code to website-build, facts to company-research.

## Installation

### Option 1: one command (Claude Code, Codex, Cursor, Copilot, Gemini CLI)

You need [Node.js](https://nodejs.org). In a terminal, run:

```bash
npx skills add https://github.com/designhouse-me/dh-skills/tree/main/skills-en
```

The program asks which skills to add and to which tools. When asked about skills, choose all of them if you want to use the website chain. The short form `npx skills add designhouse-me/dh-skills` installs the Polish set.

### Option 2: manually (Claude Code, Codex)

```bash
git clone https://github.com/designhouse-me/dh-skills.git
mkdir -p ~/.claude/skills ~/.agents/skills
cp -r dh-skills/skills-en/* ~/.claude/skills/   # Claude Code
cp -r dh-skills/skills-en/* ~/.agents/skills/   # Codex, Cursor, Copilot, Gemini CLI
```

### Option 3: without a terminal (Claude.ai, ChatGPT)

1. On GitHub, click **Code → Download ZIP** and unpack the file.
2. Zip each folder from the `skills-en/` directory separately (e.g. `company-research.zip`).
3. Upload the ZIPs in Claude.ai settings under Skills. In ChatGPT (business plans) you upload them under Plugins → Skills.

The website chain needs five skills at once: `business-website`, `company-research`, `website-plan`, `website-build` and `website-review`. `company-research` and `ui-without-slop` also work on their own.

### Does it work?

Restart the tool and type, for example:

- "Research Kowalski Joinery in York, tel. …"
- "Make a website for: company name, town, phone, what they do and what the site should achieve"
- "This site looks AI-generated, remove the dots and pills"

In Claude Code you'll see the list of skills after typing `/`, and in Codex after typing `/skills`.

### Updating

`npx skills update` with option 1. With option 2, run `git pull` in the `dh-skills` folder and copy the skills again.

## Tests

- [`evals-en/trigger-evals.json`](evals-en/trigger-evals.json): queries to check that the right skill triggers. The most important ones are the near misses between skills and outside them (competitor analysis, online shop, SEO audit).
- `evals-en/<skill-name>.json`: test cases with assertions for each skill, in the format of Anthropic's skill-creator.
- [`evals-en/fixtures/`](evals-en/fixtures/): fictional research with traps (a `do-not-use` claim, an unconfirmed price, years in business as a "proxy") and a page with deliberate errors for testing the review.

Run each case at least 3 times, with and without the skill, and compare the difference, not the result alone. All companies, numbers and addresses in the tests are fictional; the UK phone numbers come from the Ofcom range reserved for fiction.

What has been checked for the English set so far: the format (`claude plugin validate --strict`), discovery by `npx skills` (6 skills from `skills-en/`, while the short form still finds only the Polish set), the `check_plan.py` script on plans with and without errors, and the grep from `ui-without-slop` on the page with errors (7 of 7 patterns, as on the Polish page). The model evaluations (with and without the skill) were run on the Polish skills; their results are in the [Polish README](README.md#testy). The English evals in `evals-en/` are translations of those cases and haven't been run yet.

## Security

A skill is instructions the agent carries out, so read the files before installing, the same way you'd read someone else's code. The only script in the English set, [`check_plan.py`](skills-en/website-plan/scripts/check_plan.py), uses only the Python standard library, reads two Markdown files and doesn't connect to the network. The skills don't deploy anything to a server, buy domains or submit forms without an explicit request.

## Principles behind it

A few rules that repeat across all the skills:

- **We don't guess facts about the company.** Every fact has a source and a date (`F…`, `V…`, `P…`), and missing data is also a result.
- **Contact details come from the user only.** Online directories often carry old numbers.
- **A fact is not yet an argument:** `fact → permitted inference → consequence for the customer`. Years in business and headcount rarely deserve their own section.
- **Stock or generated images never pose as projects, the team or clients.**
- **The site answers the customer's questions before they get in touch**, instead of listing "About us / Services / Why choose us" modules.

## License

[CC BY 4.0](LICENSE) (Attribution 4.0 International), © 2026 Design House.

You may copy, change and distribute these skills, including commercially and in your own products, as long as you give credit, link to the license and say whether you changed anything. Example attribution:

```
Based on "Design House Skills" (https://github.com/designhouse-me/dh-skills), © Design House, CC BY 4.0 license. Modified.
```

## About Design House

[Design House](https://designhouse.me) builds websites, automations, video and apps for Polish businesses. If you'd rather we built your website for you, have a look at [Żywa Strona](https://zywastrona.designhouse.me).
