# PlanBridge — Click-by-click demo guide

This walkthrough is intended for a hiring manager reviewing forward-deployed engineering, implementation leadership, and end-to-end quality engineering capabilities. **All organizations, participants, events and balances are fictional**.

## Before you start

1. Start `python server.py` (or open the published Render URL).
2. Open the app and choose **Platform Admin** in the persona selector.
3. If you have already explored the simulator, click **Reset my workspace** so the scenarios begin in known states.
4. A persona switch is deliberately unauthenticated for ease of demo; authorization is enforced in the server-side simulator, but real IAM is not present.

## Scenario A: Clean employer payroll → simulated ledger

**Business intent:** reconcile payroll deductions and employee/employer contributions before they are reflected in a fictional participant ledger.

1. Switch to **Payroll Specialist · Cedar Arc**.
2. Open **Payroll**, locate batch `PAY-6001`, and choose **Validate payroll**.
3. Inspect the computed amounts, validation evidence and new `validated` status.
4. Switch to **Operations Analyst**. Open `PAY-6001`, then **Post fictional contributions**.
5. Check the **Contribution ledger** and activity log. Attempt to post a second time; verify that posting is rejected.

**Technical proof:** server-side role checks, batch-state guards, amount reconciliation, audit append and idempotency controls. **No funds move**.

## Scenario B: Exception remediation → mandatory revalidation

**Business intent:** prevent incorrect contributions from being posted when payroll remittance does not match calculated obligations.

1. Switch to **Operations Analyst**.
2. Validate `PAY-6003`; inspect the `REMITTANCE_MISMATCH` exception.
3. Open the **Exception workbench**, select the batch, and use **Reconcile remittance**.
4. Return to payroll, **Validate payroll** again, and post only after validation succeeds.
5. Inspect the audit event for the repair and posting.

**Technical proof:** blocked transition, controlled remediation, revalidation gate, and observable outcome.

## Scenario C: Unknown participant and duplicate ingestion

1. Validate `PAY-6002`. Confirm `UNKNOWN_PARTICIPANT` and mismatch errors.
2. Use the exception workbench's unmatched-line repair; revalidate before posting.
3. Validate `PAY-6004`. Confirm that a repeated external payroll run ID is rejected.

**Technical proof:** master-data validation and replay/deduplication controls. In a real environment, excluded deductions would require a controlled investigation and documented financial disposition.

## Scenario D: Role-scoped onboarding

1. Select **Employer Administrator · Cedar Arc** and inspect which employers and menu actions are accessible.
2. Switch to **Platform Admin** or **Operations Analyst** to see cross-employer views.
3. For **Blue Mesa Kitchens (EMP-104)**, advance the plan from `draft` through `configured` to `live` using the correct personas.
4. Attempt an unsupported transition or a transition with the wrong persona; confirm the refusal.

**Technical proof:** tenant-aware reads, workflow gates, staged approvals.

## Scenario E: Employee election and human review

1. Select **Employee · Maya Chen**.
2. Change the employee contribution election. Previously processed batches are unchanged.
3. Submit a fictional distribution inquiry.
4. Switch to **Operations Analyst** and review the inquiry. There is deliberately **no approval for actual distribution or money movement**.

**Technical proof:** employee-scoped access, forward-effective configuration, human-in-the-loop review.

## Scenario F: QA and architecture

1. Select **Platform Admin** and open **Test bench**.
2. Run all 18 checks and review the evidence by category. Failures are visible rather than silently replaced with success states.
3. Examine the architecture/technical-context pages for UI → API → domain-engine → audit dataflow and the production integration gaps.
4. Run `python -m unittest discover -s tests -v` to execute the 21 independent Python test cases.
5. Reset your session and repeat scenarios A–E if desired.

## Architectural decisions to discuss in an FDE interview

| Decision | Implemented demonstration | Production adaptation |
|---|---|---|
| Role and tenant permissions | Synthetic personas and engine-side checks | OIDC, MFA, organization memberships, tenant isolation and access review |
| Payroll integration | Deterministic CSV batches and validations | Authenticated provider adapters, webhook retries, reconciliation and SFTP/API controls |
| Financial posting | In-memory fictional ledger with double-post prevention | Durable double-entry ledger, settlement/custody integrations, transaction reconciliation |
| Workflow orchestration | Explicit transition guards and audit events | Durable queue, retries, compensating actions, operator approvals |
| Data storage | Per-browser temporary session | Encrypted durable database, retention and privacy controls |
| Quality and observability | Named on-demand bench tests and Python unittest suite | CI/CD gates, contract/performance/security tests, monitoring, incident response |

## Constraints and limitations

This application is **not associated with any real retirement-plan provider** and is **not ready to process real payroll or retirement assets**. It is a reproducible technical and workflow case study. All demo balances and events are invented. The self-contained `preview.html` runs a separate client-side simulation; use the deployed Python service for backend authorization evidence.
