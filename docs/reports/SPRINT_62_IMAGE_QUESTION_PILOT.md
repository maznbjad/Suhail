# Sprint 62 - Image Question Pilot

## Scope

This sprint establishes the final visual-question standard before processing the remaining uploaded Qudurat compilations.

## Implemented

- Added 12 original quantitative questions with newly drawn transparent SVG diagrams.
- Increased the image-question total from 21 to 33.
- Removed full-canvas backgrounds from all 33 question SVGs.
- Added tap-to-zoom for every question image.
- Added descriptive alternative text and captions.
- Assigned a visible public number to every question, from 260001 through 260292.
- Reserved 260293 as the next question number.
- Removed the computerized/paper distinction from the question data and interface.
- Added structured educational explanations:
  - core idea;
  - solution steps;
  - common trap;
  - Suhail hint;
  - clarification of a close answer choice only where relevant.
- Added an editable question schema for the future admin editor.
- Added compact internal summary headers and reduced the account-page bottom gap.

## Pilot visual topics

1. Bar-chart difference.
2. Line-chart average.
3. Square and semicircle area.
4. Comparing areas with the same diagonal.
5. Midpoint on a coordinate plane.
6. Connected tables and seats.
7. Perimeter of an L-shaped figure.
8. Triangle area.
9. Circular sector area.
10. Shaded fraction grid.
11. Coordinate translation.
12. Venn diagram union.

## Content safety

The pilot uses the uploaded compilations to identify question patterns only. The wording, numbers, diagrams, answer choices and explanations were rebuilt for Suhail.

## QA result

- 292 unique questions.
- 292 sequential public IDs.
- 33 existing and valid image questions.
- 12 pilot questions with structured explanations.
- JSON and SQLite counts match.
- Python and JavaScript syntax checks pass.
- All SVGs parse successfully.
