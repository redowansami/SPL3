"""A `RoundRobinTarget` that always tries one primary target first."""

from pyrit.prompt_target import RoundRobinTarget


class PrimaryWithFallbackTarget(RoundRobinTarget):
    """RoundRobinTarget that always tries targets[0] first, falling back to the
    rest only when it raises. Reuses RoundRobinTarget's exception-triggered
    fallback loop unchanged — only target *selection* differs from round-robin.
    """

    def _next_target(self):
        return self._targets[0]
