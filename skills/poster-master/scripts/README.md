# Scripts

Every script runs on the standard library plus the packages in
[[BT]]../requirements.txt[[BT]]. Nothing here needs a network connection at run time.

| Script | Purpose | Needs |
|---|---|---|
| [[BT]]new_project.js[[BT]] | Scaffold a poster project from the stage templates | Node 18+ |
| [[BT]]editor/server.js[[BT]] | The local component editor | Node 18+ |
| [[BT]]export_psd.py[[BT]] | Write a layered PSD from a manifest | Pillow |
| [[BT]]check_delivery.py[[BT]] | Automated delivery checks | Pillow, OpenCV (optional) |
| [[BT]]qr_extract.py[[BT]] | Detect, decode, crop, and regenerate QR codes | OpenCV, numpy, Pillow |
| [[BT]]cutout.py[[BT]] | Background removal with an edge-quality report | rembg, Pillow |

## new_project.js

[[BT]][[BT]][[BT]]bash
node new_project.js --project "<dir>" --name "<项目名>" --size 1024x1536
[[BT]][[BT]][[BT]]

Creates the project folder, the six stage documents, the asset ledger, an
[[BT]]assets/[[BT]] folder, an [[BT]]exports/[[BT]] folder, and an empty component source.
Existing files are not overwritten unless [[BT]]--force[[BT]] is passed.

## editor/server.js

[[BT]][[BT]][[BT]]bash
node editor/server.js --project "<dir>" [--port 41735]
[[BT]][[BT]][[BT]]

Opens the project in a local editor at [[BT]]http://127.0.0.1:41735/[[BT]]. The server binds to
the loopback interface only. See [[BT]]../references/editor-source-format.md[[BT]].

## export_psd.py

[[BT]][[BT]][[BT]]bash
python export_psd.py manifest.json
[[BT]][[BT]][[BT]]

The manifest lists layers in composition order (background first). The editor calls
this automatically for its PSD export.

## check_delivery.py

[[BT]][[BT]][[BT]]bash
python check_delivery.py --project "<dir>" --expect "海报-v1-print-A2.png=2480x3508"
[[BT]][[BT]][[BT]]

Checks that each export opens, matches the expected pixel size, uses a sane colour
mode, and — for PNG — whether a QR code is present and decodes. Exit code is
non-zero when a check fails.

The machine check does not judge distance legibility, factual accuracy, licences,
or whether a QR scans on a real phone. Those remain manual.

## qr_extract.py

[[BT]][[BT]][[BT]]bash
python qr_extract.py --input 截图.png --output 裁切.png --expect "https://example.com/join"
python qr_extract.py --generate "https://example.com/join" --output 二维码.png
[[BT]][[BT]][[BT]]

Always compare the decoded string with the client's stated link. A code that opens
is not necessarily the code the client meant.

## cutout.py

[[BT]][[BT]][[BT]]bash
python cutout.py --input 人物.jpg --output 人物-抠图.png --preview 边缘预览.png
[[BT]][[BT]][[BT]]

Produces a transparent PNG and an edge report. It is a first pass: judge the hair
outline, the gaps between strands, the clothing edge, the halo, and the
proportions before using the result in a poster.

