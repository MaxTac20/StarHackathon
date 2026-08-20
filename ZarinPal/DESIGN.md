# ZarinPal UI design system

## Authority and implementation

Material UI (MUI) is the primary and authoritative design system.

- Use `@mui/material` for application UI and `@mui/icons-material` for icons.
- Use `@mui/x-charts` for analytical visualization, `@mui/x-data-grid` for
  data-heavy tables, and `@mui/x-date-pickers` for date and range controls.
- `frontend/src/app/theme.ts` is the single source of truth for colors,
  typography, spacing, shape, shadows, breakpoints, component appearance, and
  light/dark mode.
- Prefer theme configuration, component variants, and reusable domain
  components before local `sx` styling. Do not hardcode a design value when a
  theme token exists.

shadcn/ui is secondary. Use it only when MUI and MUI X have no appropriate
component or it offers a substantial advantage. Never use shadcn alternatives
for standardized MUI buttons, inputs, selects, dialogs, tabs, cards, tooltips,
menus, or tables. Any retained shadcn component must be isolated and visually
conform to the MUI theme; do not mix MUI and shadcn versions of one primitive.

Before adding a primitive, check MUI, then MUI X, and only then consider shadcn
or a custom implementation.

## Language and direction

Persian (`fa-IR`) is primary: set `lang="fa"`, `dir="rtl"`, and use MUI's
`faIR` localization where supported. English (`en`) is complete and uses
`lang="en"`, `dir="ltr"`.

Set direction at the document, theme, and Emotion cache levels. Use logical
layout rather than reversing individual rows. Isolate merchant IDs,
transaction IDs, session keys, PSP codes, masked cards, API values, and
appropriate timestamps as LTR content, using monospace where it improves
scanning.

## Typography

Self-host Vazirmatn as the primary Persian font and Inter as the English font,
then fall back to Roboto, Arial, and sans-serif. Use only weights 400, 500, 600,
and 700.

| Role | Size | Weight | Line height |
|---|---:|---:|---:|
| Display / major page title | 32 px | 700 | 1.3 |
| h1 | 28 px | 700 | 1.3 |
| h2 | 24 px | 600 | theme default |
| h3 | 20 px | 600 | theme default |
| body1 | 16 px | 400 | 1.7 |
| body2 | 14 px | 400 | 1.6 |
| label | 14 px | 500 | theme default |
| caption | 12 px | 400 | theme default |
| KPI value | 28–32 px | 700 | theme default |

Do not use text smaller than 12 px.

## Semantic colors

| Role | Light value |
|---|---|
| Primary | `#2563EB` |
| Primary dark | `#1D4ED8` |
| Primary light | `#DBEAFE` |
| Secondary | `#0F766E` |
| Success | `#16A34A` |
| Warning | `#D97706` |
| Error | `#DC2626` |
| Info | `#0284C7` |
| Background | `#F8FAFC` |
| Paper | `#FFFFFF` |
| Primary text | `#0F172A` |
| Secondary text | `#475569` |
| Disabled text | `#94A3B8` |
| Divider | `#E2E8F0` |

Dark-mode values live beside these roles in the central theme. Never use
success or error colors decoratively: green means success or positive, red
means error/failure/negative, orange means warning, and blue means information
or primary action.

## Spacing, shape, and elevation

Use MUI's 8 px spacing unit. Prefer 4 px for very tight space, 8 px between
related elements, 16 px within components, 24 px between groups, 32 px between
sections, and 48 px for major page separation. Avoid arbitrary spacing.

The default radius is 10 px; small controls use 8 px, cards 12 px, and large
containers/dialogs 12–16 px. Avoid pills unless semantics require them. Favor
borders, subtle surface differences, and whitespace over shadows. Cards
normally have a subtle border and zero or low elevation.

## Layout and product components

Main content is bounded at 1600 px. Use 24–32 px desktop padding, 20–24 px on
tablet, and 16 px on mobile. Dashboard grids use responsive MUI Grid layouts;
primary information must remain usable on mobile, tablet, laptop, and desktop.

Compose MUI primitives rather than recreating them. Add reusable domain
components when they encode product meaning, such as `KpiCard`,
`PaymentStatusChip`, `TransactionTable`, `PspPerformanceChart`,
`FailureBreakdown`, and `DashboardSection`.

## Dashboard and analytics principles

Present information in this order:

1. Current health/status.
2. Primary KPIs.
3. Trends.
4. Problems and anomalies.
5. Breakdown and diagnosis.
6. Detailed transactional data.

Every chart must answer a merchant question. Avoid filler charts, excessive
pie charts or gradients, decorative icons, oversized KPI cards, and dashboards
made entirely of cards. Prefer professional financial-product density.

Trends normally use lines/areas and composition uses bars. Use pie/donut only
for a small stable category set. Start bar axes at zero; do not truncate or use
dual axes without an explicit warning. Tooltips expose exact values,
population, and unknown counts. Preserve Unknown as a neutral category and
provide an accessible text/table alternative.

Every metric surface exposes its definition, version, grain, formula,
numerator/denominator, time basis, timezone, filters, freshness, null handling,
and a route to contributing transactions as specified in `docs/metrics.md`.

## Data formatting

Use locale-aware formatting. Persian user-facing amounts use thousands
separators and state the confirmed unit. Percentages normally show at most one
or two decimals. Show latency in milliseconds below 1000 ms and seconds where
appropriate above it. Storage/API dates remain ISO/Gregorian; Persian UI may
show Jalali only after the calendar decision is confirmed, while English uses
Gregorian.

Do not present unresolved currency, timezone, calendar, or status semantics as
facts. Keep sensitive identifiers masked and merchant scope enforced on the
server.

## Accessibility and review

Target WCAG 2.2 AA. All interactive elements are keyboard accessible, have
visible focus, and have accessible localized names. Do not use color as the
only status carrier. Charts require labels/tooltips and equivalent textual
information. Respect reduced motion.

Review every user-facing slice in Persian and English, RTL and LTR, light and
dark, and at mobile and desktop widths. Cover loading, empty, error, unknown,
partial-data, and zero-denominator states.

Do not add colors, fonts, spacing scales, radii, or component libraries without
updating this contract and `frontend/src/app/theme.ts`.
