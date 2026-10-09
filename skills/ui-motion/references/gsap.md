# GSAP timelines and scroll scenes

Read when GSAP already owns the sequence or the task needs its timeline/scroll controls. Check the installed version and required plugins first; do not add ScrollSmoother or a new React integration just for a local fix. Official references checked on 2026-10-09.

## Component lifetime

Scope selectors and created animations with `gsap.context(..., root)` and revert the context during teardown. `revert()` restores the recorded styles and disposes the recorded animations/ScrollTriggers; a context is a cleanup scope, not a playback controller. Keep the timeline handle for play/reverse/retarget behavior. [gsap.context](https://gsap.com/docs/v3/GSAP/gsap.context%28%29/).

Animations created later by click handlers or timers also need ownership. Register that later work with the context, or use `contextSafe` when the project already uses `@gsap/react`/`useGSAP`. Remove the actual event listener during cleanup as well; wrapping it does not remove it. Keep cleanup local rather than killing every timeline or ScrollTrigger in the application. [React integration](https://gsap.com/resources/React/).

Use one maintained timeline for a reversible panel. Repeated input should change its destination/direction, not create overlapping tweens from the original starting pose. Check callbacks against the current desired state before hiding content or applying final styles. A route change must leave no pin spacer, scroll lock or delayed callback behind.

## Responsive and reduced behavior

Use `gsap.matchMedia()` for media-dependent scene construction. Conditions can combine the project's breakpoints with `prefers-reduced-motion`; GSAP records work created in the callback and reverts it when the conditions change. Return cleanup for your own listeners/observers and call `mm.revert()` when the component is removed. For the reduced branch, restore the meaningful static states and ordinary document flow rather than creating a zero-duration pinned journey. [gsap.matchMedia](https://gsap.com/docs/v3/GSAP/gsap.matchMedia%28%29/).

Differentiate viewport changes from content changes. ScrollTrigger refresh recalculates start/end positions; `update()` only updates progress against existing positions. Refresh after a relevant async layout change, such as loaded media changing scene height, rather than in a scroll/frame loop. Verify resize across breakpoints and anchor navigation with the final fonts/content. [ScrollTrigger refresh](https://gsap.com/docs/v3/Plugins/ScrollTrigger/refresh%28%29/).

For tween values derived from geometry, use function-based values and `invalidateOnRefresh: true` when the associated animation must discard its cached starting values on refresh. Recalculating trigger positions alone does not refresh every tween's cached measurements. [ScrollTrigger configuration](https://gsap.com/docs/v3/Plugins/ScrollTrigger/).

Keep essential text visible in the base document. If a pinned graphic has a separate static explanation, ensure the explanation remains present for reduced motion and non-JS access. On mobile, choose a readable composition rather than shrinking the desktop pin distances and type until they fit.
