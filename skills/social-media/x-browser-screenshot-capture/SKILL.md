---
name: x-browser-screenshot-capture
description: Capture readable screenshots of X/Twitter posts or articles in the browser tool, including workarounds for blank-white screenshots and blurry full-page captures.
triggers:
  - User asks for a screenshot of an X/Twitter post, thread, or article
  - Browser screenshot output for X looks blank white or empty
  - Screenshot is valid but too blurry to read
---

# X/Twitter browser screenshot capture

Use this when the user wants a screenshot of X content and the first browser screenshot is blank, blocked, or too blurry.

## Why this skill exists

X often renders partially in the browser tool:
- the initial status URL may show login/signup gating or cookie banners
- a normal screenshot can come out blank white even when the DOM has content
- a full-page screenshot can be technically correct but too zoomed out to read in chat

This workflow gets to a readable screenshot and verifies it before sending.

## Workflow

1. Open the status URL with `browser_navigate`.
2. If the page shows cookies, dismiss them (usually `Refuse non-essential cookies` works).
3. Refresh state with `browser_snapshot(full=true)` or `browser_console()`.
4. If the tweet/article content is present in the accessibility tree, look for:
   - `Focus mode`
   - `/article/...` links
   - author handle, body text, and media links
5. If the status page is awkward or partially gated, navigate directly to the article URL:
   - `https://x.com/<handle>/article/<status_id>`
   This often renders better than the raw `/status/` page.
6. Before sending any image, call `browser_vision()` and explicitly ask whether the screenshot contains the expected X article/post content and is not a blank white page.
7. If the screenshot is readable, send it.
8. If the user says it is blurry, increase zoom before taking another screenshot:
   - use `browser_console()` with JS like `document.body.style.zoom='200%'`
   - then call `browser_vision()` again to produce a tighter, more readable screenshot
9. Prefer the zoomed-in article/body view over a full-page view when the goal is readability in chat.

## Useful checks

### Check whether content exists even if snapshot looks empty
Use `browser_console()`:
- inspect `document.title`
- inspect `document.body.innerText.slice(0, 500)`
- inspect anchors for `/article/` URLs

Example JS patterns:
- `({href:location.href,title:document.title,ready:document.readyState,body:document.body?.innerText.slice(0,500)})`
- `Array.from(document.querySelectorAll('a')).map(a => ({text:a.innerText.trim(), href:a.href})).filter(x => x.href.includes('/article/')).slice(0,10)`

These confirm that the page has loaded meaningful content even if the compact snapshot is sparse.

## Failure modes and responses

### Blank white screenshot
Symptoms:
- screenshot file exists but is almost pure white
- vision says the image is blank or nearly blank

Response:
- do not send it as if it were good
- navigate again or switch from `/status/` to `/article/`
- verify with `browser_vision()` before sending

### Snapshot says `Empty page` but content is actually present
Response:
- use `browser_console()` to inspect DOM text/title/links
- continue if body text clearly contains the post/article

### Screenshot is correct but blurry
Response:
- zoom page to 200% (or higher if needed)
- re-capture with `browser_vision()`
- if still blurry, make segmented screenshots or crop to the main content column

### Zoomed recapture regresses to blank/white or stops scrolling reliably
This happened in practice after a valid X article screenshot was obtained.

Response:
1. Keep the last known-good screenshot path from `browser_vision()`.
2. If that screenshot is tall/high-resolution but still too small to read in chat, segment that already-validated image offline instead of relying on more browser captures.
3. On macOS, prefer an AppKit/Swift crop helper over `sips` for exact y-offset crops. `sips -c` is fine for simple crops, but its offset behavior is awkward for repeatable top/middle/bottom slicing.
4. Verify each cropped segment with `vision_analyze()` before sending.
5. If the crop order is confusing, rename outputs to match reading order only after verification.

Example macOS crop helper:
```bash
cat >/tmp/crop.swift <<'SWIFT'
import Foundation
import AppKit

let args = CommandLine.arguments
if args.count != 8 {
    fputs("usage: crop.swift input output x y width height scale\n", stderr)
    exit(1)
}
let input = args[1]
let output = args[2]
let x = CGFloat(Double(args[3])!)
let y = CGFloat(Double(args[4])!)
let width = CGFloat(Double(args[5])!)
let height = CGFloat(Double(args[6])!)
let scale = CGFloat(Double(args[7])!)

guard let img = NSImage(contentsOfFile: input) else { fatalError("load fail") }
var rect = NSRect(origin: .zero, size: img.size)
guard let cg = img.cgImage(forProposedRect: &rect, context: nil, hints: nil) else { fatalError("cg fail") }
let imgH = CGFloat(cg.height)
let cropRect = CGRect(x: x, y: imgH - y - height, width: width, height: height)
guard let cropped = cg.cropping(to: cropRect) else { fatalError("crop fail") }
let rep = NSBitmapImageRep(cgImage: cropped)
rep.size = NSSize(width: width*scale, height: height*scale)
guard let data = rep.representation(using: .png, properties: [:]) else { fatalError("png fail") }
try data.write(to: URL(fileURLWithPath: output))
print("wrote", output)
SWIFT
```

Then create sequential slices, for example from a 1980px-wide tall screenshot:
```bash
swift /tmp/crop.swift input.png part1.png 0 0    1980 2400 1
swift /tmp/crop.swift input.png part2.png 0 2200 1980 2400 1
swift /tmp/crop.swift input.png part3.png 0 4400 1980 2400 1
swift /tmp/crop.swift input.png part4.png 0 6600 1980 2498 1
```

Then verify which part is top/middle/bottom with `vision_analyze()` before delivery.

## Verification rule

Never send an X screenshot without verifying one of these first:
- `browser_vision()` confirms the screenshot contains the expected content and is not blank
- OR DOM inspection plus a fresh validated screenshot confirms the article/post body is visible

## Login/home-feed specific failure mode (new)

When the user asks for screenshots from the X **home recommendations feed** rather than a specific public post/article, there is an extra risk: the browser tool session may not have a logged-in X session, and it cannot reuse the user's already-signed-in local browser automatically.

### Key lesson
A remote/browser-tool session is its own browser context.
Even if the user says "I'm already logged in with Google in my browser", that does **not** mean the browser tool inherits that Google or X session.

### What to check
Use `browser_console()` on `https://x.com/` and `https://x.com/i/flow/login`.
If you see signals like:
- homepage shows only `Happening now / Join today / Sign in`
- login flow shows `Something went wrong. Try reloading.`
- no username/password inputs are present
- console shows errors around `https://api.x.com/1.1/onboarding/task.json?flow_name=login`

then the blocker is the login flow itself, not missing clicks.

### Important interpretation
If the browser console shows errors like:
- `Access to XMLHttpRequest at 'https://api.x.com/1.1/onboarding/task.json?flow_name=login' ... blocked by CORS policy`
- `Failed to load resource: net::ERR_FAILED`

that means the X login onboarding API is failing in this environment. In that state:
- you cannot reliably proceed to the email/password form
- you cannot rely on Google sign-in chooser appearing
- retrying the same login page usually does not help much

### Response strategy
1. Verify the failure with `browser_console()` and/or `browser_vision()`.
2. Explain clearly that the remote browser is not reusing the user's local Google/X session.
3. Do **not** pretend login is one or two clicks away if the login form never loads.
4. Offer alternatives:
   - user provides direct tweet URLs to capture one by one
   - use a public profile or article URL instead of the home feed
   - retry later if X's login flow is temporarily broken in this environment

## Local real-browser capture pitfall (new)

If you switch from the browser tool to the user's real local Chrome session and try to generate tweet images from DOM data, do **not** confuse a DOM reconstruction with a true screenshot.

### Failure pattern
A tempting workaround is:
1. use AppleScript/Chrome JS to read `article` elements from the real `x.com/home` tab
2. clone the DOM subtree
3. render it through SVG `foreignObject` and/or canvas
4. export PNGs

This can preserve text while silently losing important visual fidelity:
- native X styling only partially survives
- CSS variables, pseudo-elements, masks, icons, and dynamic media often break
- avatars/images/videos may degrade into placeholders or blank white boxes
- the final image can look mostly white even though the tweet text is present

### Rule
If the user wants a screenshot of the real browser page, a DOM-reconstructed image is **not** good enough. Treat it as an extraction/debug artifact, not deliverable output.

### What to do instead
- Prefer true pixel capture from the real browser window/screen.
- Verify the output visually before sending.
- If the screenshot looks structurally correct but visually washed out/white, assume the reconstruction path is at fault before blaming the page.

## macOS system screenshot pitfall (new)

Even when AppleScript confirms Chrome is on `https://x.com/home` and page JS can read live tweets, `screencapture` may still fail to capture the actual visible browser pixels.

### Symptoms
- `tell application "Google Chrome"` reports the correct URL/title/window bounds
- page JavaScript sees `article` nodes and tweet text
- but `screencapture` returns a pure-color/empty/wrong image instead of the Chrome window
- window-id capture may fail with `could not create image from window`

### Interpretation
This usually means the blocker is at the macOS display/screen-capture layer, not the X page itself. Common causes:
- Screen Recording permission is missing for the terminal/Hermes/Python host process
- the automation process is not attached to the same active GUI session the user is viewing
- window-server capture is otherwise restricted

### New macOS input-injection pitfall
When trying to switch from JS scrolling to **real user-like input** (CGEvent mouse wheel, click, PageDown) in the user's local Chrome, the real blocker may be the host process identity, not the X page.

Observed failure pattern:
- JS `window.scrollBy(...)` changes `scrollY`, but does not show the loading behavior the user sees during manual scrolling
- CGEvent-based wheel / click / PageDown events do **not** change `scrollY`
- page-side checks show `document.hasFocus() === false` even after `tell application "Google Chrome" to activate`
- a click counter injected into the page stays at 0, proving the synthetic click never landed in the page
- `AXIsProcessTrustedWithOptions(...)` returns `false`

Key lesson:
- On macOS, Accessibility / input permission is granted to a **specific executable or app identity**.
- The user may have already granted access to Terminal, iTerm, Chrome, or `Python.app`, but Hermes may actually be running under a different host binary.
- In practice, Hermes gateway can run under an unsigned uv/venv Python such as:
  - `~/.hermes/hermes-agent/venv/bin/python`
  - which may resolve to `~/.local/share/uv/python/.../bin/python3.11`
- That unsigned bare executable is not the same client as the signed `Python.app` bundle (`org.python.python`), so the user's existing Accessibility grants may not apply.

What to check:
1. Identify the actual long-lived Hermes/gateway process command line.
2. Resolve symlinks for the executing `python` binary.
3. Check whether that exact binary is signed / app-bundled.
4. Verify `AXIsProcessTrustedWithOptions(...)` from the same host context that is trying to post events.
5. Verify page focus with `document.hasFocus()`.
6. Verify whether synthetic clicks actually land by temporarily adding a page click counter.

Interpretation rule:
- If AX trust is false, `document.hasFocus()` stays false, and synthetic clicks never increment the page counter, do **not** keep blaming X lazy-loading.
- The real blocker is that the current Hermes host process is not trusted to inject input into the real Chrome window.
- Existing grants for `Python.app` may be irrelevant if Hermes is actually running under an unsigned uv/venv Python binary.

### Response strategy
1. Verify separately:
   - browser state via AppleScript (`URL`, `title`, window `bounds`)
   - page content via JS (`document.querySelectorAll('article')`, `innerText`)
   - screenshot output via `vision_analyze()`
2. If browser state is correct but screenshots are wrong, stop treating it as an X-render bug.
3. Tell the user the screenshot channel itself is blocked/failing.
4. Ask the user to enable/check macOS Screen Recording for the relevant host app(s) before retrying.

## Practical notes from experience

- X content may be accessible through the article view even when the status view is annoying.
- Cookie dismissal can materially change render success.
- A valid screenshot may still be poor for messaging apps because the text is too small; zoomed screenshots are usually better than full-page captures.
- `browser_vision()` is the fastest way to catch white/blank captures before the user does.
- The browser tool does not inherit the user's local Google/X login session.
- If X login shows only `Something went wrong. Try reloading.` plus onboarding API/CORS failures, switch from "try to log in" to an alternate capture plan.

## Public post-detail capture limitation for replies (new)

For logged-out/public X post detail pages in the browser tool, there is an important split:
- the main post header usually renders well enough to capture
- actual replies often do **not** render inline, even when the DOM shows a `Read N replies` button

### What happens
On a public post detail URL, the browser tool can often capture:
- author avatar/name/handle
- post text/media
- timestamp, views, and engagement row

But when trying to reveal replies:
- clicking `Read N replies` may open a login/signup dialog instead of loading replies
- a large bottom signup banner (`Don’t miss what’s happening`) may obscure the lower part of the post
- the accessibility tree can still mention the main post while no visible replies appear in the screenshot

### Practical rule
If the user wants `author info + main post + some replies` and you are on a logged-out/public browser-tool page:
1. First capture a clean author-visible top screenshot of the main post.
2. Verify with `browser_vision()` that author info and main content are truly readable.
3. Do **not** assume `Read replies` will expose reply content; verify after clicking.
4. If clicking `Read replies` triggers a login gate/dialog, treat reply capture in the browser tool as blocked.
5. In that state, do not promise a better reply-rich recapture from the browser tool; either:
   - fall back to a real local logged-in browser path, or
   - send the last known-good readable set and clearly explain the limitation.

## Local real-browser recapture regression rule (new)

When using the real local Chrome/window-capture path, a previously working capture pipeline can regress and start producing black images again.

### Important rule
If a new recapture attempt produces black/empty images:
- verify with vision before sending anything
- do **not** send the black outputs just because they are newer
- keep the last known-good readable screenshot set as the fallback deliverable
- tell the user you are reusing the readable set while the improved recapture path is currently regressed

This is especially important when the user asked for a refinement (for example, `show more complete author header` or `make comment-heavy posts taller`). A failed refinement pass should not replace a readable baseline with broken black captures.

## Local macOS Chrome capture fallback (new)

When the user insists they are already logged in in their real local Chrome, the browser tool may still be useless because it runs in a separate browser context. In that case, fall back to the **real local Chrome window** on macOS.

### Key lesson
Do not rely on `screencapture -R ...` alone.
In practice it can capture the wrong Space, a blank/solid-color frame, or another app even when AppleScript says Chrome is frontmost.

Also, do not assume that switching Hermes/local automation from one Python runtime to another will fix real-input problems by itself. In practice, moving from an unsigned uv-managed Python 3.11 runtime to a signed Python 3.13 runtime and even to `Python.app` still did **not** make CGEvent click/scroll input reach the live Chrome page.

### More reliable approach
1. Use AppleScript to inspect Chrome windows/tabs and activate the right tab.
   - Enumerate windows and tabs.
   - Pick the tab whose URL/title is `x.com/home` or the needed X page.
   - Bring that tab/window forward and set explicit bounds.
2. Use CoreGraphics window enumeration to find the actual onscreen Chrome window.
   - `CGWindowListCopyWindowInfo([.optionAll], ...)`
   - Filter for `owner == "Google Chrome"` and `onscreen == 1`
   - Prefer the window whose title is `Home / X` or `x.com/home`
3. Capture the window with `CGWindowListCreateImage(.optionIncludingWindow, windowID, ...)` instead of normal `screencapture`.
   - This produced a correct Chrome/X window image in practice when `screencapture` returned nonsense.
4. Only after the full window capture is validated should you crop individual tweets.

### New failure mode: signed Python host still cannot deliver real input

A tempting hypothesis is that failed local Chrome scrolling/clicking is caused solely by Hermes running under an **unsigned** Python interpreter.
In practice, that was tested and found insufficient:
- current gateway host: uv-managed Python 3.11 binary with no code signature
- alternate test host: signed Python 3.13
- alternate app-bundle host: `Python.app`

Observed result in all three cases:
- `tell application "Google Chrome" to activate` succeeded
- the correct `x.com/home` tab remained frontmost
- but `document.hasFocus()` stayed `false`
- page-level click counters stayed at `0`
- injected CGEvent mouse clicks / wheel scrolls / PageDown-style inputs did not change `scrollY`

### Interpretation
If signed and unsigned Python hosts both fail the same way, the blocker is likely **not** just the interpreter signature.
Instead suspect one of:
- wrong macOS GUI/input session
- page/tab not receiving true focus despite window activation
- TCC / Input Monitoring / Accessibility state above the Python runtime level
- event injection reaching the OS but not the live Chrome document

### Practical rule
If you already tested a signed Python host and still see:
- `document.hasFocus() === false`
- click listeners never fire
- wheel/key events do not move the page

then stop treating "switch Python runtime" as the main fix. Investigate focus/session/input-routing instead.

### Suggested macOS helper pattern
Use a small Swift helper for capture:
```swift
import Foundation
import CoreGraphics
import AppKit

let wid = CGWindowID(UInt32(CommandLine.arguments[1])!)
let out = CommandLine.arguments[2]
let image = CGWindowListCreateImage(.null, .optionIncludingWindow, wid, [.boundsIgnoreFraming, .bestResolution])
let rep = NSBitmapImageRep(cgImage: image!)
let data = rep.representation(using: .png, properties: [:])!
try data.write(to: URL(fileURLWithPath: out))
```

And another helper to enumerate windows:
```swift
import Foundation
import CoreGraphics

let info = CGWindowListCopyWindowInfo([.optionAll], kCGNullWindowID) as? [[String: Any]] ?? []
for w in info {
    let owner = w[kCGWindowOwnerName as String] as? String ?? ""
    let name = w[kCGWindowName as String] as? String ?? ""
    let onscreen = w[kCGWindowIsOnscreen as String] as? Int ?? -1
    if owner == "Google Chrome" && onscreen == 1 {
        print(owner, name)
    }
}
```

### Verification rule for local capture
Before sending anything to the user:
- run image verification (`vision_analyze()` or equivalent) on the captured full window
- confirm the image really shows Chrome + `x.com/home`
- only then crop tweet cards

## X home timeline lazy-load failure mode (new)

On a logged-in local `x.com/home` page, the DOM may expose only a handful of `article` nodes even after large scrolls.

### Observed symptoms
- `document.querySelectorAll('article').length` stayed fixed at `4`
- `window.scrollY` increased to thousands of pixels
- clicking `See new posts` did not increase the article count
- the page still showed real tweet text, but no new tweet cards entered the DOM

### Interpretation
This is likely a home-timeline lazy-load / virtualization failure in the current automation context, not simply "you forgot to scroll far enough".

### Response strategy
- Treat this as a real blocker, not user error.
- Report the measured facts: current article count, current `scrollY`, whether `See new posts` changed anything.
- If the user still wants output immediately, offer to capture the currently available tweets first.
- If completeness matters, refresh/re-seat the timeline and re-verify before promising 9 tweets.

### Stronger proof when the user disputes "you really reached the bottom"
A plain screenshot is often not persuasive enough because:
- the macOS/Chrome scrollbar may auto-hide
- the visible feed can still look like a normal mid-page view even when the document is at max scroll
- the user may reasonably suspect the wrong scroll container was moved

When that happens, verify the real scroll container and produce a combined evidence artifact.

#### Verification steps
1. In the live local Chrome tab, inspect the actual scroller with JS:
   - `const root = document.scrollingElement || document.documentElement`
   - capture `window.scrollY`, `root.scrollHeight`, `root.clientHeight`, and `document.querySelectorAll('article').length`
2. Compute max scroll as:
   - `max = root.scrollHeight - root.clientHeight`
3. If `window.scrollY === max`, treat that as evidence that the page document itself is already at maximum scroll.
4. Also record what the real scroller is (`root.tagName`, usually `HTML`) so you can answer "did you scroll the wrong element?" directly.

#### Better user-facing proof artifact
If the last recorded frame still does not visibly prove the bottom state, build a side-by-side annotated image:
- left: the last known-good screenshot/frame of the real `x.com/home` view
- right: a large text panel containing live DOM metrics from the current tab, including:
  - URL
  - real scroll container (`HTML / document.scrollingElement` or similar)
  - `scrollY`
  - `max`
  - document height / viewport height
  - current article count
- add a short conclusion box such as:
  - `scrollY == max, so the page is already at its maximum scroll position`
  - `the problem is not "didn't reach bottom"; it is "reached bottom but only 5 articles loaded"`

This works better than relying on a visible scrollbar because it answers the exact objection with live measurements from the real tab.

#### Important lesson
If `scrollY == max` but `article` count is still fixed (for example 5), do not keep arguing from screenshots alone. At that point the debugging target shifts from scrolling mechanics to:
- lazy-load failure
- virtualization stall
- feed/network/request errors near the bottom of the home timeline

### New fallback when local home-feed capture is unstable
If the real local `x.com/home` timeline only exposes a few posts (for example 4 or 5) and refuses to lazy-load more, but the DOM still contains the individual post/status links, switch delivery strategy:
1. Extract the visible `/status/` URLs from the live home tab DOM.
2. Open each status URL individually in the browser tool.
3. Dismiss cookies if needed.
4. Use `browser_snapshot(full=true)` to confirm the post body is present even if the page also shows `Something went wrong. Try reloading.` lower on the page.
5. Use `browser_vision()` to generate a validated readable screenshot of the post detail page.
6. Deliver those validated screenshots instead of insisting on one more unstable local-window crop pass.

This is useful because:
- the home feed may freeze at a fixed `article` count under automation
- local CoreGraphics window capture may regress from working to black/blank frames
- but the individual public status pages can still render well enough in the browser tool for readable evidence screenshots

### Playwright-with-profile-copy pitfall (new)
A tempting "different way" is to copy the local Chrome profile and launch it under Playwright.
In practice this may still fail to reuse the user's signed-in X session:
- launching Chrome/Chromium with a copied `Profile 1` and `Local State` can still redirect `https://x.com/home` to `https://x.com/i/flow/login?redirect_after_login=%2Fhome`
- the copied profile may not carry over a usable live session in automation
- so this is not a guaranteed fix for local-home-feed capture

Rule:
- treat Playwright + copied local profile as an experiment, not a dependable way to inherit the user's live logged-in X session
- if it lands on the login flow, report that fact quickly and fall back to either the live local Chrome window or individual public status pages
- the home feed may freeze at a fixed `article` count under automation
- local CoreGraphics window capture may regress from working to black/blank frames
- but the individual public status pages can still render well enough in the browser tool for readable evidence screenshots

If fidelity to the exact home-feed view matters more than immediate delivery, prefer waiting for the live home page to recover instead of substituting detail pages.

## macOS real-Chrome capture lessons (new)

When the user insists they are already logged in locally and the browser tool cannot reuse that session, a fallback is to drive the **real local Chrome** with AppleScript and capture the actual window pixels from WindowServer.

### Key lessons

1. `screencapture` is not always trustworthy for this workflow.
   - It may return the wrong Space/desktop contents.
   - It may capture a different frontmost app even after `activate`.
   - Cropping from a full-screen shot can produce unrelated imagery even though AppleScript reports the right Chrome URL/tab.

2. Prefer `CGWindowListCreateImage` for the exact Chrome window.
   - Enumerate windows with CoreGraphics (`CGWindowListCopyWindowInfo`).
   - Find the on-screen Chrome window whose title is `Home / X` or `x.com/home`.
   - Capture that specific `windowID` with `CGWindowListCreateImage(... optionIncludingWindow ...)`.
   - This worked reliably when `screencapture` produced wrong or abstract/blank content.

3. Multiple Chrome windows/tabs matter.
   - The correct X page may be a non-active tab in a window that also contains unrelated tabs.
   - Another Chrome window (for example a blank new-tab window) can become the visible on-screen window and trick the capture pipeline.
   - Before capture, explicitly:
     - enumerate all Chrome windows and tabs
     - switch to the target tab by index
     - raise that window to the front
     - close or ignore decoy windows like `chrome://newtab/`

4. Verify with both DOM and image checks.
   - DOM/AppleScript can say the active tab is `https://x.com/home` while the captured image is still the wrong window or a blank page.
   - Always validate the captured PNG with vision before sending it.

5. For cropping individual posts from a real Chrome window:
   - read `window.devicePixelRatio`, `innerWidth`, `innerHeight`
   - get each `article.getBoundingClientRect()`
   - compute browser chrome height as `(captured_window_pixel_height / dpr) - innerHeight`
   - convert DOM coordinates to image pixels using `dpr`
   - add a small margin around the card before cropping

### New failure mode: X home timeline instability in real Chrome automation

Even with a valid logged-in local Chrome session, `x.com/home` may become unstable under automation:
- the timeline may briefly show a few posts, then stop at only 4 `article` nodes
- scrolling may increase `scrollY` without loading more posts
- after reload, the tab may still be `x.com/home` but the main timeline can regress to 0 `article` nodes or a mostly blank center column

Interpretation:
- this is no longer a login/session-discovery problem
- it is a timeline-render/loading instability in the live X page under automation

Response:
1. Distinguish clearly between:
   - wrong window capture
   - correct window capture but blank X content
   - correct X content but only a small fixed set of posts loaded
2. Do not promise a full 9-post capture if the live page only exposes 4 posts before regressing.
3. Ask the user to manually refresh the already-correct Chrome window and confirm the timeline is visibly loaded before resuming capture.
4. Once the correct window is confirmed, continue from that window instead of re-solving window discovery again.

### New lesson: local real-input gating can be the blocker, not X itself

A major failure mode on macOS is that the local Chrome tab is readable via AppleScript/JS, but **real user-like input still does not reach it**.
Symptoms observed in practice:
- `document.hasFocus()` is `false`
- `document.visibilityState` is `hidden`
- CGEvent click/wheel injections do nothing
- PageDown does nothing
- X stays stuck around 4–5 `article` nodes

What to check first:
1. `AXIsProcessTrustedWithOptions(...)` for the actual host process that is sending events.
2. In-page focus state:
   - `document.hasFocus()`
   - `document.visibilityState`
3. Whether a real key event changes `scrollY`.

Important interpretation:
- If `hasFocus=false` and `visibilityState='hidden'`, do **not** blame X home-feed lazy loading yet.
- The real blocker may be the macOS input/Accessibility chain.

Practical recovery rule:
- After Accessibility permission is fixed, re-test with a **real PageDown** event first.
- In practice, PageDown was the signal that proved the chain was repaired:
  - before fix: `scrollY` stayed `0`, `articleCount` stayed `5`
  - after fix: `focus=true`, `visibility='visible'`, PageDown increased `scrollY` and `articleCount` rose from `5` to `8` to `10`

### New lesson: real keyboard paging may work before synthetic click/wheel does

Once local permissions/focus improved, the most reliable way to grow the X home timeline was not JS `scrollBy`, but repeated **real PageDown** events.
Observed behavior:
- synthetic click counters could still remain `0`
- synthetic wheel scrolling could still be inconsistent
- but PageDown reliably advanced the feed and triggered more `article` nodes

Use this ordering for local X home-feed expansion:
1. Bring Chrome frontmost.
2. Verify `document.hasFocus() === true` and `document.visibilityState === 'visible'`.
3. Reset to top if needed.
4. Send repeated real PageDown events.
5. After each burst, check:
   - `window.scrollY`
   - `document.querySelectorAll('article').length`
   - loading indicators / progress bars
6. Only if PageDown fails should you fall back to JS scrolling for diagnostic purposes.

### Stronger root-cause check: hidden document / wrong GUI foreground session

A very important failure mode appeared in practice: AppleScript could read and execute JS in a real local Chrome `x.com/home` tab, but all attempts to send **real** click / wheel / PageDown input still failed. The page looked readable through JS, yet behaved as if it were not the true frontmost interactive page.

#### Symptoms
- `document.hasFocus()` stays `false`
- `document.visibilityState` stays `"hidden"`
- `window.focus()` does nothing
- click instrumentation such as `window.__clicks` stays at `0` after CGEvent mouse clicks
- CGEvent wheel / PageDown does not change `window.scrollY`
- `NSWorkspace.sharedWorkspace().frontmostApplication()` reports `loginwindow`, not `Google Chrome`
- this can remain true even when:
  - `tell application "Google Chrome" to activate` succeeds
  - Chrome windows/tabs and URLs are readable via AppleScript
  - the process is launched inside `gui/<uid>` via `launchctl bootstrap`

#### Interpretation
This means the automation process is **not actually attached to the same interactive foreground GUI session** as the user's visible desktop Chrome, even if it can inspect Chrome by AppleScript. In this state:
- JS/DOM reads can work
- window capture may partially work
- but true user-like input will not land in the page
- `x.com/home` may report only a few `article` nodes while remaining non-interactive from the automation perspective

#### Required checks
Before assuming X itself is broken, run these checks on the target tab:
- `document.hasFocus()`
- `document.visibilityState`
- optional click counter instrumentation
- frontmost app from AppKit / NSWorkspace

Useful JS probe:
```js
JSON.stringify({
  href: location.href,
  title: document.title,
  hasFocus: document.hasFocus(),
  visibility: document.visibilityState,
  activeTag: document.activeElement && document.activeElement.tagName,
  scrollY: Math.round(window.scrollY),
  articleCount: document.querySelectorAll('article').length
})
```

Useful AppKit probe from a signed local Python / AppKit-capable process:
```python
import AppKit
app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
print(app.localizedName() if app else None, app.bundleIdentifier() if app else None)
```

If that probe returns `loginwindow` instead of Chrome, stop expecting real scroll/click synthesis to work.

#### Response strategy
1. Do not keep retrying CGEvent mouse/scroll/keyboard injection once `visibilityState` is `hidden` and frontmost app resolves to `loginwindow`.
2. Explain clearly that the automation context can read Chrome but is not in the true interactive foreground desktop session.
3. Do not keep promising a "manual-like scroll" path from that context.
4. Fall back to one of:
   - a genuinely foreground user session / terminal launched from the visible desktop
   - non-interactive DOM/network inspection of the already logged-in page
   - a user-assisted local step if exact manual-scroll fidelity is required
5. Treat this as a **GUI session mismatch**, not merely a Chrome-focus bug or an unsigned-Python issue.

#### Important lesson
Switching from an unsigned Python to a signed Python or even `Python.app` may still fail if the deeper problem is the GUI session view itself. Signed-host testing is useful, but if the page remains `hidden` and AppKit still sees `loginwindow` as frontmost, the blocker is higher-level session isolation.

## Real-input permission / focus recovery for local Chrome (new)

When trying to drive the **real local Chrome** with system-level input (wheel, PageDown, click), distinguish these two states:

### State A: input path is blocked
Observed signals:
- `document.hasFocus() === false`
- `document.visibilityState === 'hidden'`
- CGEvent click does not increment a page click counter
- wheel/PageDown leaves `scrollY` unchanged

Interpretation:
- the automation path is not actually reaching the visible interactive page
- before changing capture strategy again, check Accessibility / input permissions first

### State B: input path recovered
After enabling the correct Python 3.11 host in macOS Accessibility, the state changed to:
- `document.hasFocus() === true`
- `document.visibilityState === 'visible'`
- real `PageDown` started working
- home-feed `article` count increased from `5 -> 8 -> 10`
- `scrollY` advanced normally (`0 -> 1816 -> 3632` in one run)

Key lesson:
- if focus/visibility become `true/visible`, retry **real PageDown** before concluding X home lazy-load is broken
- a previous “stuck at 5 articles” diagnosis may have been caused by blocked real-input delivery rather than the feed itself

### Practical verification snippet
On the live tab, verify before attempting a real-scroll capture:
- `document.hasFocus()`
- `document.visibilityState`
- `window.scrollY`
- `document.querySelectorAll('article').length`

If focus is restored, prefer real PageDown over JS-only scrolling for feed loading validation.

## Detail-page capture formatting lesson (new)

When the user asks for **tweet detail screenshots with some comments**, the preferred framing is:
1. top section must include author/header information
2. include the main post body/media/engagement row
3. include some visible replies or follow-up content below
4. for comment-heavy items, make the image taller by stitching an upper crop (header + post) with a lower crop (replies section)

A successful reusable pattern was:
- capture one crop aligned at the top so author info is visible
- scroll downward to expose replies/comments
- capture a second crop of the same content column
- stitch the two crops vertically with a thin separator
- compress to JPEG so the final image remains Telegram-photo-safe

This produced final images that Telegram accepted as photos around `921 x 2560`, while preserving author info plus more reply content.

## macOS real-browser capture pitfall: wrong Chrome window/tab/Space (new)

When using the **real local Chrome** on macOS instead of the remote browser tool, a "blank", wrong-color, or unrelated screenshot may mean you are capturing the wrong visible window/Space — not that X itself failed to render.

### Symptoms
- AppleScript can read Chrome just fine:
  - URL is `https://x.com/home`
  - title is `Home / X`
  - DOM queries return real `article` nodes and tweet text
- but `screencapture` returns:
  - a pure-color frame
  - Telegram or another app
  - unrelated content
  - a crop that clearly is not the X timeline

### Key lesson
On macOS with multiple Chrome windows/tabs/desktops, the desired X tab may exist but still be **offscreen** from WindowServer's point of view.
In practice, the frontmost visible Chrome window can be a different tab/window than the one whose URL you just queried.

### Reliable diagnosis
Prefer checking window visibility at the WindowServer level before trusting a system screenshot.

Use a Swift helper with `CGWindowListCopyWindowInfo` and inspect:
- `kCGWindowOwnerName`
- `kCGWindowName`
- `kCGWindowIsOnscreen`
- bounds

If you see something like:
- Telegram window -> `onscreen=1`
- Chrome `Home / X` window -> `onscreen=-1`

then the screenshot path is targeting the wrong visible Space/window.

### Reliable recovery workflow
1. Enumerate Chrome windows/tabs with AppleScript.
2. Find which window actually contains the `https://x.com/home` tab.
3. Explicitly switch that window's active tab to the X tab.
4. Bring that window to the front (`set index of window N to 1`, `activate`).
5. Resize/reposition it if needed.
6. Re-check `CGWindowListCopyWindowInfo` until the target Chrome window shows as onscreen.
7. Only then run `screencapture -R ...` or other system-level capture.

### AppleScript pattern
```applescript
tell application "Google Chrome"
  set active tab index of window 1 to 5
  set index of window 1 to 1
  set bounds of window 1 to {80, 60, 1500, 980}
  activate
end tell
```

### Verification rule for real-browser capture
Do not assume that successful AppleScript control means the right pixels are visible.
Before cropping/sending, verify at least one of:
- WindowServer reports the target Chrome window as onscreen
- a fresh screenshot visually shows the Chrome window with `x.com/home` and the timeline

### Interpretation
If permissions are already granted but screenshots still show the wrong content, the blocker may be:
- another app still occupying the visible Space
- the target Chrome tab living in a different Chrome window
- the target Chrome window existing but remaining offscreen

In that case, fix window/tab selection first; do not keep debugging CSS or screenshot codecs.
- DOM-reconstructed tweet images from the real browser are not acceptable substitutes for pixel-faithful screenshots.
- On macOS, a correct Chrome tab plus wrong `screencapture` output usually points to Screen Recording / GUI-session issues, not the webpage.

## Stronger proof/debug path: short local screen recording (new)

If the user says "I still don't believe that's what the real browser is showing" or asks to **see the process**, a short local screen recording is more trustworthy than a single still frame.

### Why this helps
In practice, different capture paths can disagree:
- DOM inspection can show valid tweets
- `CGWindowListCreateImage` can sometimes return a black/empty still image for the same Chrome window
- but a short `screencapture -v` desktop recording can still show the real Chrome page correctly

So if still-image capture is disputed, record a short clip of the real desktop while you:
1. bring Chrome to the front
2. switch to the target X tab
3. reload or navigate to `https://x.com/home`
4. stop after a few seconds

### macOS command pattern
Use the built-in recorder:
```bash
mkdir -p /tmp/hermes_video_demo
screencapture -D1 -v -V12 -k /tmp/hermes_video_demo/x_demo.mov
```

Then, while recording is running, drive Chrome with AppleScript:
```applescript
tell application "Google Chrome"
  set index of window 1 to 1
  set active tab index of window 1 to 5
  activate
  tell active tab of window 1 to reload
end tell
```

### How to verify the recording
Before sending it, extract a few frames and inspect them:
```bash
ffmpeg -y -i /tmp/hermes_video_demo/x_demo.mov \
  -vf "select='eq(n,60)+eq(n,240)+eq(n,420)',scale=1280:-2" \
  -vsync 0 /tmp/hermes_video_demo/frame_%02d.png
```

Check at least:
- an early frame to prove Chrome is on `x.com/home`
- a later frame to see whether the page stayed normal or regressed to black/blank

### Important lesson
A screen recording may show the page correctly even when a window-still capture path is black.
So when proving what the real local browser showed, prefer:
- desktop video evidence
- then extracted frames for analysis
- and only after that rely on window-still crops

### Playback / delivery lesson
If the user wants a "show me what you did" artifact, record the desktop in a way that makes the motion obvious:
1. keep Chrome frontmost
2. hold each visible post for about 3 seconds
3. scroll to the next post
4. keep the clip short (around 12–16 seconds)

This style is much easier for the user to validate than a fast reload or a single still frame.

## Real-user scrolling vs JS scrolling on local X home (new)

When debugging why the X home feed does not load more posts, distinguish carefully between **JS-driven scrolling** and **real user input scrolling**.

### What happened in practice
The local automation scripts used browser-page JS such as:
- `window.scrollTo(0, 0)`
- `window.scrollBy(0, Math.floor(window.innerHeight * 0.72))`
- `article.scrollIntoView({behavior:'instant', block:'center'})`

Those methods changed `window.scrollY`, but the user correctly pointed out that manual scrolling on X normally shows visible loading behavior (spinner/skeleton/loading animation). JS scroll may bypass or fail to trigger the same chain of events as a real wheel/trackpad gesture.

### Important lesson
Do **not** tell the user you "manually scrolled" if you only changed scroll position through page JS. For X home lazy-loading bugs, that distinction matters.

### Better interpretation of evidence
If you observe something like:
- `scrollY` becomes very large
- `document.querySelectorAll('article').length` stays low (for example 5)
- the user says manual scrolling should trigger loading UI

then one plausible explanation is:
- the page/document height is large because of timeline container virtualization or placeholders
- but your JS scroll did not reproduce the real human input path that triggers feed loading

### Additional macOS finding
Trying to upgrade to more human-like local input with CoreGraphics event injection may still fail:
- CGEvent mouse-wheel injection can post successfully but leave `window.scrollY` unchanged
- CGEvent PageDown key injection can also leave `window.scrollY` unchanged

So there are two separate pitfalls:
1. JS scroll is not equivalent to manual scroll for X loading behavior
2. even OS-level synthetic wheel/key events may fail to drive the visible Chrome page in the current automation chain

### Response strategy
1. Be explicit about which scroll method was used.
2. If the user expects visible loading animations, do not rely on `window.scrollBy(...)` as proof that you reproduced manual behavior.
3. Verify scroll success with live DOM metrics after each attempt:
   - `window.scrollY`
   - `document.querySelectorAll('article').length`
   - presence of loading indicators (`[role="progressbar"]`, skeletons, loading text)
4. If CGEvent wheel/PageDown injection leaves `scrollY` at 0 or otherwise unchanged, report that the local GUI input injection path itself is failing.
5. Do not over-interpret a large `scrollY` as proof that many tweet cards are loaded; X may expose large virtualized container heights while keeping only a few `article` nodes materialized.

### Telegram delivery pitfall for recorded proof
When sending the recording to Telegram, `sendVideo` may fail intermittently (for example `curl: (56) Recv failure: Connection reset by peer`) even for a small MP4.

Fallback:
- retry once if appropriate
- if `sendVideo` is flaky, send the same `.mp4` via `sendDocument`
- Telegram may still render it as an animation/video-like attachment with preview, which is acceptable when the priority is reliable delivery of proof

### User-expectation lesson
The user may expect to literally see the automation happening on their visible machine.
If they say they cannot see your actions, explain clearly that:
- some actions run in the remote browser tool and are invisible locally
- local macOS automation via AppleScript/JS may not show obvious mouse movement
- actions may occur in another Chrome window/Space unless you explicitly bring the intended window frontmost

If the user wants visible proof, use the short screen-recording path instead of only describing the steps.

## Critical macOS gateway-session pitfall (new)

When Hermes is serving the user through a **background gateway process** (for example Telegram gateway) and tries to drive the user's real local Chrome on macOS, AppleScript may still be able to:
- read Chrome window/tab URLs
- execute JS in the active tab
- report `https://x.com/home`

But true user-input simulation can still fail completely.

### Observed symptoms
- `document.hasFocus()` stays `false`
- `document.visibilityState` stays `"hidden"`
- JS `window.focus()` does nothing
- synthetic clicks/scroll-wheel/PageDown events do not increment in-page click counters and do not change `scrollY`
- NSWorkspace / frontmost-app inspection from the automation process reports `loginwindow` as frontmost instead of `Google Chrome`
- the gateway/background Hermes process has `tty = ??` or otherwise looks detached from the visible interactive terminal session

### Interpretation
This means the automation process is **not attached to the same real frontmost GUI session** the user is looking at, even if:
- `launchctl managername` says `Aqua`
- Chrome can be activated via AppleScript
- WindowServer enumeration can still see Chrome windows

In this state, the process can often **read** Chrome but cannot truly **input** into the visible page.

### Important correction
Do not over-attribute this to Python version/signing alone.
Switching from an unsigned Python runtime to a signed Python runtime may still leave the same failure mode if the process is still running in the wrong GUI/session context.

### What to check
1. Read page focus/visibility directly from the target tab:
   - `document.hasFocus()`
   - `document.visibilityState`
2. Instrument a click counter in page JS:
   - `window.__hermes_clicks = 0; window.addEventListener('click', () => window.__hermes_clicks++)`
3. Attempt a real click / real wheel event.
4. Re-read:
   - click count
   - `scrollY`
   - focus/visibility
5. Inspect frontmost app from the same automation process.
   - If it says `loginwindow`, not `Google Chrome`, the process is not in the user's true foreground desktop context.

### Recovery strategy
If the gateway/background process shows `visibilityState = hidden` and frontmost app `loginwindow`:
1. Stop treating the gateway process as a valid path for true local user-input simulation.
2. Distinguish it from any real **foreground terminal Hermes** session the user may also have open.
3. Prepare a tiny local foreground validation script and ask the user to run it from the visible terminal/TTY session.
4. That script should:
   - activate Chrome
   - instrument click count + focus/visibility
   - send one real click + wheel scroll
   - print before/after JSON (`hasFocus`, `visibilityState`, `scrollY`, `articleCount`, `clicks`)
5. Use the result to determine whether the problem is:
   - gateway/background session isolation
   - or a broader macOS permission/input problem affecting even the foreground terminal session

### Rule
If local Chrome automation via gateway can read the page but `document.visibilityState` is `hidden`, do not claim you are exercising the same input path as a real user. Treat it as **session-context mismatch**, not merely a scrolling bug.
