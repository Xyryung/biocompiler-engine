# Submission checklist

## Official sources reviewed (2026-11-03)

The [event page](https://cerebralvalley.ai/e/meta-ai-developer-hackathon) lists the
November 4, 2026, 9 PM ET deadline (9 PM in Panama).
The [official terms and event waiver](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver)
display October 25, 2026 as their date. The document was read in full, including
its submission, licensing, and IP clauses.

Relevant requirements:

- Indie teams may have up to four members. An authorized representative submits
  on the team's behalf and identifies every member.
- Projects use Meta AI tooling. The document does not establish that a demo
  using only mock responses meets this requirement.
- Entrants retain ownership and grant organizers broad, perpetual,
  non-exclusive submission rights. Shared materials are not confidential.
- Open-source components are permitted when their licenses are followed and
  the project builds on them. Preserve project and dependency attributions.
- The reviewed text does not specify public repository visibility, a video
  duration limit, or a video hosting service; confirm these in the submission form.

- [x] Read the official terms and record their URL/displayed date.
- [x] Confirm four team members; the team fits the stated size limit.
- [ ] Confirm each member's individual eligibility, acceptance, and agreement to the rules.
- [ ] Select the authorized submission representative and complete all portal fields.
- [ ] Confirm repository/judge access and video requirements in the submission form.
- [ ] Obtain live Meta model evidence for the submission.
- [ ] Confirm dependency license compliance, including the upstream SAM License.
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
- [x] Confirm all four accounts; ownership is shared without separate engineering roles.
- [x] Attribute the confirmed team by their supplied GitHub identities in LICENSE.
- [x] Verify automatic review routing: test PR #19 requested MateoDG2006, yukki2126,
      and Xyryung automatically against the shared-CODEOWNERS base branch.
- [ ] Obtain the one human PR approval required by the existing main ruleset.

## Live evidence still required

- [ ] Authenticated Muse Spark call succeeds using the configured team account.
- [ ] Authenticated SAM 3.1 call returns 96 mapped masks for the synthetic frame.
- [x] Obtain a real ESMFold prediction and bundle the issue #9 cached fallback;
      record original request latency and the public endpoint's client cost.
- [x] Explicitly use and benchmark the actual local Opentrons fallback permitted by #11.
- [ ] Watch the complete demo video and verify intelligible audio and duration.

Credentials were unavailable during implementation. Unit tests validate adapters
using test responses; they are not evidence of authenticated service availability.
