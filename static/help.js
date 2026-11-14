/* Contextual FDE and Guidewire-reference learning layer. This demo does NOT integrate with Guidewire. */
(() => {
  const pageHelp = {
    overview: {
      summary: 'Understand the cross-functional value stream before choosing a persona or running a scenario.',
      cards: [
        ['Business intent', 'Follow the employer → employee → payroll → operations → ledger handoffs. Every action should change the shared workflow rather than just a dashboard number.'],
        ['Technical proof', 'Each browser session has isolated synthetic state. The Python API enforces permissions, allowed state transitions, and event evidence on mutations.'],
        ['Guidewire parallel', 'Comparable orchestration challenge: PolicyCenter policy transactions can generate downstream billing requests into BillingCenter. PlanBridge is a separate retirement-domain simulation, not a Guidewire connector.']
      ]
    },
    employers: {
      summary: 'Model sponsor onboarding and controlled operational activation, rather than allowing direct jumps between lifecycle stages.',
      cards: [
        ['How to demo', 'Select Blue Mesa Kitchens (EMP-104). A sponsor can configure a draft plan; Operations must separately authorize the configured → live transition.'],
        ['Backend boundary', 'POST /api/action with advance_plan checks role, employer scope, current status and the permitted next state. The UI does not grant authorization.'],
        ['Guidewire parallel', 'Analogous to controlled PolicyCenter policy-job transitions: validated configuration, permitted actor, a defined next state, and an auditable transaction. Retirement-plan states are not Guidewire policy states.']
      ]
    },
    participants: {
      summary: 'See how role-scoped participant profiles and deferral elections influence later payroll without rewriting posted financial history.',
      cards: [
        ['How to demo', 'Switch to Employee · Maya Chen. Update the deferral percentage; confirm the change takes effect in a future unprocessed payroll calculation.'],
        ['Data and authorization', 'The engine validates percentages and participant identity, limits an employee to their own record, and writes ELECTION_CHANGED audit evidence.'],
        ['Guidewire parallel', 'A similar API design principle applies to PolicyCenter endorsements: manage requested changes through an authorized business transaction, preserving effective dates and existing history. This is conceptual, not shared schema.']
      ]
    },
    payroll: {
      summary: 'The core integration flow: ingest external payroll IDs, validate source data, reconcile totals, and post only an approved batch.',
      cards: [
        ['How to demo', 'Select PAY-6001. Payroll Specialist validates; Operations Analyst posts. Then attempt a second posting to see replay protection.'],
        ['Integration contract', 'POST validate_batch evaluates participant references, unique pay runs, deferral amounts, remittance equality, and timing flags before a validated state is assigned.'],
        ['Guidewire parallel', 'BillingCenter deals with insurance charges, invoices and payments, while this screen reconciles retirement contributions. Both need reliable external identifiers, reconciliation, and controlled financial posting; these are distinct domain entities.']
      ]
    },
    exceptions: {
      summary: 'Investigate invalid payroll records with explicit ownership, repeatable remediation, and mandatory revalidation.',
      cards: [
        ['How to demo', 'Validate PAY-6003 to reveal a $125 remittance mismatch. Use Operations to reconcile, then validate again before posting.'],
        ['Failure contract', 'Exception cases have codes, severities and assigned owners. Repairs produce audit evidence and never skip the validation gate.'],
        ['Guidewire parallel', 'Conceptually similar to ClaimCenter work queues and activities: a case has an accountable owner, reason, resolution evidence, and a tracked outcome. These are payroll exceptions, not claims.']
      ]
    },
    ledger: {
      summary: 'Trace synthetic contributions from an accepted payroll batch into participant-level employee/employer entries.',
      cards: [
        ['How to demo', 'Validate and post PAY-6001, open the ledger and inspect both allocation types, batch references and audit events.'],
        ['Financial control', 'Posting requires a validated batch and rechecks its contents. Duplicate posting is rejected. This records simulated ledger rows; no bank transfer occurs.'],
        ['Guidewire parallel', 'Like BillingCenter financial traceability, downstream accounting records need consistent source references, reconcilable values, and error handling. Retirement contributions are not insurance premiums.']
      ]
    },
    requests: {
      summary: 'Demonstrate employee self-service with human-review gates and a clear boundary between review and disbursement.',
      cards: [
        ['How to demo', 'As Employee · Maya Chen, submit a fictional distribution inquiry. Switch to Operations to record its review.'],
        ['Backend boundary', 'request_distribution validates the participant, the illustrative available amount, and access. review_distribution changes a review status only; it does not move funds.'],
        ['Guidewire parallel', 'A case lifecycle resembles ClaimCenter activity/approval patterns in a broad architectural sense: an incoming request is reviewed by an authorized operator. PlanBridge does not execute Guidewire claim payments.']
      ]
    },
    architecture: {
      summary: 'Map the FDE problem statement to components, API boundaries, integration contracts, state enforcement, and production gaps.',
      cards: [
        ['Integration shape', 'The browser calls a Python HTTP API. A workflow engine owns state, authorization rules, reconciliation, audit events, and simulated tenant scoping.'],
        ['Production extensions', 'Real adoption would need external payroll adapters, OIDC, tenant data persistence, durable idempotency, reconciliation with trusted custodians, monitoring, and compliance review.'],
        ['Guidewire orientation', 'InsuranceSuite Cloud API is REST-based and supports data access and actions in PolicyCenter, BillingCenter and ClaimCenter. Here only comparable API/workflow principles are shown; no Guidewire SDK, API, or real insurer data is connected.']
      ]
    },
    quality: {
      summary: 'Use executable checks to prove state management, cross-tenant access rules, financial controls, and negative paths.',
      cards: [
        ['How to demo', 'Run all 18 checks and inspect each PASS/FAIL result and its evidence. Tests run on fresh engine instances, leaving your working scenario unchanged.'],
        ['Test coverage', 'The backend also includes Python tests for arithmetic, validation, lifecycle gates, RBAC, exception remediation, replay prevention, and production-like error paths.'],
        ['Guidewire parallel', 'Similar test strategy for InsuranceSuite integrations: API contracts, SIT across PolicyCenter/BillingCenter/ClaimCenter, negative cases, authorization, reconciliations and end-to-end business UAT. These demo tests do not execute against Guidewire.']
      ]
    }
  };
  const tableHelp = {
    'status': 'A lifecycle state returned by the Python engine, not an arbitrary UI flag. Transitions require role and workflow checks.',
    'state': 'The source-of-truth workflow state. Failed validation prevents promotion to a postable state.',
    'batch': 'A fictional payroll file or pay run; its external reference is checked for replay or duplicate processing.',
    'employer': 'An isolated fictional plan sponsor (tenant). The engine scopes data and allowed actions by role and employer.',
    'participant': 'A plan member. The engine checks whether the participant belongs to the selected sponsor.',
    'remitted': 'The amount provided by the fictional payroll source; it must reconcile to expected employee and employer allocations.',
    'expected': 'Recalculated contribution total from payroll lines and current participant elections.',
    'amount': 'A simulation amount only. No external funds are transferred by PlanBridge.',
    'exception': 'A blocking or reviewable condition with an assigned owner and auditable remediation path.',
    'owner': 'Accountable operations role responsible for progressing an exception or review.',
    'severity': 'A triage indicator describing impact and urgency; not a production incident management integration.',
    'deferral': 'Employee payroll contribution election; updates apply to future unprocessed payroll in this simulation.',
    'ledger': 'Synthetic allocation journal entries created only after a validated batch is posted.',
    'date': 'Illustrative transaction or effective date from the seeded scenario.'
  };
  const escapeHTML = v => String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const guide = key => {
    const p=pageHelp[key]||pageHelp.overview;
    return `<section class="context-guide" aria-label="Context help and technical explanations">
      <div class="context-guide-intro"><span class="context-mark" aria-hidden="true">?</span>
        <div><h2 class="context-guide-title">On this page · Business and technical guide</h2>
        <p class="context-guide-subtitle">${escapeHTML(p.summary)}</p></div></div>
      <div class="context-guide-grid">${p.cards.map(([h,b],i)=>`<details class="context-topic"><summary>${escapeHTML(h)}</summary><div class="context-topic-content">${escapeHTML(b)}</div></details>`).join('')}</div>
      <div class="context-guide-note">Guidewire comparisons are architectural learning references only. PlanBridge is a fictional retirement operations application and does not connect to InsuranceSuite.</div>
    </section>`;
  };
  const render = key => {
    const app=document.getElementById('app');
    if(!app)return;
    const head=app.querySelector('.head,.hero');
    if(head)head.insertAdjacentHTML('afterend',guide(key));else app.insertAdjacentHTML('afterbegin',guide(key));
    app.querySelectorAll('.data-table th').forEach(th=>{
      const txt=(th.textContent||'').toLowerCase();
      const hint=Object.entries(tableHelp).find(([word])=>txt.includes(word));
      if(!hint || th.querySelector('.help-inline'))return;
      th.insertAdjacentHTML('beforeend',`<details class="help-inline"><summary aria-label="Explain ${escapeHTML(th.textContent.trim())}">?</summary><span class="help-inline-body">${escapeHTML(hint[1])}</span></details>`);
    });
  };
  function closeMenu(){
    const sidebar=document.getElementById('sidebar'),scrim=document.getElementById('nav-scrim'),toggle=document.getElementById('menu-toggle');
    if(sidebar)sidebar.classList.remove('open');
    if(scrim)scrim.hidden=true;
    if(toggle){toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label','Open navigation');}
    document.body.style.overflow='';
  }
  function toggleMenu(){
    const sidebar=document.getElementById('sidebar'),scrim=document.getElementById('nav-scrim'),toggle=document.getElementById('menu-toggle');
    if(!sidebar)return;
    const open=!sidebar.classList.contains('open');
    sidebar.classList.toggle('open',open);
    if(scrim)scrim.hidden=!open;
    if(toggle){toggle.setAttribute('aria-expanded',String(open));toggle.setAttribute('aria-label',open?'Close navigation':'Open navigation');}
    document.body.style.overflow=open?'hidden':'';
    if(open)sidebar.querySelector('.nav-item')?.focus();
    else toggle?.focus();
  }
  document.addEventListener('click',e=>{
    if(e.target.id==='nav-scrim')closeMenu();
    if(e.target.closest('.context-topic summary')){
      const target=e.target.closest('details');
      document.querySelectorAll('.context-topic[open]').forEach(d=>{if(d!==target)d.open=false;});
    }
    if(e.target.closest('.help-inline summary')){
      const target=e.target.closest('details');
      document.querySelectorAll('.help-inline[open]').forEach(d=>{if(d!==target)d.open=false;});
    }
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeMenu();document.querySelectorAll('.context-topic[open],.help-inline[open]').forEach(d=>d.open=false);}});
  window.PlanBridgeHelp={render,closeMenu,toggleMenu};
})();
