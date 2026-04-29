---
name: text-to-pdf-macos
description: Convert UTF-8 plain text into a readable multipage PDF on macOS using built-in Swift/AppKit/CoreText when pandoc or LibreOffice are unavailable.
triggers:
  - User asks to turn extracted text into a PDF on macOS
  - Need a PDF document from plain text without external conversion tools
  - textutil exists but does not directly give the needed text->PDF workflow
---

# Text to PDF on macOS with built-in Swift

Use this when you have plain text content and need to deliver a real PDF file, especially in Hermes/Telegram flows where the user wants the actual file attachment.

## Why this skill exists

On macOS, `textutil` is often present, but it is not always the simplest path to a clean plain-text-to-PDF conversion. External tools like `pandoc`, `libreoffice`, or `pdftotext` may be missing. A reliable fallback is to render the text directly with Swift using `AppKit`, `CoreGraphics`, and `CoreText`.

This works for UTF-8 Chinese/English mixed text and creates a proper multipage PDF.

## Workflow

1. Save the text content to a UTF-8 `.txt` file with `write_file`.
2. For plain text, prefer macOS built-in `cupsfilter` first:
   - `cupsfilter /tmp/input.txt > /tmp/output.pdf`
   - This uses the system text-to-PDF pipeline and, in practice, produced a correctly oriented PDF when a custom Swift/CoreText render came out upside down.
3. Verify the output exists with `stat`.
4. Verify readability/orientation with a Quick Look preview render before sending:
   - `qlmanage -t -s 1000 -o /tmp/pdf_preview /tmp/output.pdf`
   - inspect the generated PNG with `vision_analyze()` if needed.
5. If the user wants richer layout, section styling, or embedded images, switch to a custom Swift/AppKit PDF generator instead of plain `cupsfilter`.
6. Deliver the actual file to the user with `MEDIA:/absolute/path/to/file` on Telegram.

## Escalation path

- Plain text only, fast path -> use `cupsfilter`.
- Need headings, cards, or images -> use a custom Swift/AppKit compositor.
- Always preview at least the first page before delivery when typography/orientation matters.

## Reference script

```swift
import Foundation
import AppKit
import CoreGraphics
import CoreText

let input = "/tmp/input.txt"
let output = "/tmp/output.pdf"
let text = try String(contentsOfFile: input, encoding: .utf8)

let pageWidth: CGFloat = 595
let pageHeight: CGFloat = 842
let margin: CGFloat = 50
let contentRect = CGRect(x: margin, y: margin, width: pageWidth - margin * 2, height: pageHeight - margin * 2)

let paragraph = NSMutableParagraphStyle()
paragraph.lineSpacing = 6
paragraph.paragraphSpacing = 10
paragraph.alignment = .left
paragraph.lineBreakMode = .byWordWrapping

let font = NSFont.systemFont(ofSize: 14)
let attrs: [NSAttributedString.Key: Any] = [
    .font: font,
    .paragraphStyle: paragraph,
    .foregroundColor: NSColor.black,
]

let attributed = NSAttributedString(string: text, attributes: attrs)
let framesetter = CTFramesetterCreateWithAttributedString(attributed as CFAttributedString)

var mediaBox = CGRect(x: 0, y: 0, width: pageWidth, height: pageHeight)
guard let ctx = CGContext(URL(fileURLWithPath: output) as CFURL, mediaBox: &mediaBox, nil) else {
    fatalError("Unable to create PDF")
}

var currentLocation = 0
let fullLength = attributed.length

while currentLocation < fullLength {
    ctx.beginPDFPage(nil)
    ctx.saveGState()

    ctx.textMatrix = .identity
    ctx.translateBy(x: 0, y: pageHeight)
    ctx.scaleBy(x: 1, y: -1)

    let path = CGMutablePath()
    path.addRect(contentRect)
    let frame = CTFramesetterCreateFrame(framesetter, CFRange(location: currentLocation, length: 0), path, nil)
    CTFrameDraw(frame, ctx)

    let visible = CTFrameGetVisibleStringRange(frame)
    currentLocation += visible.length

    ctx.restoreGState()
    ctx.endPDFPage()
}

ctx.closePDF()
print(output)
```

## Example terminal usage

```bash
cat >/tmp/text_to_pdf.swift <<'SWIFT'
# ...script above...
SWIFT
swift /tmp/text_to_pdf.swift
stat -f '%N %z bytes' /tmp/output.pdf
```

## Notes

- `CoreText` import is required for `CTFramesetter...` symbols.
- `NSImage.dataWithPDF` is not a reliable path for this text-rendering workflow.
- A hand-rolled `CGContext` + CoreText script can accidentally produce upside-down pages if the coordinate system is mishandled. Do not trust it without previewing the result.
- For plain text on macOS, `cupsfilter` is often the safest built-in route to a normally oriented PDF.
- If the user wants richer typography, headings, or images, build a custom AppKit/Swift compositor and verify the preview with `qlmanage` before sending.
- On Telegram, send the resulting PDF as an attachment with `MEDIA:` rather than only mentioning the path.

## Verification

Before finishing:
- confirm the PDF file exists and has non-zero size
- if needed, also keep the source `.txt` for regeneration
- send the PDF file itself, not just the pathname
