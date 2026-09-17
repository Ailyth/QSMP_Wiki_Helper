# Abandoned CCS Action Plan

## Objective
Turn the current desktop helper into a browser-based product that is usable by external users, while adding new capabilities in a way that does not break the working data pipeline.

## Guiding principle
Do not do one giant rewrite first.

Instead, keep the current logic stable, separate the business logic from the UI, and add new functionality in small slices. Once the data flow is reliable, move the interface to a browser app and then deploy it for external use.

---

## What to keep from the current project
The project already has a strong foundation in the following files:
- [main.py](main.py): orchestrates the full processing flow
- [logic.py](logic.py): core merge and grouping logic
- [wiki_generator.py](wiki_generator.py): text generation
- [data_loader.py](data_loader.py): Google Sheets access
- [activity_parser.py](activity_parser.py) and [vod_parser.py](vod_parser.py): source parsing
- [gui/gui.py](gui/gui.py): current UI layer, which should be replaced later

These are the pieces worth preserving. The main thing to change is the presentation layer, not the core data processing.

---

## Concrete product direction
The product should be a small internal/external web dashboard with tabs, not a raw technical tool.

### Tab 1: Overview
Purpose:
- show all creators at a glance
- summarize missing data, inactive creators, and issues
- act as the landing screen

Features:
- total creator count
- number of days with activity
- missing VOD count
- recent refresh timestamp
- quick search

### Tab 2: Creators
Purpose:
- browse all creators and their history
- filter by date and status
- work with the main business value of the app

Features:
- creator list
- activity timeline
- per-creator summary
- date filters
- status badges

### Tab 3: VOD Review
Purpose:
- review matches and mismatches between activity and VODs
- identify missing or suspicious data

Features:
- matched / unmatched summary
- list of uncertain matches
- allow manual correction or status override
- reason labels for mismatches

### Tab 4: Wiki Preview
Purpose:
- show generated wiki text before copying or publishing
- make the output readable and easy to verify

Features:
- creator-specific preview
- month grouping
- copy text button
- export to TXT

### Tab 5: Settings
Purpose:
- configure sources, creators, templates, and display options
- keep non-technical users from editing raw code

Features:
- source spreadsheet URLs
- allowed creators
- custom mapping
- output format options
- template configuration

### Tab 6: Admin / Data Quality
Purpose:
- show errors and operational health
- support future maintenance

Features:
- last sync time
- missing field warnings
- failed rows
- refresh actions
- issue logs

---

## Should new features be implemented before the web transition?

### Yes, but only in a focused way
Do not wait to add features until the full web app exists. But do not add broad “nice-to-have” features either.

### Good features to add before the transition
Choose features that:
- support the current production workflow
- are connected to the current data model
- can be validated quickly
- do not force a full redesign of the app

Examples:
- creator overview dashboard
- better creator filtering
- VOD mismatch review panel
- wiki preview page
- export functionality
- settings page for allowed creators and URLs

### Features to postpone
Do not build these before the browser migration unless they are essential:
- elaborate role-based access control
- advanced analytics dashboards
- complex multi-user permissions
- personalization settings for every user
- deep admin tooling for public users

These work better after the product structure is stable.

---

## Required work before moving smoothly to web

### 1. Stabilize the data contract
Create a clear understanding of the objects that move through the app:
- creator
- server_day
- calendar_day
- wiki_date
- VOD entry
- activity entry
- matched status
- unmatched status

These should be consistent across backend, UI, and output generation.

### 2. Separate the backend from the UI
Refactor the current code so the data processing layer can be reused from both:
- the desktop workflow
- the future browser API

This is the most important technical step.

### 3. Build a simple API layer
Create a backend service with endpoints like:
- GET /creators
- GET /creator/{name}
- GET /wiki/{name}
- GET /overview
- GET /vod-review

This gives the browser app a clean way to consume the same logic.

### 4. Move config out of code
The app should not depend on hard-coded values in the UI or logic for the long term.
Store:
- spreadsheet URLs
- allowed creators
- template files
- output settings
- date rules

in config files or environment variables.

### 5. Make UI decisions user-friendly
For external users, use:
- cards instead of raw data dumps
- clear statuses and labels
- search and filters
- big action buttons
- preview before confirm/export

The UI should hide technical details when possible.

### 6. Add validation checks
Before shipping externally, add checks for:
- missing creator mappings
- date mismatches
- missing VOD entries
- malformed wiki output
- creator names not found in config

This avoids broken experiences caused by dirty source data.

### 7. Prepare for hosted deployment
Before going public, ensure the app supports:
- environment variables
- secrets management
- hosted Google auth or service account access
- browser-safe APIs
- error handling for public users

---

## Concrete build sequence

### Phase 1: Refactor and stabilize
- Confirm the current pipeline works end-to-end
- Separate data logic from GUI code
- Define the core data objects
- Add basic validation for missing or bad data

Goal: the project should produce the same output from a backend service as it does from the desktop version.

### Phase 2: Add high-value feature slices
Implement these next in priority order:
1. creator overview
2. date and creator filters
3. VOD mismatch review
4. wiki text preview
5. export/copy actions
6. settings page

Goal: the app becomes useful to a user without requiring technical knowledge.

### Phase 3: Build the browser shell
Create a browser app with tabs and page-level navigation:
- Overview
- Creators
- VOD Review
- Wiki Preview
- Settings
- Admin / Data Quality

Goal: a clean and friendly interface for non-technical users.

### Phase 4: Deploy publicly
Host the backend and web UI using a platform such as:
- Google Cloud Run
- App Engine
- or a lightweight managed web host

Then configure secure access to the Google Sheets sources.

---

## Recommended first implementation order
This is the order I would follow for this repo:

1. Refactor current logic into backend-ready functions
2. Create a simple API layer
3. Add overview dashboard
4. Add creator list + filter screen
5. Add wiki preview screen
6. Add VOD mismatch review
7. Add settings screen
8. Build browser tabs and polish UX
9. Deploy to hosted environment

This sequence keeps the risk low and makes the final transition smoother.

---

## Concrete principle for this project
The main job is not to add “random new features.”
The main job is to build a reliable data review and wiki-generation workflow that is easier to use, easier to trust, and easier to access externally.

That means the next product features should all serve these goals:
- better visibility
- easier data review
- faster wiki generation
- clearer settings
- low-friction public access

---

## Final recommendation
The best path is:
- keep the core pipeline
- add a small set of practical features now
- isolate logic from UI
- launch a browser app with tabs
- then move to hosted public access

This lets you grow the tool without losing the work you already built.
