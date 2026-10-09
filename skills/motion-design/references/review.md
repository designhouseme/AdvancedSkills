# Review the final film, including frames between storyboard samples

Use the actual final encoded file. A clean HTML preview or contact sheet sampled once a second does not establish that the exported film has no one-frame blank, flash or jump.

```bash
python3 scripts/review_frames.py --film out/film.mp4 --outdir out/review
python3 scripts/review_frames.py --film out/film.mp4 --timeline timeline.generated.json --outdir out/review
python3 scripts/review_frames.py --film out/film.mp4 --cues out/cues.json --outdir out/review
```

Paths above are examples relative to the film project. Use the script from the skill directory if it was not copied into that project. Python standard library, FFmpeg and ffprobe are required; Pillow and npm are not. Contact sheets use the FFmpeg `drawtext` filter and its default font. A missing filter/font is a failed review, not a successful review without evidence.

`--timeline` and `--cues` are mutually exclusive. A generated timeline describes the **full final film**, with optional `fps`, `durationFrames`, `cuts: [seconds]` and `cues: [{id, t, d?, text?}]`. When provided, its expected frame count and frame rate must match the actual artifact. Review a rendered fragment without the full-film timeline: an offset contract is not implemented.

Legacy cues accept `{ "duration": 3, "cuts": [1.5], "cues": [...] }`; `cuts` is optional and uses seconds, just as in generated timelines. A cue is a named review moment; its presence does not establish that an abrupt change is intentional. Only an explicit `"type": "cut"` declares a cut. An explicit `"type": "hold"` with positive `d` annotates an intended hold. Ordinary cues with `d` are not inferred to be holds. Generated timeline cuts come from the top-level `cuts` array; generated v1 cues do not require a type.

## What the scan measures

1. ffprobe reads/counts the first video stream. Missing video, decoder errors and a mismatch against the container's declared frame count fail the review.
2. FFmpeg decodes **every frame**, without frame-rate resampling, into a 64×36 grayscale image. It records each presentation timestamp. The scanner keeps only three tiny images at once; scalar timestamps and a temporary decoder log cover the whole film. A timeout, partial raw frame, missing timestamp or incomplete frame count is an error.
3. Contiguous black or nearly uniform frames are grouped into runs. Their exact frame numbers and observed times are reported. Uniform means little grayscale variation; it can be a legitimate colour field and is a warning to inspect, not a rejected design.
4. A three-frame check finds a large change into a frame followed immediately by a large change back toward the surrounding image. This detects some isolated flashes, pops and blank frames. A persistent scene change is not classified as an isolated flash. A temporal outlier touching a declared cut is annotated as an expected cut transition. Black/uniform content still requires human judgement, even at a declared cut.
5. Review candidates include the first/last frame, anomalies, and the frame before/on/after declared cuts and cues. Cue ends are included when `d` exists. Candidate timestamps use decoded PTS relative to the first displayed video frame, including for variable-frame-rate inputs.

An unchanged patterned frame can hold for any duration without an error or a freeze warning. A declared hold does not excuse a black frame inside a scene that should contain text: the report preserves the content warning and annotates the hold.

All numeric thresholds are recorded in `review.json`; they are heuristic grayscale values, not perception standards. Tiny text, an occluded letter, colour-only changes of similar brightness and problems hidden by downscaling can escape this scan. The tool does not do OCR, inspect DOM geometry, listen to sound, certify flash safety, validate alpha, judge the story or test the renderer's determinism. These checks remain explicitly `not_checked`. Use the separate renderer repeatability check and the film/asset checks as well.

## Evidence and statuses

The output is `review.json` and JPEG contact sheets with timestamp labels. Each 320×180 thumbnail has a separate 28-pixel dark label strip above it; the timestamp does not cover any film content. The report records the final film's exact SHA-256 and size, probe data, measured frame count/fps, timestamp coverage, scan settings, declared cuts, findings and each sheet's SHA-256. The film and input timeline are hashed again before evidence is published; a change during review fails completion. The JSON is replaced atomically only after the run has a result. A failed run replaces an old successful report with a failed report; it never reuses old evidence as current.

Images are bounded: at most 96 candidates, 12 cells per page, eight pages. Candidate selection is deterministic: first/last, anomalies, then timeline boundaries; selected frames are presented chronologically. At most 200 detailed event findings are retained, while aggregate event counts still cover the entire scan. Omitted candidates/findings are recorded and make the review a warning. This bounds evidence output, not scan coverage. Add specific full-resolution stills for omitted areas or important details before accepting the film.

Sheet names include an artifact-hash prefix and settings/contract fingerprint. Reports reference only the current sheets. Files from older reviews are retained; do not infer the current result by opening an arbitrary JPEG in the directory. Use the sheet list in `review.json`.

- `passed`: the specified mechanical check completed without a flagged condition; this is not a human visual approval.
- `warning`: a candidate requires inspection, frame intervals vary, or bounded output omitted detailed evidence.
- `failed`: input, decode, coverage, contract or evidence generation could not be completed correctly.
- `not_checked`: the tool did not perform that kind of review.

Exit status is **0 for completed reviews**, including warnings, and **1 for failure/incomplete review**. Invalid command syntax uses argparse's exit status 2. Scripts that require no outstanding warnings must inspect `review.json.status`; do not interpret exit 0 alone as delivery approval. Each external command has a 300-second limit by default; use `--timeout SECONDS` for longer films or slower hardware. A timeout never becomes a pass.

After generating the evidence, actually view the current sheets, inspect suspicious frames at full resolution, and record which warnings are intentional. Re-run after changing or re-encoding the film: the previous report certifies a different byte sequence.
