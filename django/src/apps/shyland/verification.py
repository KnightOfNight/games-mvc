"""v24.29 (#249 Part 2): the read-only verification family.

``make verify`` / ``make verify-prod`` (Part 1, shipped on main) run one
``verify_*`` management command per invocation against the dev stack or,
on the operator's confirmation, against production. This module is the
in-container half: the base class those commands are built on.

Deliberately Shyland-scoped. A shared home would be platform shared
surface under CLAUDE.md Rule 2 and would need its own stop-and-flag;
Shyland is the only consumer today. If a second game ever needs it,
moving it is that session's decision.

The two invariants:

- **Nothing is written.** The verification body runs inside an atomic
  block that is *always* rolled back, so any write — accidental or
  otherwise — is discarded rather than committed. This is the runtime
  backstop behind the ``verify_*`` name gate the Makefile enforces, and
  it is what makes pointing one of these at production safe.
- **Findings are reported, never repaired.** No verification command may
  mutate state, even to "fix" what it finds. The rollback enforces that
  at runtime; it is also a review rule. A finding is information — the
  answer to it is a design ruling, not a write.

Exit code is the outcome signal, because that is what ``make`` reads:
**0 = clean, nonzero = findings or error.** A failure has to be loud
through the Make target, not buried in stdout.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class _ForcedRollback(Exception):
    """Raised to unwind the atomic block once the body has finished.

    Never escapes :meth:`VerificationCommand.handle` — it exists only so
    the transaction rolls back on the success path exactly as it would
    on the failure path.
    """


class VerificationCommand(BaseCommand):
    """Base class for the ``verify_*`` read-only command family.

    Subclasses implement :meth:`verify` and do not override ``handle()``.
    :meth:`verify` writes its human-readable report to ``self.stdout``
    and returns the findings: an empty list (or ``None``) means clean and
    exits 0; a non-empty list is reported and exits nonzero.
    """

    def verify(self, *args, **options):
        """Perform the verification.

        Return a list of human-readable finding strings — empty or
        ``None`` when the check is clean. Must not mutate state; the
        surrounding transaction is rolled back regardless.
        """
        raise NotImplementedError(
            'Verification commands implement verify(), not handle().')

    def handle(self, *args, **options):
        findings = []
        try:
            with transaction.atomic():
                findings = self.verify(*args, **options) or []
                # The body is done and the report is written; unwind so
                # nothing it touched can reach the database.
                raise _ForcedRollback()
        except _ForcedRollback:
            pass

        if findings:
            self.stdout.write('')
            for finding in findings:
                self.stdout.write(f'  {finding}')
            # CommandError is Django's own nonzero-exit mechanism: it
            # exits 1 under run_from_argv and raises under call_command,
            # so make and the test suite both see the failure.
            raise CommandError(
                f'{self.__class__.__module__.rsplit(".", 1)[-1]}: '
                f'{len(findings)} finding(s) — reported, not repaired.')
