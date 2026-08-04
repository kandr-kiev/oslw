# Local LLM Wiki Algorithm

> **Дата останнього оновлення:** 2026-07-25
> **Версія системи:** 2.0.0 (OOP Refactor)

## 0. Session Orientation

Before any operation:
1. Read `AGENTS.md` (agent contract & graph-first protocol).
2. Read `SCHEMA.md` (tag taxonomy & conventions).
3. Read `wiki/index.md` (wiki page index).
4. Read recent `log.md` entries.
5. Search existing wiki pages for the target topic.

Completion criterion: agent knows existing pages, taxonomy, and recent work.

---

## 1. Ingest Algorithm

**Input:** URL, file path, pasted text, or transcript.

**v2.0 CLI:** `llmwiki ingest [--dry-run] [--limit N]`
**v2.0 Python:** `IntegratorTool.ingest(url)`

### Steps

1. **Capture raw source.**
   - URL: `web_extract()` → extract markdown/text → save under `raw/articles/` unless it is a paper/transcript.
   - File: copy/extract readable text into `raw/<type>/`.
   - Paste: save as timestamped raw note.
2. **Add raw frontmatter:** `source_url`, `ingested`, `sha256`.
3. **Check existing pages** by searching `index.md` and `wiki/**/*.md`.
4. **Extract central concepts/entities.**
5. **For each central concept/entity:**
   - create page if threshold is met;
   - otherwise update an existing page;
   - add sources and confidence.
6. **Update cross-links.**
7. **Update `index.md`** alphabetically inside sections.
8. **Append one `log.md` entry** listing all created/updated files.
9. **Run lint and record findings.**

### v2.0 Pipeline

```
External Source → raw/ (immutable) → IntegratorTool → wiki/ (mutable)
     ↓                 ↓                  ↓              ↓
  URL/Paste        SHA256 verify    Classify +     Index + Log
  (RSS/GitHub)     Atomic write     Generate       Updated
```

---

## 2. Query Algorithm

**Input:** user question.

**v2.0 CLI:** `llmwiki graphify query <query> --depth N --json`

### Steps

1. **Graph-First Protocol (MANDATORY):**
   - Load graph: `graphify-out/graph.json`
   - Find seed node(s) for the query topic
   - BFS(depth=2) to discover connected pages
   - Community filter: prioritize pages from relevant community
2. **Read `index.md`** and relevant wiki pages from BFS results (top-5).
3. **If wiki pages are missing or low-confidence**, inspect raw sources.
4. **Answer with citations** to wiki pages and raw sources.
5. **If answer is reusable or analytical**, save it under `wiki/queries/` or `wiki/comparisons/`.
6. **Update `index.md` and `log.md`** if a page was filed.

### Why Graph-First?

- **Graph** gives structure: which pages are related, community membership, bridge nodes
- **Wiki** gives content: actual text, analysis, context
- **Graph-first** prevents reading irrelevant pages and ensures comprehensive coverage
- **BFS depth 2** covers 80% of relevant context without noise

---

## 3. Lint Algorithm

**v2.0 CLI:** `llmwiki maintenance wiki-lint`
**v2.0 Python:** `WikiLintTool.scan_all()`

### Steps

1. Enumerate all markdown files under `wiki/` excluding README placeholders.
2. Validate frontmatter (YAML parsing, required fields).
3. Validate required fields: `type`, `title`, `description`, `created`, `updated`, `tags`, `sources`, `confidence`, `links`.
4. Validate tags against `SCHEMA.md` taxonomy (via `services/utils.py::APPROVED_TAGS`).
5. Extract `[[wikilinks]]`; flag links that do not resolve to a known page slug.
6. Check every wiki page appears in `index.md`.
7. Recompute raw body `sha256`; flag drift.
8. Flag pages over 200 lines.
9. Flag `confidence: low` and `contested: true` for review.
10. Write report to `outputs/lint-report.md`.
11. Append result to `log.md`.

### v2.0 Maintenance Commands

```bash
# Full diagnostic + auto-cure (6 layers, 7 cures)
llmwiki doctor --cure

# Diagnosis only
llmwiki doctor

# Lint only
llmwiki maintenance wiki-lint

# Fix wikilinks
llmwiki maintenance fix-wikilinks

# Fix SHA256 drift
llmwiki maintenance fix-sha256

# Cleanup duplicates
llmwiki maintenance cleanup-duplicates --apply
```

---

## 4. Update Policy

When new information conflicts with old synthesis:
1. Prefer raw source over wiki synthesis.
2. Prefer newer source only if equally authoritative.
3. Preserve both claims if the conflict is unresolved.
4. Mark page `contested: true` and reduce confidence.
5. Log the conflict.

---

## 5. Naming Algorithm

1. Lowercase.
2. Transliterate only when needed; keep established English technical names.
3. Replace spaces and punctuation with hyphens.
4. Avoid duplicate slugs.
5. Use folder by type:
   - concepts → `wiki/concepts/<slug>.md`
   - entities → `wiki/entities/<slug>.md`
   - comparisons → `wiki/comparisons/<slug>.md`
   - playbooks → `wiki/playbooks/<slug>.md`
   - synthesis → `wiki/synthesis/<slug>.md`
   - queries → `wiki/queries/<slug>.md`
   - references → `wiki/references/<slug>.md`
   - templates → `wiki/templates/<slug>.md`

---

## 6. Graph-First Protocol (Detailed)

### Algorithm: graph → wiki → synthesis

1. **Load graph:** `python3 -c "import json; g=json.load(open('graphify-out/graph-from-wiki.json'))"` — get nodes, edges, communities
2. **Seed BFS:** Find the most relevant node(s) for the query topic → BFS(depth=2) to discover connected pages
3. **Community filter:** If node has a community, prioritize pages from that community
4. **Content load:** Read only the top-5 wiki pages from BFS results: `wiki/{slug}.md`
5. **Synthesize:** Answer from the loaded pages. If graph returned 0 results → read wiki/index.md, search by keyword
6. **Report structure:** When returning an answer, mention the graph path used: "discovered via graph BFS from {seed} → {n} connected pages"

### Quick graph queries

```python
# BFS from seed
import json
g = json.load(open('graphify-out/graph-from-wiki.json'))
def bfs(seed, depth=2):
    visited = {seed}; queue = [(seed, 0)]; result = []
    while queue:
        node, d = queue.pop(0)
        if d > depth: continue
        result.append(node)
        for e in g['edges']:
            if e['source'] == node and e['target'] not in visited:
                visited.add(e['target']); queue.append((e['target'], d+1))
            elif e['target'] == node and e['source'] not in visited:
                visited.add(e['source']); queue.append((e['source'], d+1))
    return result

# God nodes (most linked)
top = sorted(g['nodes'], key=lambda n: n.get('inbound',0), reverse=True)[:5]

# Orphans (0 inbound, 0 outbound)
orphans = [n for n in g['nodes'] if n.get('inbound',0)==0 and n.get('outbound',0)==0]

# Community by tag
comm = [n for n in g['nodes'] if 'llm' in n.get('tags',[])]
```

### Graph maintenance (cron jobs)

- **Every 6h** (`graphify-scan`): Run `wiki_graph_generator.py` → `graphify_bridge.py --auto-fix`
- **Weekly** (`llm-wiki graphify weekly scan`): Full gap analysis + orphan report

### Graphify CLI (advanced)

`graphify query "question" --graph graphify-out/graph-from-wiki.json` — BFS traversal
`graphify path "A" "B" --graph graphify-out/graph-from-wiki.json` — shortest path
`graphify explain "X" --graph graphify-out/graph-from-wiki.json` — node + neighbors
- `graphify watch wiki/` — auto-rebuild on changes

---

## 7. Claude Code Handoff

When asked to implement:
1. Treat `docs/ARCHITECTURE.md` and `docs/ALGORITHM.md` as the software requirements.
2. Modify only files inside `/workspace/llm-wiki` unless explicitly instructed.
3. Do not read secrets or config files outside the workspace.
4. Verify with lint before reporting success.
