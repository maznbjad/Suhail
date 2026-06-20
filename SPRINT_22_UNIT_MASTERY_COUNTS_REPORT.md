# Sprint 22 — Compact unit cards with mastery counters

- Reduced unit card height and removed keyword chips from unit cards.
- Added two progress rows to each unit card:
  - 📘 التعاريف `0/total`
  - 📐 القوانين `0/total`
- Counts are computed from the actual unit data:
  - definitions count from `definitions`
  - laws count from `formula_cards`
- Progress is currently zero until Sprint 23/24 adds mastery interactions.
- Added `data/content/mastery_schema.json` as the base structure for mastery status.
