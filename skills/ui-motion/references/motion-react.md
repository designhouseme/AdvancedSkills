# Motion for React

Read only when the project uses Motion/Framer Motion or the requested behavior justifies adding it. Inspect the installed package and imports first; don't install both packages or migrate an existing import solely to match an example. Official references checked on 2026-10-09.

## Keep state and identity stable

Let React state select `animate` targets or variants. Stable item IDs preserve identity during filtering/reordering; index keys can animate the wrong record. Avoid changing keys to replay an entrance on every render. Keep form fields and semantic controls in their established component primitives.

`initial={false}` skips the entrance and renders the `animate` state initially. Use a visible target for important static/SSR content; this prop does not make a hidden target visible. Where hooks or browser APIs are needed in Next.js App Router, place them behind the appropriate client boundary rather than converting the whole page. [Motion component](https://motion.dev/docs/react-motion-component), [Next.js client boundary](https://nextjs.org/docs/app/api-reference/directives/use-client).

Keep `AnimatePresence` mounted around the conditional child if an exit is required. Give direct children stable unique keys. Choose sequencing from the interaction: `mode="wait"` deliberately delays the next child and supports one at a time, so it is not a universal fix for rapid switching. A fading DOM node still exists; ensure exiting controls cannot retain inappropriate focus or intercept input. [AnimatePresence](https://motion.dev/docs/react-animate-presence).

## Reduced motion and cleanup

Use an existing `MotionConfig` policy or `reducedMotion="user"` at the relevant scope. It suppresses transform/layout animations while other animated properties can remain. Use `useReducedMotion` for behavior that needs a different structure, such as removing parallax or replacing a moving sequence with visible steps. CSS effects, media players and other engines need their own preference handling. [Motion accessibility](https://motion.dev/docs/react-accessibility).

For imperative sequences, `useAnimate` scopes selectors and automatically cleans up animations it creates on unmount. Still clean up event listeners, timers and external observers, and prevent async completion from applying stale state after a newer request. [useAnimate](https://motion.dev/docs/react-use-animate).

Effect setup and cleanup must survive React's development setup → cleanup → setup cycle. Do not disable Strict Mode to hide duplicate motion. Test close/reopen during exit, unmount during a sequence, and route-back remount. The latest state should win and local animations should not affect another component instance. [React useEffect](https://react.dev/reference/react/useEffect).

For drag or scroll tracking, prefer the library's motion values over setting React state on every frame. Preserve an equivalent button/keyboard path for an action that otherwise depends on dragging. Measure a reported performance problem in the actual component before claiming a frame-rate improvement.
