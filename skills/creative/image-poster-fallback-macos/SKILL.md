---
name: image-poster-fallback-macos
description: Generate and finish a themed poster image on macOS when first-party image tools/API keys are unavailable, using Pollinations as a fallback, vision-based candidate selection, and Swift/AppKit text overlay for signature lines.
triggers:
  - User wants a generated poster image right now
  - image_generate tool is unavailable
  - No FAL_KEY / GOOGLE_API_KEY / GEMINI_API_KEY is configured
  - Need to deliver the final image file directly in Telegram
  - Need subtle Chinese signature text on an image but Pillow/ffmpeg drawtext is unavailable
version: 1.0.0
author: Hermes Agent
---

# Image poster fallback on macOS

Use this when the user expects the finished image file immediately, but the normal image generation toolchain is unavailable.

This workflow was validated in a real Telegram task for a Chinese fantasy collectible poster. It is useful when:
- Hermes `image_generate` is not available because required credentials are missing
- The user still wants a directly delivered final image
- You need to iterate on prompts and visually rank candidates
- You need to add subtle Chinese signature text afterward

## Core lessons

1. Check the actual generation prerequisites first.
   - In this codebase, `tools/image_generation_tool.py` requires `FAL_KEY` or a managed FAL gateway.
   - Do not assume Gemini/OpenAI image generation is available just because the user mentions “image 2.0”.

2. If first-party generation is unavailable, a pragmatic fallback is Pollinations image generation.
   - Direct `urllib` fetches may return `403 Forbidden`.
   - `curl -L -A 'Mozilla/5.0'` worked reliably where plain Python `urllib.request.urlretrieve()` failed.

3. Generate multiple prompt variants, then use `vision_analyze()` to rank them.
   - The first image may be pretty but conceptually too generic.
   - 2–3 prompt variants plus vision-based evaluation gives a much better final pick.

4. If you need text overlay on macOS and common tools are missing:
   - Pillow may not be installed.
   - ffmpeg may exist but be built without the `drawtext` filter.
   - A Swift/AppKit script is a reliable built-in fallback for compositing text onto the image.

5. For Telegram delivery, send the actual finished file via `MEDIA:/absolute/path`.
   - Do not just describe the result or send a filesystem path.

## Recommended workflow

### 1. Verify the normal toolchain is unavailable

Use terminal checks such as:
```bash
source venv/bin/activate
python - <<'PY'
import os
print('FAL_KEY', bool(os.getenv('FAL_KEY')))
print('GOOGLE_API_KEY', bool(os.getenv('GOOGLE_API_KEY')))
print('GEMINI_API_KEY', bool(os.getenv('GEMINI_API_KEY')))
PY
```

If needed, also verify the Hermes tool’s own readiness:
```bash
source venv/bin/activate
python - <<'PY'
from tools.image_generation_tool import check_image_generation_requirements
print(check_image_generation_requirements())
PY
```

### 2. Generate fallback candidates with Pollinations

Use `curl`, not bare `urllib`, and include a browser-like user agent.

Pattern:
```bash
PROMPT_URLENCODED='...'
curl -L -A 'Mozilla/5.0' \
  "https://image.pollinations.ai/prompt/${PROMPT_URLENCODED}?width=1024&height=1536&model=flux&nologo=true&private=true&enhance=true" \
  -o /tmp/candidate.jpg -sS
```

Notes:
- `private=true` and `enhance=true` were useful defaults.
- The returned image may not match the requested pixel size exactly; verify actual dimensions afterward.
- For collectible posters, start with 3 prompt variants rather than over-optimizing one prompt.

### 3. Prompting strategy for narrative silhouette posters

For requests like “巨大优雅的人物侧脸剪影 + 内部世界观叙事 + 电影海报/梦幻水彩融合”, include these ideas explicitly:
- giant elegant side-profile silhouette as outer contour
- inside the silhouette grows a coherent world tied to the theme
- not collage / no clutter / no template background
- cinematic poster + dreamy watercolor illustration
- soft aerial perspective, misty transitions, paper grain, dry brush edges
- restrained luxury layout, quiet / sacred / nostalgic / legendary
- theme-specific symbols, architecture, creatures, relics

When the first result is too generic, strengthen theme specificity with details like:
- crown / throne / ceremonial blade
- named emotional motifs
- attendant / guardian / spirits / rebirth symbols
- signature locations or mythic structures

### 4. Rank candidates with vision

Run `vision_analyze()` on each candidate and compare:
- silhouette clarity
- theme recognizability
- coherence of internal worldbuilding
- premium / restrained composition
- whether the image feels specific or generic

Pick the strongest candidate before post-processing.

### 5. Check local post-processing tools before assuming they exist

Useful checks:
```bash
which ffmpeg
which sips
python3 - <<'PY'
for m in ['PIL','AppKit']:
    try:
        __import__(m)
        print(m, 'OK')
    except Exception as e:
        print(m, 'NO')
PY
```

Real-world finding:
- `ffmpeg` was installed, but lacked the `drawtext` filter.
- `PIL` was missing.
- `/usr/bin/swift` was available and became the best text-overlay route.

### 6. Add subtle Chinese signature text with Swift/AppKit

If you need refined Chinese signature lines in a corner of the poster, create a Swift script that:
- loads the base image with `NSImage`
- optionally upscales 2× for cleaner text rendering
- draws a translucent rounded panel if needed for readability
- uses a CJK-capable macOS font such as `Songti SC` / `STSong`
- right-aligns the text in a low-profile corner area
- exports JPEG or PNG

Important practical notes:
- A lightly translucent panel behind the text can improve legibility while remaining subtle.
- Without the panel, long Chinese quote lines may become too faint against misty backgrounds.
- Exporting huge PNGs can create files too large for some vision pipelines; JPEG is often a better final delivery format.

### 7. Verify the finished result

Use `vision_analyze()` on a smaller JPEG if the full-size file is too large.
Ask it specifically whether the signature text is:
- present
- reasonably legible
- low-profile
- integrated rather than overpowering

If needed, revise contrast or add a subtle backing panel.

### 8. Deliver the actual image

On Telegram, send:
```text
MEDIA:/absolute/path/to/final.jpg
```

Do not end with only a description or a local path.

## Practical command snippets

### Check actual image size
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x /tmp/image.jpg
```

### Convert oversized PNG to JPEG
```bash
sips -s format jpeg /tmp/input.png --out /tmp/output.jpg >/dev/null
```

### Make a smaller preview for vision verification
```bash
sips -Z 1600 /tmp/final.jpg --out /tmp/final_small.jpg >/dev/null
```

### Find a built-in Songti font on macOS
```bash
find /System/Library/Fonts -name '*Songti*'
```

## Minimal Swift/AppKit overlay template

```swift
import AppKit
import Foundation

let inputPath = "/tmp/base.jpg"
let outputPath = "/tmp/final.jpg"

let lines: [(String, CGFloat, CGFloat, NSColor)] = [
    ("遐蝶", 50, 250, NSColor(calibratedRed: 0.15, green: 0.23, blue: 0.31, alpha: 0.92)),
    ("死荫的侍女", 30, 202, NSColor(calibratedRed: 0.19, green: 0.30, blue: 0.40, alpha: 0.90)),
    ("你要呵护世间魂灵的恸哭，拥抱命运的孤独", 25, 152, NSColor(calibratedRed: 0.22, green: 0.33, blue: 0.43, alpha: 0.88)),
    ("生死皆为旅途。当蝴蝶停落枝头，那凋零的又将新生", 25, 108, NSColor(calibratedRed: 0.22, green: 0.33, blue: 0.43, alpha: 0.88)),
]

guard let input = NSImage(contentsOfFile: inputPath), let rep = input.representations.first else {
    fatalError("Failed to load image")
}

let srcSize = NSSize(width: rep.pixelsWide, height: rep.pixelsHigh)
let targetSize = NSSize(width: srcSize.width * 2, height: srcSize.height * 2)

let outputImage = NSImage(size: targetSize)
outputImage.lockFocus()
NSGraphicsContext.current?.imageInterpolation = .high
input.draw(in: NSRect(origin: .zero, size: targetSize), from: NSRect(origin: .zero, size: srcSize), operation: .copy, fraction: 1.0)

let panelRect = NSRect(x: targetSize.width - 760, y: 74, width: 670, height: 250)
NSColor(calibratedWhite: 1.0, alpha: 0.18).setFill()
NSBezierPath(roundedRect: panelRect, xRadius: 16, yRadius: 16).fill()

let paragraph = NSMutableParagraphStyle()
paragraph.alignment = .right
paragraph.lineBreakMode = .byWordWrapping

func font(size: CGFloat) -> NSFont {
    NSFont(name: "Songti SC", size: size)
        ?? NSFont(name: "STSong", size: size)
        ?? NSFont.systemFont(ofSize: size)
}

for (text, fontSize, yOffset, color) in lines {
    let shadow = NSShadow()
    shadow.shadowOffset = NSSize(width: 0, height: -1)
    shadow.shadowBlurRadius = 3
    shadow.shadowColor = NSColor(calibratedWhite: 1.0, alpha: 0.22)

    let attrs: [NSAttributedString.Key: Any] = [
        .font: font(size: fontSize),
        .foregroundColor: color,
        .paragraphStyle: paragraph,
        .strokeColor: NSColor(calibratedWhite: 1.0, alpha: 0.36),
        .strokeWidth: -1.2,
        .shadow: shadow,
    ]

    let attributed = NSAttributedString(string: text, attributes: attrs)
    attributed.draw(in: NSRect(x: targetSize.width - 724, y: yOffset, width: 620, height: fontSize * 2.4))
}

outputImage.unlockFocus()

guard let tiffData = outputImage.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiffData),
      let jpgData = bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.92]) else {
    fatalError("Failed to encode JPG")
}

try jpgData.write(to: URL(fileURLWithPath: outputPath))
print(outputPath)
```

Run it with:
```bash
swift /tmp/overlay.swift
```

## Decision rules

- If Hermes image generation is available, use it first.
- If it is unavailable and the user still expects immediate delivery, switch to the fallback instead of stalling.
- If the first fallback image is visually good but semantically generic, make more prompt variants and rank them with vision.
- If text overlay is too faint, add a translucent backing panel rather than making the text huge.
- Prefer a final JPEG for delivery and vision verification if a PNG becomes excessively large.

## Verification checklist

Before finishing:
- verified normal image toolchain was unavailable
- generated multiple fallback candidates
- selected the best one using vision-based comparison
- added requested signatures/quotes with restrained styling
- verified text presence and legibility with vision on a downsized copy if needed
- delivered the actual final image file to the user
