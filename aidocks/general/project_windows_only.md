---
name: project_windows_only
description: "The port is strictly for Windows: no Linux or macOS builds, no GitHub Actions release workflow. Releases are built, zipped and uploaded from the dev's own machine."
metadata:
  node_type: memory
  type: project
---

**The port is strictly for Windows.** There are no Linux or macOS runs, builds or releases, and no GitHub Actions release workflow.

**Why:** The repo is named Heathcote-Windows, and on 2026-10-19 the dev agreed to adopt the reference repo's working rules, which are Windows only.

**How to apply:**
- Write platform code for Windows only: `%APPDATA%` for the save, and the NVDA client and Prism for speech. No per-system tables, Linux libraries or macOS bundles.
- `compiler.py` and `releaser.py` build and release from the dev's own machine. They need their own plan in `aidocks/plans/` first ([[feedback_record_plans_first]]).
