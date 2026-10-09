# Anchor a motion insert to an edit occurrence

`src_at` is a time in the source recording. The same source time can occur more than once in an edit, for example when a sentence opens the film and returns in its original place. Give those edit segments different `id` values and select the intended one with the insert's `segment_id`.

```json
{
  "segments": [
    {"id": "hook", "in": 40.0, "out": 44.0, "text": "The result."},
    {"id": "explanation", "in": 10.0, "out": 20.0, "text": "How we got there."},
    {"id": "result", "in": 40.0, "out": 44.0, "text": "The result."}
  ],
  "inserts": [
    {"src": "inserts/result.mp4", "src_at": 41.0, "dur": 2.0, "segment_id": "result"}
  ]
}
```

The example shows the selector fields; the rest of `edit.json` still supplies the source, captions and other existing options. `src_at` remains a source time even when `segment_id` is present. It is not seconds into the chosen segment or the output film. Reordering the segments preserves the chosen occurrence while changing its output time.

- Segment `id` is optional. When present, it must be a unique non-empty string without leading/trailing whitespace. IDs are preserved in `cuts.json` under `segments[].id`; the existing numeric `seg` fields for captions/effects are unchanged.
- `segment_id` must match an ID in the processed edit. An unknown ID or an anchor outside that segment is an error, even if another segment happens to cover the source time.
- Without a selector, exactly one matching segment keeps the previous behavior. Multiple matches are an error with the candidate indexes/IDs; add IDs and choose the intended occurrence instead of relying on order.
- Matching retains the existing snapping tolerance: `in - 0.3 <= src_at < out` using the processed cut. An anchor just before the snapped in-point is clamped to that in-point. The out-point is exclusive. Tolerance can make nearby cuts ambiguous too.
- Placement still rounds the start and duration to the edit's frame grid and clips the insert at the selected segment's end. A positive requested duration that rounds to zero, or an anchor rounding onto the segment end, is an error rather than an empty insert.
- `skip` is a nonnegative time into the insert clip, not the recorded source. A nonzero skip probes the clip and shortens the insert to the remaining complete frames if necessary. An unreadable duration or no remaining frame is an error. Inserts without skip keep the existing rendering path; placement alone does not certify that their media decodes or is long enough.

Before delivery, inspect the encoded first frame and transition of the selected occurrence. Confirm the insert starts with visible content and ends on the intended cut. The selector fixes occurrence mapping; it does not establish that the chosen source words or visual are editorially correct.
