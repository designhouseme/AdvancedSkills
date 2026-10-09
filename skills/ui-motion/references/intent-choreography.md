# Intent and choreography

Read for a new sequence or when the motion feels arbitrary. For one timing correction, keep the intent next to the change rather than creating a separate document.

Describe the visitor's task first: see what changed, find the result, understand a relationship, or receive feedback. Define the useful resting interface before animating it. A weak hierarchy needs a layout correction within the authorized scope, not more movement.

For substantial work, record only decisions that affect implementation:

| Decision | What to capture |
|---|---|
| Purpose | The change or relationship the motion makes clear |
| Trigger | Input, state update, route change or scroll position |
| Start → rest | Actual component states; information present in both |
| Sequence | Primary change, necessary supporting changes, then a readable rest |
| Timing | Existing tokens or chosen duration/easing with a reason |
| Repeated input | Retarget, reverse, replace or ignore an already satisfied request |
| Interruption | What happens on close, navigation, cancellation or changed data |
| Alternatives | Reduced motion, touch and narrow layouts |
| Ownership | Component/engine responsible for motion and cleanup |
| Evidence | Interaction that demonstrates the intended result |

Keep attention on the task's primary object. Supporting movement earns its place by clarifying that object; background animation is optional. Preserve continuity where a list item becomes a detail panel, but don't delay the user's next action to finish a flourish. High-frequency interactions should tolerate repetition without becoming a performance or attention cost.

Brand motion tokens can name roles such as `feedback`, `panel`, `emphasis` and `exit`, with timing/easing and reduced behavior. They are project choices, not universal speed limits. Use consistent behavior for equivalent interactions; allow a different treatment when distance, reading load or meaning differs. Don't impose a fixed personality preset on an existing brand.

A useful interruption example: opening an inspector, closing it halfway, then reopening it should settle open with current data. Define that result before deciding whether to reverse a timeline or animate toward the latest state. A queued series of complete open/close animations is usually the wrong model for such a control.

For scroll work, preserve the document's reading order and ordinary keyboard/anchor navigation. Provide an intelligible static sequence when motion is reduced. Pinning should serve a requested explanation; avoid adding it to make an otherwise ordinary page feel animated.
