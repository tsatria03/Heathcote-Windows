---
name: feedback_review_plan_sections
description: "Before a plan is built, review each of its sections with the dev, and never start building it until the dev says so after that review."
metadata:
  node_type: memory
  type: feedback
---

**Every plan gets a review of each of its sections before it is built** (the dev, 2026-10-19, after plan 2 was finished: "Do not start plan 3. I need a review of each section for that plan. Remember that for each plan.").

**Why:** a plan is written long before it is built, and much can change in between, as the title volume did. Going through it section by section, just before building, lets the dev catch what no longer fits.

**How to apply:**
- When a plan is finished, never move on to the next by yourself. Offer its review instead.
- **The review goes section by section.** For each section, give:
  - what it builds, in plain words
  - the decisions it rests on, with anything that has changed since the plan was written, or that an earlier plan's build has changed
  - anything still uncertain, such as a number to check in the original's code
  - what the dev will test by ear, and whether each test is optional or mandatory ([[feedback_say_ear_tests_ahead]])
- Ask one question at a time about anything the review turns up ([[feedback_one_question_at_a_time]]). Changes go into the plan and are committed before building.
- Building starts only when the dev says so after the review.
