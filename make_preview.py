"""Build standalone, browser-only preview. Python backend remains authoritative."""
from pathlib import Path
from engine import Engine
from quality import run_checks
import json

ROOT=Path(__file__).parent
html=(ROOT/'static/index.html').read_text()
css=(ROOT/'static/styles.css').read_text()
js=(ROOT/'static/app.js').read_text()
js=js.replace('Run all 18 checks','Show baseline QA report')
js=js.replace('Test execution complete:', 'Baseline report loaded:')
base=Engine().snapshot()
qa=run_checks()
qa['execution']='Read-only baseline report: results captured from the Python engine. Open the server-hosted version to re-execute 18 tests.'
mock=r'''
// Browser-only preview transport. Full project uses the Python server, not this adapter.
(function(){
  const base = __STATE__;
  let DB=structuredClone(base),actor='platform',sequence=100;
  const QA=__QA__;
  const clone=x=>structuredClone(x);
  const getActor=()=>DB.actors.find(x=>x.id===actor);
  const rr=n=>Number(Number(n).toFixed(2));
  const bad=(msg,status=409)=>{let e=new Error(msg);e.status=status;throw e};
  const get=(kind,id)=>{let x=DB[kind].find(v=>v.id===id);if(!x)bad('Record not found',404);return x};
  const allow=(eid,roles)=>{let a=getActor();if(roles&&!roles.includes(a.role))bad('This persona is not permitted to perform this operation',403);if(eid&&['sponsor','payroll','participant'].includes(a.role)&&a.employer_id!==eid)bad('This persona does not have access to that employer',403)};
  const audit=(event,detail)=>DB.audit.unshift({id:`OFFLINE-${sequence++}`,time:new Date().toISOString(),actor,event,detail});
  const contribution=(wages,p)=>[rr(wages*p.deferral_pct/100),rr(wages*Math.min(p.deferral_pct,4)/200)];
  function analyze(b){let expected=0,errors=[];
    if(DB.batches.some(x=>x.id!==b.id&&x.external_id===b.external_id&&x.employer_id===b.employer_id&&['validated','posted'].includes(x.state)))errors.push(['DUPLICATE_BATCH','External payroll ID already processed']);
    let seen=new Set();for(let line of b.lines){let p=DB.people.find(x=>x.id===line.person_id&&x.employer_id===b.employer_id);if(!p){errors.push(['UNKNOWN_PARTICIPANT',`Employee ${line.person_id} cannot be matched`]);continue}if(seen.has(p.id)){errors.push(['DUPLICATE_LINE',`Duplicate ${p.id}`]);continue}seen.add(p.id);if(line.gross<=0){errors.push(['INVALID_GROSS',p.id]);continue}let [ee,er]=contribution(line.gross,p);if(p.ytd_deferral+ee>24500)errors.push(['DEFERRAL_REVIEW','Specialist review required']);expected+=ee+er}
    expected=rr(expected);if(Math.abs(expected-b.remitted_total)>.01)errors.push(['REMITTANCE_MISMATCH',`Expected ${expected.toFixed(2)}; received ${b.remitted_total.toFixed(2)}`]);if(b.flag==='timeliness_review')errors.push(['TIMELINESS_REVIEW','Specialist review required']);return {expected,errors};
  }
  function snapshot(){let a=getActor(),eid=a.employer_id,role=a.role;
    let employers=DB.employers.filter(e=>['platform','ops'].includes(role)||e.id===eid).map(clone);
    let people=DB.people.filter(p=>(['platform','ops'].includes(role)||p.employer_id===eid)&&(role!=='participant'||p.id===a.person_id)).map(clone);
    let batches=(role==='participant'?[]:DB.batches.filter(b=>['platform','ops'].includes(role)||b.employer_id===eid)).map(clone);
    batches.forEach(b=>{b.expected_total=analyze(b).expected;b.line_count=b.lines.length});
    let exceptions=DB.exceptions.filter(e=>['platform','ops'].includes(role)||(['sponsor','payroll'].includes(role)&&e.employer_id===eid)).map(clone);
    let ledger=DB.ledger.filter(l=>['platform','ops'].includes(role)||(role!=='participant'&&l.employer_id===eid)||(role==='participant'&&l.person_id===a.person_id)).map(clone);
    let requests=DB.requests.filter(x=>['platform','ops'].includes(role)||(role==='participant'&&x.person_id===a.person_id)||(role==='sponsor'&&x.employer_id===eid)).map(clone);
    let audit=role==='participant'?[]:DB.audit.filter(x=>['platform','ops'].includes(role)||x.detail.includes(eid)).slice(0,35).map(clone);
    return {actor:a,actors:DB.actors,employers,people,batches,exceptions,ledger,requests,audit,stats:{employers:employers.length,participants:people.length,batches:batches.length,exceptions:exceptions.filter(x=>x.status==='open').length,posted_batches:batches.filter(x=>x.state==='posted').length,ledger_total:rr(ledger.reduce((s,x)=>s+x.amount,0))}};
  }
  function action(p){let a=p.type, record;
    if(a==='validate_batch'){
      record=get('batches',p.id);allow(record.employer_id,['payroll','ops','platform']);if(!['received','exception'].includes(record.state))bad('Only received or exception batches can be validated');let x=analyze(record);
      if(x.errors.length){record.state='exception';for(let [code,description] of x.errors){if(!DB.exceptions.some(e=>e.batch_id===record.id&&e.code===code&&e.status==='open'))DB.exceptions.push({id:`EX-${1001+DB.exceptions.length}`,batch_id:record.id,employer_id:record.employer_id,code,description,status:'open',owner:'Operations',severity:['UNKNOWN_PARTICIPANT','REMITTANCE_MISMATCH','DEFERRAL_REVIEW'].includes(code)?'High':'Medium'})}audit('BATCH_REJECTED',`${record.employer_id} / ${record.id} failed ${x.errors.length} checks`);return {message:`Validation blocked: ${x.errors.length} issue(s) created`,evidence:{batch_id:record.id,expected_total:x.expected,errors:x.errors}}}
      record.state='validated';DB.exceptions.filter(e=>e.batch_id===record.id).forEach(e=>e.status='resolved');audit('BATCH_VALIDATED',`${record.employer_id} / ${record.id}`);return {message:'Payroll batch validated; Operations can now post it',evidence:{batch_id:record.id,amount:x.expected}};
    }
    if(a==='repair_batch'){
      record=get('batches',p.id);allow(record.employer_id,['ops','platform']);if(record.state!=='exception')bad('Repair requires an exception-state batch');
      if(p.repair==='reconcile_amount'){if(analyze(record).errors.some(([code])=>['UNKNOWN_PARTICIPANT','INVALID_GROSS','DUPLICATE_BATCH','DEFERRAL_REVIEW'].includes(code)))bad('Resolve blocking data issues first');record.remitted_total=analyze(record).expected}
      else if(p.repair==='remove_unmatched'){record.lines=record.lines.filter(l=>DB.people.some(per=>per.id===l.person_id&&per.employer_id===record.employer_id));record.remitted_total=analyze(record).expected}
      else if(p.repair==='new_external_id')record.external_id+=`-CORRECTED-${record.id}`;
      else if(p.repair==='acknowledge_timing')record.flag='review_acknowledged';
      else bad('Unknown repair action',400);
      audit('EXCEPTION_REMEDIATED',`${record.employer_id} / ${record.id} · ${p.repair}`);return {message:'Correction recorded. Re-run validation before posting.',evidence:{repair:p.repair,batch_id:record.id}};
    }
    if(a==='post_batch'){
      record=get('batches',p.id);allow(record.employer_id,['ops','platform']);if(record.state!=='validated')bad('Posting requires successful validation');let x=analyze(record);if(x.errors.length)bad('Batch changed since validation');let before=DB.ledger.length;for(let line of record.lines){let person=get('people',line.person_id);let [ee,er]=contribution(line.gross,person);for(let [kind,amount] of [['employee',ee],['employer',er]])DB.ledger.push({id:`L-${String(DB.ledger.length+1).padStart(5,'0')}`,batch_id:record.id,employer_id:record.employer_id,person_id:person.id,kind,amount,date:record.pay_date});person.balance=rr(person.balance+ee+er);person.ytd_deferral=rr(person.ytd_deferral+ee)}record.state='posted';audit('CONTRIBUTIONS_POSTED',`${record.employer_id} / ${record.id} · ${DB.ledger.length-before} entries`);return {message:'Fictional contributions posted to participant ledgers',evidence:{batch_id:record.id,entries:DB.ledger.slice(before),posted_total:x.expected,external_funds_moved:false}};
    }
    if(a==='set_deferral'){
      record=get('people',p.person_id);allow(record.employer_id,['participant','platform']);if(getActor().role==='participant'&&getActor().person_id!==record.id)bad('You can only edit your own election',403);let pct=Number(p.pct);if(!Number.isFinite(pct)||pct<0||pct>50||Math.abs(pct*10-Math.round(pct*10))>1e-6)bad('Election must be 0–50% in 0.1% steps',400);let old=record.deferral_pct;record.deferral_pct=pct;audit('ELECTION_CHANGED',`${record.employer_id} / ${record.id} ${old}% to ${pct}%`);return {message:'Election saved for the next unprocessed payroll',evidence:{old_pct:old,new_pct:pct,person_id:record.id}};
    }
    if(a==='advance_plan'){
      record=get('employers',p.id);allow(record.id,['sponsor','ops','platform']);let next={draft:'configured',configured:'live'}[record.status];if(!next)bad('Plan is already live');if(next==='live'&&getActor().role==='sponsor')bad('Operations approval required',403);let from=record.status;record.status=next;audit('PLAN_STATE_CHANGED',`${record.id} ${from} to ${next}`);return {message:`Plan moved from ${from} to ${next}`,evidence:{from,to:next}};
    }
    if(a==='request_distribution'){
      record=get('people',p.person_id);allow(record.employer_id,['participant','platform']);if(getActor().role==='participant'&&getActor().person_id!==record.id)bad('Not your account',403);let amount=Number(p.amount);if(!Number.isFinite(amount)||amount<=0||amount>record.balance)bad('Amount outside available illustrative balance',400);let r={id:`DIST-${String(DB.requests.length+1).padStart(4,'0')}`,person_id:record.id,employer_id:record.employer_id,amount,status:'needs_review',note:'Eligibility, tax, withholding, and plan terms require specialist assessment'};DB.requests.push(r);audit('DISTRIBUTION_REQUESTED',`${record.employer_id} / ${record.id}`);return {message:'Request submitted for specialist review; no funds moved',evidence:r};
    }
    if(a==='review_distribution'){
      record=get('requests',p.id);allow(record.employer_id,['ops','platform']);if(record.status!=='needs_review')bad('Already reviewed');record.status='reviewed_no_disbursement';audit('DISTRIBUTION_REVIEWED',`${record.employer_id} / ${record.id}`);return {message:'Review recorded. Disbursement not supported.',evidence:record};
    }
    bad('Unsupported operation',400);
  }
  window.fetch=async function(url,options={}){
    try{
      let data={};if(options.body)data=JSON.parse(options.body);
      let output;
      if(url==='/api/state')output={data:snapshot(),csrf:'preview-only'};
      else if(url==='/api/actor'){if(!DB.actors.some(a=>a.id===data.actor))bad('Unknown persona',400);actor=data.actor;output={message:'Persona switched',data:snapshot()}}
      else if(url==='/api/reset'){DB=structuredClone(base);actor='platform';output={message:'Workspace reset',data:snapshot()}}
      else if(url==='/api/tests')output=QA;
      else if(url==='/api/action')output={...action(data),data:snapshot()};
      else bad('Unknown route',404);
      return {ok:true,json:async()=>output};
    }catch(e){return {ok:false,status:e.status||500,json:async()=>({error:e.message})}}
  };
})();
'''
mock=mock.replace('__STATE__',json.dumps(base,separators=(',',':'))).replace('__QA__',json.dumps(qa,separators=(',',':')))
html=html.replace('<link rel="stylesheet" href="/styles.css">',f'<style>{css}</style>')
html=html.replace('<script src="/app.js" defer></script>',f'<script>{mock}</script><script>{js}</script>')
html=html.replace('<header class="topbar">','<header class="topbar">')
html=html.replace('<footer class="footer">', '<footer class="footer">Offline browser-only preview. Real API rules and executable QA tests are in the full Python project. · ')
path=ROOT/'preview.html'
path.write_text(html,encoding='utf-8')
print(f'Wrote {path}, {path.stat().st_size} bytes')
