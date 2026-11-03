# MIS demo: internal architecture

This document describes how the code is organised, how data flows through it,
and the role of the public functions. The user guide (in French) is in the
[README](../README.md).

## 1. Principles

- **Static site, no build step.** Plain JavaScript files loaded by the inline
  loader of `index.html` in a fixed order. No bundler, no framework, no server.
- **One namespace.** Every module is an IIFE that reads and extends
  `window.MIS`. Modules never use hidden globals.
- **One shared state.** All mutable state lives in `MIS.state` (database,
  active profile, language, open dialog, filters...).
- **SQLite in the browser.** [sql.js](https://sql.js.org) holds the data; the
  database file is saved in IndexedDB after each transaction.
- **HTML strings with escaping.** Views build HTML strings; every dynamic value
  goes through `esc()`. Event handling is delegated (`data-act`, `data-open`,
  `data-chip` attributes).
- **Demo limits are explicit.** Access control, audit log and electronic
  signature are simulated in the browser. See "Limites" in the README.

## 2. Files and load order

The inline loader in `index.html` (between `<!-- boot:start -->` and
`<!-- boot:end -->`) loads the scripts below one after another. The browser
runs that loader only if its sha256 hash matches the Content-Security-Policy
(`script-src 'self' 'sha256-...'`), so `index.html` is the root of trust. Over
http(s) the loader checks each file with Subresource Integrity (sha384). After
any change to a `.js` file or to the loader, run `python3 tools/update-sri.py`.

| # | File | Responsibility |
|---|------|----------------|
| 1 | `vendor/sql-wasm.js`, `vendor/jspdf*.js` | Third-party libraries (vendored) |
| 2 | `js/i18n/{fr,en,es,de}.js` | UI texts, one dictionary per language (`window.I18N`) |
| 3 | `js/seed.js` | SQLite schema and fictitious demo data (`window.MIS_SEED`) |
| 4 | `js/core/util.js` | Creates `window.MIS` and `MIS.state`; DOM, escaping, dates, SHA-256 |
| 5 | `js/core/i18n.js` | `t()`, `tx()`, date and number formatting, language choice |
| 6 | `js/core/rights.js` | Roles, permissions, screens per role, `can()`, `canSee()`, `maskAuth()` |
| 7 | `js/core/db.js` | Query helpers, `transact()`, IndexedDB persistence, `freshDb()` |
| 8 | `js/core/journal.js` | Append-only, hash-chained audit log |
| 9 | `js/core/rules.js` | Airworthiness rules: dues, ADs, aircraft status, LLP, Form 1, ids |
| 9c | `js/chat/kb.js`, `js/chat/engine.js` | Assistant: validated answers in 4 languages (`window.MIS_KB`) and keyword matching (`MIS.chatEngine`) |
| 9b | `js/core/session.js` | Sign-in and signature checks with the personal code (PBKDF2, persistent lock) |
| 10 | `js/ui/components.js` | HTML components, tables, forms, dialog, toast, `safe()`, `deny()` |
| 11 | `js/ui/views.js` | One function per screen (`MIS.VIEWS`) |
| 12 | `js/ui/sheets.js` | Record dialogs: aircraft, work order, part, finding, CRS |
| 13 | `js/ui/sign.js` | Simulated electronic signature |
| 13b | `js/ui/login.js` | Sign-in screen and profile switch dialog |
| 13c | `js/ui/chat.js` | Assistant button and panel (`renderChat`, `bindChat`) |
| 14 | `js/actions/workorders.js` | Work orders, task cards, part installation, CRS |
| 15 | `js/actions/stock.js` | Reception, Form 1 release from quarantine, purchase orders |
| 16 | `js/actions/quality.js` | Findings, audits, documents, modifications |
| 17 | `js/actions/admin.js` | Users and roles, database download and reset, log tools |
| 18 | `js/export/csv.js` | Download helper and CSV export |
| 19 | `js/export/pdf.js` | PDF exports: table, CRS, record sheets |
| 20 | `js/main.js` | Rendering, routing, event binding, start-up |

Dependencies only point "up" the table, with three late-bound calls resolved
at run time: `MIS.render` (main), `MIS.showRecord` (sheets) and `MIS.download`
(csv).

## 3. Data flow

### Start-up

```
inline loader ── loads every script ──> main.js start()
  loadSqlJs()        WebAssembly over http(s), asm.js for file:// or after 8 s
  openDatabase()     saved file from IndexedDB if schema "6", else freshDb() + seed
  state.me = null    every page load starts signed out
  selfTestSha()      checks sha256() against WebCrypto
  bind(); render()   sign-in screen until signIn() succeeds
```

### Display

```
URL hash (#fleet) ─> route() ─> canSee()? ─ yes ─> MIS.VIEWS.fleet() ─> #main
                                         └─ no ──> denied view + one "denied" log entry
```

`render()` also redraws the header (language, profile, compliance pill) and the
side menu. Views call `table(spec)`, which records the table in
`state.exportSpec`; the CSV and PDF buttons export exactly that table.

### User action

```
click [data-act="crs"] ─> MIS.ACTIONS.crs(id)
  1. can("crs.issue")?          no ─> deny(): log "denied" + toast
  2. business checks            (status, separation of duties, AOG)
  3. sign(...)                  simulated signature, failure logged
  4. safe(() => transact(...))  all writes + log entry in ONE transaction
       success: toast, render(), refresh of the open dialog
       error:   rollback, error toast, nothing written
```

`transact()` saves the database to IndexedDB after each commit.

### Credentials

Each profile has a random 12-character personal code (about 60 bits). Codes
are handed to presenters separately and are never committed or published.
`users.auth_hash` holds `pbkdf2-sha256$100000$<salt>$<hash>`
(PBKDF2-HMAC-SHA256, random 16-byte salt). `verifySecret()` uses WebCrypto,
with a pure JavaScript fallback, and compares in constant time. Typed codes
are normalised (upper case, spaces and dashes removed). The same code is
asked to sign in, to switch profile and to sign.

Every failure is logged (`login_fail`, `sign_fail`). The lock is computed from
the audit log, so a page reload does not reset it: 5 failures of one profile
within 10 minutes (since its last successful sign-in) lock that profile, for
sign-in and signature, until 5 minutes after the last failure; 20 failed
sign-ins of all profiles within 10 minutes lock every sign-in the same way.
Limit: clearing site data, another browser or editing the code bypasses it,
and the hashes on the workstation can be attacked offline; production needs
server-side authentication and rate limiting. A CRS freezes a non-secret
credential identifier (`MIS_SEED.credentialId`), never the code.

### Assistant

The site stays static, so the assistant generates nothing and calls no
service. `MIS.chatEngine.match(text)` folds the text (lower case, no accents,
no stop words) and compares its words with the keywords and questions of the
20 entries of `window.MIS_KB`, in the 4 languages. Words match when they share
a beginning of at least 5 letters and 55 % of the longer word. The result is
`answer` (one entry wins on matched words, then on the share of its words
matched), `clarify` (a single vague word, or an exact tie: up to 3 questions
are offered) or `none`. Typing an entry's exact question always answers it.
`renderChat()` runs after every `render()`; the panel keeps the typed text and
focus. The conversation and votes live in `state.chat` only: nothing is
logged, stored or sent, and they are reset on sign-out or profile change.
Screen links are shown only when `canSee(screen)` is true.

### Audit log

Each entry stores `prev` (hash of the previous entry, 64 zeros for the first)
and `h = SHA-256(prev | ts | uid | role | action | msg | params)`. SQL triggers
forbid `UPDATE` and `DELETE` on the table. `verifyLog()` recomputes the chain;
the head hash is shown on the audit log screen and appended to its exports.
The admin reset copies the existing log unchanged into the new database.
Limit: in a browser, a user with developer tools can drop the triggers and
recompute the whole chain; only the head hash kept outside the workstation
reveals it. A tamper-proof log needs a server (sealed log, server-side key and
time source).

## 4. Shared state (`MIS.state`)

| Field | Content |
|-------|---------|
| `SQL`, `db` | sql.js module and current database |
| `me` | Signed-in profile (row of `users`), `null` before sign-in |
| `lang` | UI language code |
| `exportSpec` | Table on screen, used by the exports |
| `chat` | Assistant: `open`, `owner` (profile id), `history`, `votes` (memory only) |
| `current` | `"type:id"` of the open dialog, refreshed after an action |
| `filters` | Filter chips and search text |
| `shaOk`, `saveState`, `lastDenied` | SHA self-test, persistence indicator, last logged denial |

## 5. Public functions (`window.MIS`)

**Core**

| Function | Role |
|----------|------|
| `q(sql, params)`, `one(...)`, `run(...)` | Query all rows, first row, or execute |
| `transact(fn)` | Atomic write: commit and persist, or roll back and re-throw |
| `freshDb(keepLog?)` | New database with demo data, optionally keeping the log |
| `addLog(uid, action, msg, params, ts?)`, `log(...)`, `logNow(...)` | Append audit entries |
| `verifyLog()` | `true` when the hash chain is intact |
| `t(key, params)`, `tx(value)` | Translate a key, or a data value starting with `@` |
| `fD`, `fTs`, `fH`, `fN` | Format a date, timestamp, hours, number |
| `can(perm)`, `canSee(screen)` | Permission checks for the active profile |
| `signIn(uid, typed)`, `checkMySecret(typed)` | Sign-in and signature checks (async, PBKDF2, persistent lock) |
| `lockRemaining(uid, forSignIn)` | Seconds before the profile may try again (0 if not locked) |
| `verifySecret(stored, typed)` | Compares a typed secret with a stored PBKDF2 hash |
| `maskAuth(auth)` | Fixed mask: personal codes are never displayed |
| `taskRows(reg?)`, `adRows(reg?)` | Programme tasks and ADs with due status |
| `acStatus(aircraft)` | `aog`, `overdue`, `soon` or `airworthy`, with details |
| `llp(part)`, `isInstallable(part)` | Life-limit status, installation check |
| `form1Check(ref, org, date)` | Form 1 validation (format, issuer, date, uniqueness) |
| `nextId(table, prefix, width)` | Next yearly sequence id, e.g. `WO-2026-0426` |

**User interface**

| Function | Role |
|----------|------|
| `table(spec)`, `tableNoExport(spec)` | Table HTML; the first one becomes the export |
| `pageHead`, `pill`, `kv`, `list`, `chips`, `field`, `select` | HTML components; `kv()` escapes values unless wrapped with `html()` |
| `openDlg`, `closeDlg`, `formDlg` | Modal dialog and generic form dialog |
| `toast(message, bad?)` | Transient message |
| `safe(fn, okKey?, params?)` | Runs a write action, reports the result, refreshes the screen |
| `deny(perm)` | Logs and reports a refused action |
| `showRecord(ref)`, `openRecord(ref)` | Opens a record dialog from `"type:id"` |
| `sign(purposeKey, params, onOk)` | Simulated signature dialog |
| `render()` | Redraws the whole page |

**Registries**

- `MIS.VIEWS[screen]()` returns the HTML of a screen.
- `MIS.ACTIONS[name](id)` handles a click on `[data-act=name][data-id=id]`.

## 6. Adding a feature

1. **Screen:** add `V.myScreen` in `js/ui/views.js`, declare it with its roles
   in `SCREENS` (`js/core/rights.js`) and add `nav.myScreen` to the 4
   language files.
2. **Action:** write a handler in the matching `js/actions/*.js` file: check
   `can()`, validate, then `safe(() => transact(() => { ...; log(...); }), "toast.key")`,
   and register it in `MIS.ACTIONS`.
3. **Texts:** add every new key to `fr.js`, `en.js`, `es.js` and `de.js`.
4. **Schema change:** update `js/seed.js` and the schema version (`meta.schema`
   and `SCHEMA_VERSION` in `js/main.js`), so old saved databases are replaced.
5. Run `python3 tools/update-sri.py`, then test over http and file://, and update
   the functional test plan (`docs/TESTS-FONCTIONNELS.md`, in French) when a
   user-visible behaviour changes.

## 7. Conventions

- Code comments, identifiers and this document are in English; the UI texts
  are translated in `js/i18n`.
- JSDoc header (`@file`) on every module, one-line description on every
  function whose name is not self-explanatory.
- Functions stay short: complex screens and actions are split into helpers
  (data collection, HTML sections, validation, database write).
- Every write goes through `transact()` and writes an audit log entry.
