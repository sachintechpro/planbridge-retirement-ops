/* PlanBridge contextual chat guide: local, deterministic, read-only explanations. */
(() => {
  'use strict';
  const LABELS = {overview:'Overview',employers:'Employer plans',participants:'Participants',payroll:'Payroll integration',exceptions:'Exception workbench',ledger:'Contribution ledger',requests:'Distributions',architecture:'Architecture & intent',quality:'Test bench'};
  const PAGES = {
    overview: {
      intro:'Trace the workflow from employer setup through participant elections, payroll validation, and ledger posting.',
      how:'Start with Payroll, validate PAY-6001 as Payroll Specialist, then switch to Operations Analyst and post it. Open Contribution ledger to see the allocation evidence. For a negative path, validate PAY-6003 and investigate the exception.',
      fields:'Plans in scope counts visible employer sponsors. Participants counts eligible synthetic plan members. Payroll files groups pay runs across states. Open exceptions counts unresolved cases. The value stream connects each stage.',
      proof:'The Python workflow engine shares in-memory state between screens within one visitor session; server-side checks control actions and create audit events.',
      prompts:['Explain these numbers','Walk me through a demo','What happens when payroll fails','What technology is used']
    },
    employers: {
      intro:'Understand the plan sponsor, setup fields, and the guarded draft → configured → live lifecycle.',
      how:'Select Blue Mesa Kitchens (EMP-104). Move draft to configured using a permitted sponsor or operations persona. Only Operations Analyst or Platform Admin can authorize configured → live.',
      fields:'Plan type identifies the retirement plan design; payroll provider is the fictional feed partner; participants counts members for this sponsor; employer match is its illustrative match rule; next pay date is its seeded payroll date; current owner is the responsible operations role.',
      proof:'Engine.advance_plan checks the selected employer, actor permissions, and allowed state transition. Successful changes generate PLAN_STATE_CHANGED evidence.',
      prompts:['Explain plan fields','Who can activate a plan?','What do draft and configured mean?','How is tenant access enforced?']
    },
    participants: {
      intro:'Explore employee elections, employer scoping, balances, and future-effective contribution changes.',
      how:'Switch to Employee · Maya Chen. On Participants, change the deferral percentage and Save election. This affects future unprocessed payroll calculations, not previously posted transactions.',
      fields:'Election and deferral are the employee contribution percentage; balance is an illustrative accumulated ledger amount; year-to-date deferral is the synthetic amount contributed so far; status describes the participant record.',
      proof:'The Python engine validates 0–50% elections in 0.1% increments, checks participant ownership, and emits ELECTION_CHANGED. The displayed persona is a demo switcher, not real login.',
      prompts:['What is deferral?','Explain balance and YTD','Why can’t I edit this participant?','How do elections affect payroll?']
    },
    payroll: {
      intro:'Inspect source payroll, amount reconciliation, validation controls, and protected posting states.',
      how:'Select PAY-6001, validate it as Payroll Specialist, then switch to Operations Analyst and post fictional contributions. Select PAY-6003 to test remittance mismatch and repair gating.',
      fields:'Calculated total is expected employee + employer allocation; remitted amount is the fictional source remittance; variance is remitted minus calculated. Employees is payroll line count; control is a validation/review flag; external ID identifies the source pay run.',
      proof:'POST /api/action validates identity mapping, duplicate run IDs, calculations, and review flags. Only a validated batch can be posted; posting emits ledger lines and audit evidence.',
      prompts:['What is variance?','Why is this batch blocked?','Explain validation controls','How do I post payroll?']
    },
    exceptions: {
      intro:'Diagnose failed payroll records, ownership, severity, and documented repairs.',
      how:'Validate PAY-6003 under Payroll to generate a mismatch. Return here as Operations, choose the blocked batch, Reconcile remittance, then return to Payroll and validate again before posting.',
      fields:'Case is a tracked exception record; category is its code; payroll links to the affected batch; severity is triage priority; status is open or resolved; owner identifies who should resolve it.',
      proof:'Engine.repair_batch records corrections and EXCEPTION_REMEDIATED evidence; it does not skip the validation gate or perform regulatory adjudication.',
      prompts:['What does severity mean?','Explain exception codes','How do I repair PAY-6003?','Why must I revalidate?']
    },
    ledger: {
      intro:'Understand the simulated allocation journal, its sources, and duplicate-posting protection.',
      how:'First validate and post PAY-6001 from Payroll. Return to Contribution ledger to inspect the employee and employer entries and source batch references.',
      fields:'Recorded contributions is the sum of simulated allocations; journal entries counts individual records; referenced batches counts posted payroll sources; external transfers is always $0 because this demo does not move funds.',
      proof:'Engine.post_batch enforces validated → posted and appends synthetic journal entries. Participant balances update once; repeat posting is rejected.',
      prompts:['What is a journal entry?','What do allocations mean?','Are funds actually moved?','How is double posting prevented?']
    },
    requests: {
      intro:'Explore an employee request routed to human review without initiating a real distribution.',
      how:'Switch to Employee · Maya Chen. Enter a requested amount and submit for human review. Switch to Operations Analyst to record the specialist review.',
      fields:'Requested amount is an illustrative inquiry amount; illustrative balance is a synthetic participant value; needs_review means the request awaits human action; reviewed means the review was recorded, not that money was paid.',
      proof:'The Python engine checks participant ownership and creates DISTRIBUTION_REQUESTED and DISTRIBUTION_REVIEWED events. No eligibility decision, tax calculation, or payment occurs.',
      prompts:['What is needs_review?','How do I submit a request?','Does this send money?','Who can review requests?']
    },
    architecture: {
      intro:'See how the interface, Python API, workflow engine, data fixtures, and controls fit together.',
      how:'Read Logical architecture and Representative API, then test a payroll action. The browser calls a Python server; engine.py enforces workflow rules; quality.py runs independent checks.',
      fields:'The browser is HTML/CSS/JavaScript. The server uses Python standard library HTTP endpoints. CSV fixtures create employers, participants, and payroll runs. Session state is isolated in memory and is not durable production storage.',
      proof:'The demo models integration and Guidewire-like workflow ideas, but has no live payroll adapter, real IAM/OIDC, external custodian, database, or Guidewire integration.',
      prompts:['Explain the technology stack','What does /api/action do?','What is simulated vs real?','What would production need?']
    },
    quality: {
      intro:'Run deterministic checks and understand the types of release evidence.',
      how:'Select Run all 18 checks. Inspect the case names, PASS/FAIL results and evidence. Checks create fresh engine instances and do not change your current scenario.',
      fields:'Runnable checks is the fixed suite size; executed counts checks in the latest run; passed and failed summarize results. Unit, integration, E2E, RBAC, security, and UAT group the scenarios.',
      proof:'POST /api/tests calls quality.py. Additional Python unit and workflow checks run during the Render build. The displayed evidence is generated by execution, not a fabricated test report.',
      prompts:['How do I run tests?','Explain Unit vs SIT vs UAT','What does RBAC cover?','Do tests affect my data?']
    }
  };

  /* Terms are based on the UI/engine. No external model or unverified compliance claims. */
  const TERMS = [
    ['remittance mismatch','The fictional remitted amount does not equal the recalculated employee and employer contributions. PAY-6003 starts $125 short; Operations can reconcile and must revalidate.'],
    ['variance','Variance = remitted amount minus calculated total. A negative value indicates a shortfall; a nonzero mismatch prevents posting until corrected and validated.'],
    ['calculated total','The server recalculates expected payroll contributions using eligible wages, each participant’s deferral election, and the illustrative employer match.'],
    ['remitted amount','The amount reported as paid by the fictional payroll source. It must reconcile with the calculated total before a batch can be posted.'],
    ['remitted','The fictional payroll source remittance amount, which is compared against expected employee and employer contributions.'],
    ['eligible wages','The seeded compensation amount on a payroll line used for the participant contribution calculation.'],
    ['match rule','This simulator uses an illustrative employer match of 50% on the first 4% of eligible wages contributed by an employee.'],
    ['employer match','A simulated employer contribution in addition to the employee’s deferral. This is a demonstration formula, not a universal plan rule.'],
    ['deferral','The percentage of eligible pay an employee elects to contribute. In this demo it is 0–50%, in 0.1% steps, and changes apply to future unprocessed payroll.'],
    ['ytd deferral','Year-to-date employee deferrals recorded in the synthetic participant data. They are not current real retirement balances.'],
    ['year-to-date deferral','The synthetic total of employee elective contributions so far this year. It does not represent a real custodial account.'],
    ['balance','An illustrative participant balance held in session state. Successful posting can increase it; no bank or custodian is connected.'],
    ['election','An employee’s chosen payroll contribution percentage. An election change is audited and takes effect only on future unprocessed payroll.'],
    ['participant mapping','A control ensuring payroll participant IDs belong to the correct employer and map to seeded member records.'],
    ['participant id','The synthetic key identifying a plan participant. The engine checks identity and employer relationships during processing.'],
    ['external run id','The payroll provider’s reference for a pay run. Reusing an already processed ID is blocked to help prevent duplicate posting.'],
    ['external id','A fictional source-system identifier used for reconciliation and duplicate detection.'],
    ['idempotency','A safeguard so retrying the same payroll posting cannot create duplicate journal records or balance increases.'],
    ['duplicate','PAY-6004 demonstrates a duplicate external run ID. The workflow should reject repeated processing rather than create duplicate contributions.'],
    ['validation controls','Payroll checks include participant mapping, unique run identity, contribution reconciliation, simplified deferral screening, and timing review flags.'],
    ['pay date','The illustrative date assigned to the pay run; it is shown for tracing the source and contribution timeline.'],
    ['payroll provider','A fictional source partner from which payroll data would be ingested in a production integration. This app does not connect to a real provider.'],
    ['plan type','The configured retirement plan category for the fictional employer, such as 401(k) or 403(b).'],
    ['next pay date','The next illustrative payroll date in the seeded employer record.'],
    ['current owner','The operations role accountable for progressing the employer onboarding or case workflow.'],
    ['employee','A fictional plan participant. Employees can update their own deferrals and submit review requests, subject to demo role restrictions.'],
    ['employer','The fictional plan sponsor and tenant. Plan and participant data are scoped by employer in the Python engine.'],
    ['participant','A synthetic plan member identified by an employer and participant ID. Employee self-service is scoped to the selected member.'],
    ['draft','An employer plan setup state before configuration is completed. It cannot jump directly to live.'],
    ['configured','An intermediate plan state after setup and mapping; Operations approval is still needed to mark it live.'],
    ['live','For employer plans, a state after Operations authorization. For participant/batch badges, read the status in the corresponding workflow context.'],
    ['received','The payroll batch was ingested into the simulation but has not passed validation.'],
    ['validated','The payroll batch passed checks and is eligible for posting by an authorized operations role.'],
    ['posted','The batch was recorded into the synthetic journal. Repeating posting is prohibited. No real money was moved.'],
    ['exception','A validation failure or flagged case requiring investigation or review. A blocked payroll batch must be repaired and revalidated.'],
    ['case','A tracked exception or request with an identifier, status, and follow-up responsibility.'],
    ['category','The machine-readable type of exception, such as REMITTANCE_MISMATCH or UNKNOWN_PARTICIPANT.'],
    ['severity','A triage priority for an exception case; it is not an external incident-management integration.'],
    ['owner','The role responsible for reviewing or resolving an exception, request, or onboarding transition.'],
    ['status','The workflow state returned by the Python engine. The interface does not arbitrarily skip required transitions.'],
    ['state','The server-owned workflow state, such as received, validated, exception, posted or draft, configured, live.'],
    ['allocation','One employee or employer contribution journal item attributed to a participant and source payroll batch.'],
    ['journal entry','An append-only synthetic record for an employee or employer contribution, with source batch, participant, date, and amount.'],
    ['ledger','The simulator’s contribution journal created after successful posting. It does not represent a real trustee account or payments system.'],
    ['referenced batches','The distinct posted payroll batches represented in the synthetic contribution ledger.'],
    ['external transfers','Always $0 here: there are no ACH transfers, actual payouts, custodian transactions or investment execution.'],
    ['requested amount','The fictional amount entered for a distribution inquiry. An inquiry is reviewed, not paid.'],
    ['needs_review','A request awaits an authorized operations specialist to record a human review.'],
    ['reviewed','The specialist recorded review of an inquiry. It is not an eligibility approval or funds transfer.'],
    ['distribution','A participant request to ask about withdrawing funds; this demo logs an inquiry and review only.'],
    ['api/action','The POST endpoint for controlled operations such as validate_batch, post_batch, advance_plan, and distribution review. The Python engine checks authorization.'],
    ['api/state','A GET endpoint returning this visitor session’s role-scoped synthetic application state and CSRF token.'],
    ['api/tests','The POST endpoint that executes the 18 isolated checks in quality.py and returns the test results.'],
    ['api/actor','The POST endpoint for switching the simulated persona. This is not production authentication.'],
    ['api/reset','The POST endpoint that restores the visitor’s synthetic workflow state.'],
    ['csrf','A request token used by the demo to protect state-changing API calls. It is not a substitute for production login or security controls.'],
    ['rbac','Role-based access control: which demo actor can view or change specific data. Permissions are checked in the Python engine.'],
    ['tenant isolation','Employer-by-employer data scoping enforced in the engine for simulated roles. It is not a production multi-tenant identity or database system.'],
    ['oidc','OpenID Connect is a standard production identity layer. PlanBridge does not integrate a real OIDC provider; its persona switcher is open for demonstration.'],
    ['audit','The engine records named workflow events and returns evidence for changes such as ELECTION_CHANGED or CONTRIBUTIONS_POSTED.'],
    ['csv','Seeded CSV fixtures supply synthetic employers, participants, and payroll data. Each browser session receives its own in-memory copy.'],
    ['python','Python standard-library HTTP server and workflow engine power the API, validation, state transitions, and test suite.'],
    ['javascript','Vanilla JavaScript renders the interface, calls the Python API, and updates the page. The chat guide uses built-in local explanations.'],
    ['technology','The app uses HTML/CSS/JavaScript, a Python standard-library HTTP API, an in-memory workflow engine, seeded CSV data, and runnable Python tests on Render. No LLM or external payroll connection is used.'],
    ['guidewire','PlanBridge is a retirement operations simulation, not a Guidewire application. Its state-machine, approvals, APIs, and audit patterns are conceptually comparable, but no InsuranceSuite integration is implemented.'],
    ['production','A production platform would need authenticated IAM/OIDC, persistent tenant-isolated storage, secure payroll integrations, durable idempotency, monitoring, and compliance/legal review.'],
    ['test bench','The Test bench runs 18 deterministic checks on fresh engine instances and displays result evidence without altering the visitor’s live scenario.'],
    ['unit test','Unit tests focus on individual engine rules and calculations, such as matching, validation, and contribution arithmetic.'],
    ['integration','Integration checks verify data relationships and cross-component processes such as sponsor/participant mapping, payload reconciliation, and event outcomes.'],
    ['e2e','End-to-end tests cover multi-step journeys, such as validate → post → ledger and failure → repair → revalidate.'],
    ['sit','System integration testing checks interactions across systems or components, including payroll intake, engine validation, and posting behavior.'],
    ['uat','User acceptance testing evaluates whether representative sponsor, employee and operations scenarios satisfy the intended business workflows.'],
    ['quality','Quality evidence includes executable Python checks, workflow-negative cases, role scoping, idempotency tests and deployment smoke checks.']
  ];
  const normalize = text => String(text || '').toLowerCase().replace(/[_–—/-]/g, ' ').replace(/[^a-z0-9% ]/g, ' ').replace(/\s+/g, ' ').trim();
  const fmt = value => '$' + Number(value || 0).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
  const topicList = TERMS.map(([term,answer]) => ({term,normalized:normalize(term),answer})).sort((a,b)=>b.normalized.length-a.normalized.length);
  const local = {page:'overview',actor:{label:'Platform Admin'},batch:null,employer:null,person:null,stats:null};
  let opened=false;
  let messages=0;

  function pageSpec(){return PAGES[local.page] || PAGES.overview;}
  function introText(){return LABELS[local.page]+' · '+(local.actor?.label || 'Current persona')+'. '+pageSpec().intro;}
  function selectedValue(){
    if (local.page==='payroll' && local.batch) {
      const b=local.batch;return 'Selected '+b.id+' is '+b.state+'. Expected '+fmt(b.expected_total)+', remitted '+fmt(b.remitted_total)+', variance '+fmt(Number(b.remitted_total || 0)-Number(b.expected_total || 0))+'.';
    }
    if (local.page==='employers' && local.employer) return 'Selected '+local.employer.name+' ('+local.employer.id+') is '+local.employer.status+'.';
    if (local.page==='participants' && local.person) return 'Selected '+local.person.name+' ('+local.person.id+') has a '+local.person.deferral_pct+'% deferral election.';
    return '';
  }

  function matchTerm(q){
    const n=' '+normalize(q)+' ';
    for (const entry of topicList) {
      if (n.includes(' '+entry.normalized+' ')) return entry.answer;
    }
    return null;
  }
  function answer(question){
    const raw=String(question||'').trim().slice(0,240);
    if(!raw) return 'Ask about a field, business rule, workflow action, or technology on this page.';
    const q=normalize(raw),p=pageSpec();
    if(/\b(hello|hi|hey)\b/.test(q) && q.length<15) return introText();
    if(/(difference|compare|versus|vs)/.test(q) && /remit/.test(q) && /(calculat|expect)/.test(q)) return TERMS[1][1]+' '+selectedValue();
    if(/(why|reason).*(block|fail|error|exception)/.test(q) && local.page==='payroll') {
      if(local.batch?.state==='exception')return 'This batch is in exception state because its validation found a blocking issue. Inspect the Exception workbench, repair as Operations, then validate again. '+selectedValue();
      return 'Only batches passing mapping, duplicate, reconciliation, and review controls can post. '+selectedValue();
    }
    if(/(current|selected|this|my).*(batch|payroll|employer|plan|participant|status|variance)/.test(q) && selectedValue()) return selectedValue()+' Ask about its status or the next allowed step.';
    if(/(explain|what|meaning|mean|tell).*(field|parameter|number|dashboard|screen|page|metric|column)/.test(q)) return p.fields;
    if(/\bpay\s*-?\s*600[1-5]\b/.test(q)) {
      const id=(q.match(/pay\s*-?\s*600[1-5]/)||[''])[0].replace(/\s/g,'').toUpperCase().replace('PAY','PAY-');
      const cases={'PAY-6001':'Clean payroll: validate with Payroll Specialist, then post with Operations.','PAY-6002':'Unknown participant and remittance issues: validate to create an exception, then remediate and revalidate.','PAY-6003':'Fictional remittance is $125 short: reconcile under Exceptions, then validate again.','PAY-6004':'Duplicate external payroll run ID: the engine must reject replay after its source run was processed.','PAY-6005':'Timeliness review flag: Operations may record acknowledgment, but this does not determine regulatory compliance.'};
      return (cases[id]||'Payroll fixture.')+' '+(local.batch?.id===id?selectedValue():'');
    }
    if(/(how|why).*(role|permission|tenant|security|identity|access)/.test(q)) return p.proof+' '+TERMS.find(x=>x[0]==='rbac')[1];
    if(/(technology|tech stack|framework|python|javascript|backend|frontend|api|architecture)/.test(q) && /(what|which|how|stack|used|built)/.test(q)) return p.proof+' '+TERMS.find(x=>x[0]==='technology')[1];
    if(/(what|why).*(this page|this screen|purpose|business)/.test(q)) return p.intro;
    if(/(production|real world|real integration|simulat)/.test(q)) return TERMS.find(x=>x[0]==='production')[1]+' '+TERMS.find(x=>x[0]==='guidewire')[1];
    const term=matchTerm(raw);
    if(term)return term+(selectedValue() && /(variance|calculated total|remitted amount|status|state)/.test(q)?' '+selectedValue():'');
    if(/(how|walk|steps|try|demo|next|start|use this|what should i do)/.test(q)) return p.how;
    const help=window.PlanBridgeHelp?.pageHelp?.[local.page];
    if(help && /(business intent|technical proof|guidewire parallel|how to demo|integration contract|backend boundary)/.test(q)){
      const card=help.cards.find(([name])=>q.includes(normalize(name)));
      if(card)return card[1];
    }
    const app=document.getElementById('app');
    const labels=[...app?.querySelectorAll('.definition dt,.stat-label,.data-table th,.field label')||[]].map(el=>el.textContent.trim().replace(/\s*\?$/, '')).filter(Boolean);
    const unique=[...new Set(labels)].slice(0,14);
    const termFromVisible=unique.filter(x=>normalize(q).includes(normalize(x))).sort((a,b)=>b.length-a.length)[0];
    if(termFromVisible)return '“'+termFromVisible+'” is a field on '+LABELS[local.page]+'. '+p.fields+' For a specific rule, ask “How do I use this page?”';
    return 'I do not have a verified answer to that wording in this demo guide. On '+LABELS[local.page]+', try: '+p.prompts.slice(0,3).join(' · ')+'.';
  }

  const button=document.createElement('button');
  button.type='button';button.id='pb-guide-toggle';button.className='pb-guide-toggle';
  button.setAttribute('aria-controls','pb-guide-panel');button.setAttribute('aria-expanded','false');
  button.textContent='?  Ask this page';
  const panel=document.createElement('section');
  panel.id='pb-guide-panel';panel.className='pb-guide-panel';panel.hidden=true;
  panel.setAttribute('role','dialog');panel.setAttribute('aria-label','PlanBridge page guide');
  panel.innerHTML='<header class="pb-guide-header"><div><strong>PlanBridge Page Guide</strong><span>Clear answers from this application</span></div><button type="button" id="pb-guide-close" aria-label="Close page guide">×</button></header>'+
    '<div class="pb-guide-context" id="pb-guide-context"></div>'+
    '<div class="pb-guide-messages" id="pb-guide-messages" role="log" aria-label="Guide conversation" aria-live="polite"></div>'+
    '<div class="pb-guide-prompts" id="pb-guide-prompts" aria-label="Suggested questions"></div>'+
    '<form id="pb-guide-form" class="pb-guide-form"><label class="pb-guide-sr" for="pb-guide-input">Ask about this page</label><input id="pb-guide-input" type="text" maxlength="240" autocomplete="off" placeholder="Ask about a field or next step…" required><button type="submit">Ask</button></form>'+
    '<p class="pb-guide-note">Built-in contextual help · No outside AI service or data sharing</p>';
  document.body.append(button,panel);
  const log=panel.querySelector('#pb-guide-messages');
  const prompts=panel.querySelector('#pb-guide-prompts');
  const context=panel.querySelector('#pb-guide-context');
  const input=panel.querySelector('#pb-guide-input');
  const closeBtn=panel.querySelector('#pb-guide-close');
  const addMessage=(who,text)=>{
    const el=document.createElement('p');
    el.className='pb-guide-message '+(who==='assistant'?'pb-guide-answer':'pb-guide-question');
    el.textContent=text;
    log.append(el);
    messages++;
    while(messages>14){log.firstElementChild?.remove();messages--;}
    log.scrollTop=log.scrollHeight;
  };
  function updatePrompts(){
    prompts.replaceChildren();
    pageSpec().prompts.forEach(q=>{
      const btn=document.createElement('button');btn.type='button';btn.textContent=q;
      btn.addEventListener('click',()=>ask(q));
      prompts.append(btn);
    });
  }
  function updateContext(){
    context.textContent='On this page: '+(LABELS[local.page] || 'Overview')+' · '+(local.actor?.label || 'Current persona');
    updatePrompts();
  }
  function ask(q){
    addMessage('visitor',q);
    addMessage('assistant',answer(q));
  }
  function toggle(open){
    opened=!!open;
    panel.hidden=!opened;
    button.setAttribute('aria-expanded',String(opened));
    button.textContent=opened?'×  Close guide':'?  Ask this page';
    if(opened){
      if(!messages)addMessage('assistant',introText()+' Choose a suggested question or type your own.');
      updateContext();input.focus();
    }else button.focus();
  }
  button.addEventListener('click',()=>toggle(!opened));
  closeBtn.addEventListener('click',()=>toggle(false));
  panel.querySelector('#pb-guide-form').addEventListener('submit',e=>{
    e.preventDefault();const q=input.value.trim();if(!q)return;
    input.value='';ask(q);input.focus();
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&opened){e.preventDefault();toggle(false);}});
  window.PlanBridgeChat={
    setContext(payload){
      const previous=local.page;
      Object.assign(local,payload||{});
      if(previous!==local.page){
        log.replaceChildren();messages=0;
        if(opened)addMessage('assistant','Now viewing '+(LABELS[local.page]||'Overview')+'. '+pageSpec().intro);
      }
      updateContext();
    },
    answer
  };
  updateContext();
})();