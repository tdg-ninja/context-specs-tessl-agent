# Domain discovery — interviewing the human to shape the wiki

*Hackable seam: this is how `wiki-init` Step 1 decides the wiki's taxonomy, tags, and
`raw/` subfolders. Edit it to change the interview.*

**Do not scan a codebase.** This wiki is about a **domain** and the human's **general
architecture best practices** — knowledge that spans projects. Nothing here is derived
from the app being built. The taxonomy comes from a conversation, not a repo.

You are a guide. Open it up, listen, and propose — don't march a form. The goal is to
end Step 1 with the human agreeing on: the domain name + one-liner, the page taxonomy,
the starting tag set, and the `raw/` subfolders.

## What to draw out

**1. The domain and why it matters to them.**
- "What problem space is this wiki about?" (e.g. "SNF survey readiness",
  "event-driven backend architecture", "RAG eval methodology".)
- "What do you want to be able to reason about clearly *before* you start building?"
- Capture a one-line description — it seeds the conventions doc, MOC, and README headers.

**2. The shape of the knowledge → the page taxonomy.**
The default taxonomy is `concept / entity / workflow / source / index`. Pressure-test it
against their domain and adapt the emphasis (not the five types):
- **Concepts** dominate when the domain is ideas, patterns, distinctions, techniques.
- **Entities** dominate when there are many named things — orgs, roles, regulations,
  tools, vendors, products, protocols.
- **Workflows** dominate when the domain is procedural — multi-step practices.
Ask: "When you picture the pages, are they mostly *ideas*, *named things*, or
*step-by-step procedures*?" Use the answer to tell them which folders will fill first
(and to seed MOC sections), not to remove a type.

**3. Architecture best-practices angle.**
Because this wiki also captures *general architecture best practices*, ask whether there's
an architecture/engineering lens that should be first-class — e.g. patterns, trade-offs,
reference designs, anti-patterns. These usually live as `concept` pages; just make sure
the MOC has a section for them if the human cares about that lens.

**4. The sources they have (or will have) → `raw/` subfolders.**
Offer the standard set and trim to what they'll actually use:
- `raw/articles/` — references, guidance docs, blog posts, papers, PDFs
- `raw/transcripts/` — audio/video transcripts (talks, interviews, walkthroughs)
- `raw/course/` — course material
- `raw/tweets/` — tweet threads
- `raw/markdown-files/` — research done with LLM chatbots markdown files
- `raw/repos/` — notes copied from repos
- `raw/google-drive/` - docs from google drive

Ask: "What kinds of material will you be dropping in?" Create only the subfolders that fit.

**5. A starting tag set.**
Propose a small set anchored on a domain slug, e.g. `[<domain-slug>, ...]`. Tags are
cheap to add later; start minimal.

## Output of Step 1

Propose all of the above back to the user as a short spec:

```
DOMAIN:      <name> — <one-liner>
TAXONOMY:    concept / entity / workflow / source / index
             (expect <type(s)> to dominate; MOC seeded with sections: <...>)
RAW FOLDERS: raw/{articles, transcripts, ...}
TAGS:        [<domain-slug>, ...]
```

Refine until it fits, then carry these values into the plan-pass (Step 2) where they fill
the conventions doc, the MOC template, and the README.
