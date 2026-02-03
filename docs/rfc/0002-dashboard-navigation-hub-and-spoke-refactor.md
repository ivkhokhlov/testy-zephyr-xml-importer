RFC 0002: Dashboard Navigation Hub-and-Spoke Refactor

Problem statement

The current dashboard page (`/plugins/zephyr-xml-importer/`) presents two competing navigation
mechanisms:

- A header "Import/Export" nav with an "active" (primary) state pre-selected.
- Two cards ("Import" and "Export") that also contain primary CTA buttons to the same routes.

This creates a mixed navigation model where the dashboard simultaneously behaves like:
(1) a tabbed page with an active state, and (2) a dispatcher page with two task choices.

As a result, users can be misled into thinking "Import" is already selected, and the page has three
visually competing primary actions.

Motivation

- Reduce cognitive load and misclicks on the first screen.
- Make the dashboard clearly act as a task dispatcher (Hub) rather than a partial duplicate of
  Import/Export pages.
- Provide clearer orientation on internal pages (Spokes) with explicit "Back" and "Switch" links.

Goals

- On the dashboard (index), remove header-level navigation that implies an active tab state.
- Keep the Import/Export cards as the only entry points (primary CTAs) from the dashboard.
- On internal pages (`/import/`, `/export/`), provide lightweight navigation:
  - back to dashboard
  - switch to the other task
- Preserve existing routes and backend behavior (HTML-only change).

Non-goals

- Redesigning the overall styling system or extracting shared CSS into separate static files.
- Adding new import/export functionality, changing APIs, or altering permissions.
- Introducing client-side routing; links remain standard anchors.

Proposed design

External behavior / user-facing impact

- Dashboard (`/plugins/zephyr-xml-importer/`):
  - Shows title, short instruction text, and two equal cards (Import and Export).
  - No header navigation buttons.
  - Card buttons remain visually primary to guide the next action.
- Import (`.../import/`) and Export (`.../export/`):
  - Header includes a small nav row:
    - "← Back to Dashboard" (returns to index)
    - "Switch to Export" / "Switch to Import" (moves between spokes)

Templates and link strategy

- Update `zephyr_xml_importer/templates/zephyr_xml_importer/index.html`:
  - Remove the `<div class="nav">...</div>` block inside `<header>`.
  - Keep the card CTA buttons as-is (or update labels; see below).
  - Update the header copy to instruct the user to pick an action.
- Update `zephyr_xml_importer/templates/zephyr_xml_importer/import.html` and
  `zephyr_xml_importer/templates/zephyr_xml_importer/export.html`:
  - Add a `<div class="nav">` inside the header.
  - Use relative links to avoid hard-coding the plugin mount path:
    - Back: `href="../"`
    - Switch: `href="../export/"` (from import) and `href="../import/"` (from export)

Visual treatment

- Dashboard card CTAs keep the `.primary` styling to remain the single dominant actions on that
  page.
- Internal-page header nav links should not look like active tabs:
  - no `.primary`
  - neutral styling (bordered links, muted background, or simple text links)
  - consistent placement (right side of header, or below the title block)

Copy (optional but recommended)

- Change dashboard CTA labels for clarity and consistency:
  - "Open import" -> "Start Import"
  - "Open export" -> "Start Export"
- Keep the card titles ("Import", "Export") unchanged.

Implementation plan

1) Update dashboard template
   - Remove header `.nav` from `index.html`.
   - Adjust header description text and spacing around the version block.

2) Add internal-page navigation
   - Add header nav links to `import.html` and `export.html`.
   - Add minimal `.nav` CSS to those templates (or reuse existing styles) to keep appearance
     consistent and non-tab-like.

3) Manual QA / regression checks
   - Verify dashboard shows only two primary buttons (the card CTAs).
   - Verify links work when the plugin is mounted under a non-root prefix (relative links).
   - Verify import/export pages provide a working "Back" and "Switch" navigation path.

4) Documentation (if needed)
   - Update `docs/usage.md` screenshots or text if it references the old header navigation.

Acceptance criteria

- On the dashboard page, there is no header navigation section for Import/Export.
- The dashboard has exactly two primary CTAs: the Import card button and the Export card button.
- Clicking the Import card CTA navigates to `/import/`; clicking the Export card CTA navigates to
  `/export/`.
- The Import page header includes:
  - a link that navigates back to the dashboard
  - a link that navigates to the Export page
- The Export page header includes:
  - a link that navigates back to the dashboard
  - a link that navigates to the Import page
- (If copy changes are implemented) dashboard CTA labels read "Start Import" and "Start Export".

Risks

- Relative-link navigation (`../`) assumes the URLs keep trailing slashes and do not change their
  structure; future route changes would require updating templates.
- Visual regressions are possible because templates currently duplicate CSS per page; styling changes
  must be applied consistently across templates.

Open questions

- Should the internal-page nav be placed in the existing header flex row (right-aligned), or below
  the title block for better responsiveness?
- Do we want to enforce the copy change ("Start Import/Start Export") as part of this ticket, or
  keep it optional?
