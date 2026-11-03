# Submission checklist

## Verified public event information (2026-11-03)

Source: [Meta event page](https://dev.meta.ai/events/global-hackathon). It identifies
the indie track, supported Meta models, and a November 4, 2026, 9 PM ET deadline
(9 PM in Panama on that date). The landing page says selected participants must
accept official rules but does not expose the full entrant rules.

Do not treat the following unverified clauses as satisfied by the landing page:

- [ ] Read the participant portal's full official rules and save their URL/version.
- [ ] Verify required repository visibility and grant the judges access.
- [ ] Verify eligibility, team size/membership, and all submission fields.
- [ ] Verify model-use requirements and whether an offline-only take qualifies.
- [ ] Verify third-party licensing, SAM License compatibility, and IP grants.
- [ ] Verify video length, hosting, language, and accessibility requirements.
- [ ] Complete the actual submission in the participant portal.

## Repository and handoff

- [x] Project MIT license and synthetic imagery provenance are present.
- [x] UniProt reference is attributed and its CC BY 4.0 license recorded.
- [x] Python and JavaScript lockfiles support reproducible installs.
- [x] No credential values are committed; `.env` is ignored.
- [x] Simulation-only scope is visible in the app, README, and opening narration.
- [x] Backend integration uses actual Opentrons simulation.
- [x] Dashboard consumes one compile response and displays attempts/refusals.
- [x] Existing repository collaborators have write/admin access.
- [ ] Confirm lane owners and whether the fourth account is an active member.
- [ ] Confirm preferred legal names for copyright attribution.
- [ ] Verify review auto-routing after CODEOWNERS is merged to the base branch.
- [ ] Obtain the one human PR approval required by the existing main ruleset.

## Live evidence still required

- [ ] Authenticated Muse Spark call succeeds using the configured team account.
- [ ] Authenticated SAM 3.1 call returns 96 mapped masks for the synthetic frame.
- [ ] ESMFold partner endpoint is deployed; record measured latency and actual cost.
- [ ] Optional Modal cold/warm timings measured, or explicitly use the tested local fallback.
- [ ] Watch the complete demo video and verify intelligible audio and duration.

Credentials were unavailable during implementation. Unit tests validate adapters
using test responses; they are not evidence of authenticated service availability.
