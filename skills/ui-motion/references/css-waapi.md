# CSS and Web Animations

Read for a small interaction or imperative animation without a framework engine. Browser references below were checked on 2026-10-09; check compatibility for the project's targets before introducing a newer CSS/API feature.

## CSS first for state changes

Put the durable appearance in the component's actual state classes/attributes. Transition named properties, not `all`, so an unrelated future layout change does not animate accidentally. Keep `:focus-visible` recognizable independently of hover. Apply pointer-specific decoration only where the input supports it; don't hide an action until hover.

Leave document content visible in base CSS. A reveal must enhance an already readable page. Keep reduced-motion state rules scoped to the component: a global near-zero duration hack can break code that waits for transition events.

`transitionend` is not a reliable sole owner of application state: it does not fire when a transition is cancelled or when there is no transition duration. Handle the instant path directly; if listening, filter the element and property and account for cancellation. Do not require an event to release focus or unlock scrolling. [MDN transitionend](https://developer.mozilla.org/en-US/docs/Web/API/Element/transitionend_event).

## WAAPI ownership and interruption

Keep the `Animation` handle with the component. For a two-endpoint effect, reverse or retarget the current playback when input changes; avoid creating an unbounded queue. `reverse()` flips direction, so repeated requests for the same desired state must not blindly flip it again. Track the desired state separately. [MDN reverse](https://developer.mozilla.org/en-US/docs/Web/API/Animation/reverse).

When cancelling and replacing an effect, capture the current visual state if continuity matters, then animate to the latest target. A completion handler must check that its handle/request is still current before applying cleanup. If using `animation.finished`, cancellation rejects it with `AbortError`; handle expected cancellation without swallowing unrelated errors. Unmount cancels the component's own animations and removes its listeners. [MDN cancel](https://developer.mozilla.org/en-US/docs/Web/API/Animation/cancel).

Prefer committing the final *semantic state* to classes or component state and releasing the animation. `commitStyles()` writes the current computed animation values to element styles; use it only when that inline state is intentional and clean it up before responsive CSS must regain ownership. Don't leave persistent fill effects or old inline dimensions accidentally overriding later layout. [MDN commitStyles](https://developer.mozilla.org/en-US/docs/Web/API/Animation/commitStyles).

Keep layout measurements outside the frame loop. When resize changes the endpoints, preserve the current logical state and rebuild the relevant effect rather than restarting an unrelated entrance. Handle reduced-motion changes by cancelling travel and applying the correct resting state, not by leaving the element halfway through a transform.
