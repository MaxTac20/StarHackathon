# ZarinPal analytics design system

## Direction

The product should feel calm, precise, and operational: dense enough for payment
analysis without resembling a raw back-office table. Use progressive disclosure—lead
with a small set of decision-ready signals, then offer breakdowns and transaction-level
evidence.

The implementation foundation is the repository's existing
[shadcn/ui](https://ui.shadcn.com/) New York style, built on accessible
[Radix Primitives](https://www.radix-ui.com/primitives) and Tailwind CSS semantic tokens.
This is a source-owned design system: use existing shadcn components first, compose them
for product patterns, and add custom primitives only when a repeated need is proven.

## Experience foundations

### Language and direction

- Default to Persian (`fa`, `dir="rtl"`); offer complete English (`en`, `dir="ltr"`).
- Set direction at the document/app shell so layout primitives adapt naturally.
- Use logical alignment and spacing. Do not encode “right means start” in components.
- Place IDs, response codes, masked card values, and code snippets in isolated LTR spans.
- Use a Persian-capable UI font such as
  [Vazirmatn](https://github.com/rastikerdar/vazirmatn), with a tested system fallback;
  package font assets for production instead of depending on a runtime CDN.
- Use locale-aware number/date formatting. Keep identifiers in Latin digits to prevent
  transcription errors; decide currency unit, timezone, and calendar only after the
  data contract is confirmed.

### Theme

Support system preference plus explicit Light, Dark, and System choices. Persist the
choice locally without flashing the wrong theme on load. Both themes use the same
semantic roles; theme variables change, component intent does not.

Current tokens live in `frontend/src/styles/globals.css`. Evolve them around these roles:

| Role | Use |
|---|---|
| `background` / `foreground` | App canvas and primary text |
| `card` / `card-foreground` | Panels, KPI cards, and elevated data surfaces |
| `primary` / `primary-foreground` | Primary action and selected navigation |
| `muted` / `muted-foreground` | Secondary surfaces, labels, and context |
| `accent` / `accent-foreground` | Hovered or emphasized neutral content |
| `destructive` | Errors and destructive actions, never failure-chart data by itself |
| `border`, `input`, `ring` | Structure, controls, and keyboard focus |

Add chart/status tokens as semantic CSS variables before building charts (success,
failure, warning, informational, and a categorical series palette). Never hardcode raw
Tailwind color utilities inside product components or add manual `dark:` color fixes.

### Accessibility

Target WCAG 2.2 AA. Keyboard focus is always visible; icon-only actions have localized
accessible names; touch targets are comfortable; motion respects reduced-motion
preferences. Color is never the only carrier of status—pair it with text, shape, icon,
or line treatment. Charts require a text summary and accessible tabular alternative.

## Layout and hierarchy

- Desktop uses an RTL-aware collapsible sidebar, top context bar, and bounded content
  canvas. Mobile navigation becomes a sheet and filters become a focused drawer/sheet.
- Use an 8 px spacing rhythm and restrained radii. Favor alignment and whitespace over
  decorative borders.
- Page order: title/context, global filters and freshness, primary KPIs, trend, diagnostic
  breakdowns, then detailed records.
- Keep the default overview to roughly 4–6 primary KPI cards. Secondary metrics belong
  in later sections rather than a wall of equal-weight cards.
- Sticky table headers and filter summaries are useful; horizontally scrolling the
  entire page is not.

## Component patterns

Use shadcn `Sidebar`, `Card`, `Chart`, `Table`, `Tabs`, `Badge`, `Tooltip`/`Popover`,
`Sheet`, `Skeleton`, `Alert`, `Empty`, and `Separator` patterns as they are introduced.
Cards use their full header/title/description/content/footer composition. Forms use the
project's form primitives, and status labels use badges plus semantic tokens.

### KPI card

A KPI card contains a localized label, primary formatted value, comparison with explicit
period, compact context (numerator/denominator or sample size), and a metric-definition
action. The whole card is not clickable unless it has one unambiguous destination.

### Charts

- Trends use lines/areas; composition uses bars; use pie/donut charts only for a small,
  stable number of categories where angle comparison is not the main task.
- Start axes at zero for bars. Do not truncate or dual-axis without an explicit warning.
- Tooltips show the timestamp/category, exact value, population, and missing/unknown
  count where relevant.
- “Unknown” remains a visible neutral category. Limit ranked charts and group the tail as
  “Other,” with full results available in a table.
- Never use green/red alone. Series must remain distinguishable in both themes and for
  common color-vision deficiencies.

### Tables and drill-down

Transaction tables show whether each row is a session or an attempt, retain filter
context, support useful sorting, and provide a session-to-attempt detail view. Mask payer
card tokens by default. Empty, loading, error, and partial-data states are designed—not
represented by an empty rectangle.

### Metric explanation

Every KPI/chart has a consistent explanation affordance. Use a popover for a concise
formula and a sheet/dialog or metric-guide route for the complete contract. Include the
metric version, grain, formula, numerator/denominator, time basis, timezone, filters,
freshness, null handling, and “View transactions” action described in
[docs/metrics.md](docs/metrics.md).

## Content voice

Use direct, neutral, non-blaming language. Prefer “Verification rate decreased by 2.1
percentage points” over “Payments are failing badly.” Distinguish percentage points from
percent change. Explain abbreviations on first use in each context, and never translate
opaque PSP/bank/response codes.

Persian is authored as product copy, not left as a late machine-translation pass. English
and Persian messages should communicate the same action and severity even when their
lengths differ.

## Review checklist

- Persian default, complete English, correct RTL/LTR and mixed-direction data
- Light and dark screenshots at mobile and desktop widths
- Semantic tokens only; sufficient contrast and visible keyboard focus
- Metric formula, grain, filters, period, timezone, freshness, and drill-down available
- Loading, empty, error, unknown, and zero-denominator states covered
- Charts understandable without color and paired with accessible data
- Sensitive identifiers masked and merchant scope enforced server-side
- Components composed from the existing shadcn foundation before custom UI is added
