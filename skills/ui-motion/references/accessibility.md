# Accessible motion and imported assets

Read for interactive controls, substantial motion, loops or an imported animation. Sources checked on 2026-10-09.

## A usable reduced state

Respect `prefers-reduced-motion` at load and when it changes. CSS can express this directly; imperative effects must also settle or cancel when the preference changes. Reduce the motion causing difficulty: remove parallax, large translation/zoom, spinning and unnecessary loops. Keep state changes, instructions and status labels. Reduced motion does not mean all content is hidden, and opacity fades are optional. [MDN prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion).

A pause/stop/hide mechanism is required by WCAG 2.2.2 for moving, blinking or scrolling information that starts automatically, lasts more than five seconds, and runs alongside other content, unless the movement is essential. Auto-updating information has its own part of the criterion without that five-second condition. A hover-only pause does not cover touch or keyboard users. A user's pause choice should survive leaving/re-entering the viewport. [W3C Pause, Stop, Hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html).

## Focus and input

Keep existing accessible dialog/menu primitives. Motion should not replace their Escape handling, focus containment, return focus or trigger semantics. A visually closing panel must not leave an invisible focus trap; a reopened panel must not be hidden by an older completion. Move focus to a sensible surviving target before removing a focused item. [W3C dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).

Do not assume `opacity: 0`, an offscreen transform or `aria-hidden` prevents keyboard focus. Coordinate actual visibility/inertness with the semantic state and the primitive's lifecycle. For hover treatments, preserve visible focus and touch activation. Don't move a target away from a user approaching it. If drag changes a value or order, provide an equivalent control for users who cannot drag.

Test with keyboard-only navigation and touch/no-hover emulation, then toggle reduced motion while an effect is active. Inspect the settled interface as well as the intermediate frame. A stylesheet containing the media query is not proof that every animation respects it.

## Imported Lottie/dotLottie or other animated media

Treat the supplied asset as an input. Use the existing player and its documented lifecycle; inspect loading/error behavior, a meaningful static poster, pause/resume, reduced motion and destruction on unmount. Stop unnecessary playback while hidden/offscreen without overriding a user's explicit pause. Preserve the original asset and record its source/license in the project's media notes.

Critical text and actionable controls belong in the DOM, not only inside the animation. Check the imported asset in the actual chosen player and renderer; a JSON parse success is not a visual compatibility check. Authoring a new Lottie file or converting arbitrary HTML/CSS into Lottie is outside this skill.
