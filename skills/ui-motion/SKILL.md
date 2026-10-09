---
name: ui-motion
description: >-
  Designs, implements and fixes animation inside an existing website or app:
  interaction feedback, state and layout transitions, entrances, scroll choreography
  and imported animation playback. Use when interface motion needs to work across
  repeated input, navigation, mobile and reduced-motion preferences. Not for rendering
  a standalone video or GIF, editing recorded footage, or creating Lottie assets.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.0"
---

# UI motion

Make a change of state easier to understand without delaying the task. Work in the existing project, preserving its copy, layout intent, semantic controls and component library. A small interaction change needs a small implementation, not a new design process.

## Start from the interface

Inspect the affected component, its current states, animation dependencies and versions, and brand tokens. Reproduce a reported fault before changing it when a browser is available. Infer the motion's purpose from the request and the interface; ask only about a missing decision that would materially change the result.

For a simple fix, record the intended behavior in a sentence. For a sequence, use [intent and choreography](references/intent-choreography.md): trigger, start and resting states, what changes first, interruption, reduced motion and mobile behavior. Keep these notes with the component or existing design documentation; a separate spec is optional.

## Choose one owner for each animated property

Use the project's working animation stack first. For simple hover, focus, press or state changes without an existing owner, start with CSS. Add a runtime only when the requested behavior needs it; don't install several engines or migrate packages as part of a motion fix.

| Work | Read when needed |
|---|---|
| CSS transitions, imperative playback, cancellation or reversal | [CSS and Web Animations](references/css-waapi.md) |
| React state, presence or layout using the installed Motion package | [Motion for React](references/motion-react.md) |
| Authored timelines or scroll scenes using GSAP | [GSAP](references/gsap.md) |
| Reduced motion, focus, touch, looping or imported assets | [Accessibility](references/accessibility.md) |
| Jank, heavy paint, layout shifts or costly continuous animation | [Performance](references/performance.md) |

Check the installed version against official documentation linked in the relevant reference before using unfamiliar APIs. CSS, WAAPI, Motion and GSAP must not compete for the same element's transform; use one owner or separate wrappers when distinct behaviors must compose.

## Preserve the behavior

- **State owns the result.** Input, validation, selected values and navigation do not wait for decorative animation. Repeated input retargets or reverses the active motion; an obsolete completion callback must not hide a reopened panel or restore old data.
- **The resting interface works without the effect.** Static/SSR content and primary actions stay visible if animation JavaScript fails or is disabled. Do not put essential page content at `opacity: 0` until hydration or an observer runs. Preserve an existing app's loading/error behavior instead of broadening the task into an architecture rewrite.
- **Reduced motion is a complete state.** Remove unnecessary travel, parallax and continuous effects while keeping the same information and usable controls. An immediate update or small fade may fit; a fade is not mandatory. Handle preference changes while the page is open.
- **Semantics survive animation.** Keep real links/buttons and existing dialog/menu primitives. Opacity alone does not remove a control from keyboard focus. Restore focus appropriately after closing, keep focus indicators visible, and give touch users a path that does not depend on hover.
- **Own the lifecycle.** Scope animations to the component. Clean up animations, subscriptions, observers and listeners on unmount; leave no stale inline styles, scroll locks or pin spacers. Recompute geometry when relevant content, fonts or layout changes, without rebuilding on every frame.
- **Brand behavior is intentional.** Reuse suitable timing/easing tokens. Choose travel and sequencing from the task and geometry, not a fixed quota of layers, a universal duration cap or an obligatory entrance on every section.

## Verify the changed path

Use the project's normal build/type/lint checks. Exercise the changed interaction in a browser; stills alone cannot establish that interruption or cleanup works. Select the relevant checks rather than running a site-wide audit for one hover rule:

- trigger → halfway interruption → opposite input → final resting state;
- repeat the action, navigate away and back, or unmount/remount the component;
- keyboard focus/activation/Escape where applicable, touch without hover, and affected viewport sizes;
- reduced motion both at load and after changing the preference; no-JS/static fallback for page entrances;
- resize or changed content for measured/pinned layouts; console errors and layout stability.

Keep a short capture or targeted assertions when the behavior is substantial or regressed before. Inspect initial, intermediate and settled states. A config saying `fps: 60` is not a measurement; report performance only with an actual trace and its test conditions. If a browser or device is unavailable, state precisely which behavior remains unverified.

Deliver the code, how to reproduce the interaction, and the relevant verification results. Standalone generated MP4/GIF work belongs to `motion-design`; cuts, captions and recorded footage belong to `video-edit`. An existing Lottie/dotLottie asset may be integrated and checked here, but this skill does not promise to convert HTML/CSS motion into that format.
