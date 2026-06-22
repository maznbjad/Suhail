# Sprint 69 — Summary Knowledge Linking

## Scope
- Kept the 72 previously approved physics summaries only.
- Added no chemistry, mathematics, biology, ecology, verbal, or quantitative summaries.
- Converted the existing physics content into stable, editable knowledge blocks.

## Results
- Physics summaries: **72**
- Knowledge blocks: **936**
- Physics questions: **600**
- Linked physics questions: **600**
- Unlinked physics questions: **0**

## Knowledge block types
- comparison: 216
- definition: 216
- example: 72
- idea: 72
- relationship: 72
- rule: 72
- tip: 144
- trap: 72

## Student experience
- Every linked physics question displays the exact related summary information, not only the lesson name.
- The related block opens in a focused sheet with its title, content, lesson, unit, and book.
- Saved questions now store the question number, answer, explanation, and linked knowledge block.
- The summary page includes a **جوهر الملخص** section and the number of linked questions.
- Dark mode styles are included for all new components.

## Admin/content structure
- Block IDs stay stable after publishing.
- A question has one primary knowledge block and may receive secondary links later.
- Links are editable in the question editor schema.
- The content workflow includes: unlinked, automatically linked, reviewed, and approved states.

## Important boundary
This release links only the already-approved physics summaries. Other subjects remain without summaries, following the product decision not to create new summaries automatically.
