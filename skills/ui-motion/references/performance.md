# Measure the changed motion

Read for reported jank, continuous effects, pinning or costly layout/paint. Do not turn an ordinary interaction edit into a full performance audit unless its behavior warrants one.

Prefer transform/opacity for movement and fading when they express the intended change. Other properties may be justified: an accordion changes document geometry, a color change communicates state. Measure their actual cost instead of claiming every non-transform animation is invalid or every transform is free. Large composited surfaces, paint effects and excessive promoted layers can still be expensive. [web.dev animation guide](https://web.dev/articles/animations-guide), checked 2026-10-09.

Reproduce the problem with the actual content and input sequence. Record the browser, viewport, hardware or throttling, and action. Use a performance trace to distinguish scripting, forced layout, paint and compositing. A frame-rate target or bundle-size field in a config proves none of these.

Match the correction to the cause:

- Batch geometry reads before writes; don't measure and mutate layout repeatedly inside the same frame.
- Avoid framework rerenders for every pointer/scroll tick when the installed animation engine already has a value pipeline.
- Cache stable geometry, and invalidate it for relevant resize/content/font changes instead of assuming mount-time positions last forever.
- Pause nonessential loops outside the visible page/viewport. Remove subscriptions and animation work when a component leaves the page.
- Use `will-change` only for a measured need and remove it when no longer needed; don't promote all cards or a whole page by default.
- Keep the primary page content in the initial readable render. Animation must not become a loading gate for the headline, image or CTA.

After the targeted fix, repeat the same trace or observable interaction. Check input response and layout stability with the longest real content, and ensure the change still works with reduced motion. Report measured conditions and remaining uncertainty, rather than a universal claim such as “120 fps on every device.”
