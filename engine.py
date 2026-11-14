"""Deterministic retirement operations workflow engine. All funds are fictional."""
from datetime import datetime, timezone
from math import isclose
from copy import deepcopy
from seed import seed_state, ACTORS

ANNUAL_DEFERRAL_REFERENCE_2026 = 24500.0  # illustrative under-age-50 base limit only

class WorkflowError(Exception):
    def __init__(self, message, code=409):
        self.code = code
        super().__init__(message)

class Engine:
    def __init__(self):
        self.data = seed_state()
        self.actor = 'platform'

    @property
    def identity(self):
        return next(actor for actor in ACTORS if actor['id'] == self.actor)

    def switch(self, actor):
        if actor not in {a['id'] for a in ACTORS}:
            raise WorkflowError('Unknown demonstration persona', 400)
        self.actor = actor
        return self.snapshot()

    def reset(self):
        self.data = seed_state()
        self.actor = 'platform'
        return self.snapshot()

    def allowed(self, employer_id=None, roles=None):
        actor = self.identity
        if roles and actor['role'] not in roles:
            raise WorkflowError('This persona is not permitted to perform this operation', 403)
        if employer_id and actor['role'] in ('sponsor','payroll','participant') and actor['employer_id'] != employer_id:
            raise WorkflowError('This persona does not have access to that employer', 403)

    def _get(self, kind, item_id):
        value = next((x for x in self.data[kind] if x['id'] == item_id), None)
        if not value:
            raise WorkflowError('Record not found', 404)
        return value

    def audit(self, event, detail):
        self.data['seq'] += 1
        self.data['audit'].insert(0, {'id':f"EVT-{self.data['seq']:04d}", 'time':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'actor':self.actor,'event':event,'detail':detail})

    def contribution(self, gross, person):
        """Illustrative plan: employee election plus 50% match on first 4% of eligible gross."""
        employee = round(gross * person['deferral_pct'] / 100, 2)
        employer = round(gross * min(person['deferral_pct'], 4.0) / 100 * 0.5, 2)
        return employee, employer

    def analyze_batch(self, batch):
        problems = []
        lines = batch['lines']
        if not lines:
            problems.append(('EMPTY_BATCH','File has no contribution lines'))
        existing_external = [b for b in self.data['batches'] if b['id'] != batch['id'] and b['external_id'] == batch['external_id'] and b['employer_id'] == batch['employer_id'] and b['state'] in ('posted','validated')]
        if existing_external:
            problems.append(('DUPLICATE_BATCH',f"External payroll ID {batch['external_id']} was previously validated or posted"))
        seen = set()
        expected = 0.0
        for line in lines:
            person = next((p for p in self.data['people'] if p['id'] == line['person_id'] and p['employer_id'] == batch['employer_id']), None)
            if not person:
                problems.append(('UNKNOWN_PARTICIPANT',f"Employee {line['person_id']} cannot be matched to the employer's plan"))
                continue
            if line['person_id'] in seen:
                problems.append(('DUPLICATE_LINE',f"Employee {line['person_id']} appears twice"))
                continue
            seen.add(line['person_id'])
            if line['gross'] <= 0:
                problems.append(('INVALID_GROSS',f"Nonpositive wages for {person['name']}"))
                continue
            ee, er = self.contribution(line['gross'],person)
            if person['ytd_deferral'] + ee > ANNUAL_DEFERRAL_REFERENCE_2026:
                problems.append(('DEFERRAL_REVIEW',f"{person['name']} exceeds simplified 2026 base deferral threshold; specialist review required"))
            expected += ee + er
        expected = round(expected,2)
        if not isclose(expected, batch['remitted_total'], rel_tol=0, abs_tol=0.01):
            problems.append(('REMITTANCE_MISMATCH',f"Expected ${expected:,.2f}; received ${batch['remitted_total']:,.2f}"))
        # A flag for operations review, not a determination of legal non-compliance.
        if batch['flag'] == 'timeliness_review':
            problems.append(('TIMELINESS_REVIEW','Payroll remittance timing needs human review against applicable plan and DOL rules'))
        return expected, problems

    def snapshot(self):
        a = self.identity
        role = a['role']
        eid = a['employer_id']
        employers = [deepcopy(e) for e in self.data['employers'] if role in ('platform','ops') or e['id']==eid]
        people = [deepcopy(p) for p in self.data['people'] if (role in ('platform','ops') or p['employer_id']==eid) and (role!='participant' or p['id']==a['person_id'])]
        batches = [] if role=='participant' else [deepcopy(b) for b in self.data['batches'] if role in ('platform','ops') or b['employer_id']==eid]
        for batch in batches:
            batch['expected_total'] = self.analyze_batch(batch)[0]
            batch['line_count'] = len(batch['lines'])
        exceptions = [deepcopy(e) for e in self.data['exceptions'] if role in ('platform','ops') or (role in ('sponsor','payroll') and e['employer_id']==eid)]
        ledger = [deepcopy(x) for x in self.data['ledger'] if role in ('platform','ops') or (role != 'participant' and x['employer_id']==eid) or (role=='participant' and x['person_id']==a['person_id'])]
        requests = [deepcopy(x) for x in self.data['requests'] if role in ('platform','ops') or (role=='participant' and x['person_id']==a['person_id']) or (role=='sponsor' and x['employer_id']==eid)]
        audit = [] if role=='participant' else [deepcopy(x) for x in self.data['audit'][:35] if role in ('platform','ops') or eid in x['detail']]
        return {'actor':a,'actors':ACTORS,'employers':employers,'people':people,'batches':batches,'exceptions':exceptions, 'ledger':ledger,'requests':requests,'audit':audit, 'stats':{
            'employers':len(employers),'participants':len(people),'batches':len(batches),
            'exceptions':len([x for x in exceptions if x['status']=='open']),
            'posted_batches':len([b for b in batches if b['state']=='posted']),
            'ledger_total':round(sum(x['amount'] for x in ledger if x['kind'] in ('employee','employer')),2),
        }}

    def apply(self, action, payload):
        if action == 'validate_batch':
            batch = self._get('batches',payload.get('id'))
            self.allowed(batch['employer_id'],['payroll','ops','platform'])
            if batch['state'] not in ('received','exception'):
                raise WorkflowError('Only received or exception batches can be validated')
            amount, errors = self.analyze_batch(batch)
            if errors:
                batch['state'] = 'exception'
                for code, message in errors:
                    if not any(e['batch_id']==batch['id'] and e['code']==code and e['status']=='open' for e in self.data['exceptions']):
                        self.data['exceptions'].append({'id':f"EX-{len(self.data['exceptions'])+1001}", 'batch_id':batch['id'],'employer_id':batch['employer_id'],'code':code,'description':message,'status':'open','owner':'Operations','severity':'High' if code in ('UNKNOWN_PARTICIPANT','REMITTANCE_MISMATCH','DEFERRAL_REVIEW') else 'Medium'})
                self.audit('BATCH_REJECTED',f"{batch['employer_id']} / {batch['id']} failed {len(errors)} checks")
                return {'message':f"Validation blocked: {len(errors)} issue(s) created",'evidence':{'batch_id':batch['id'],'expected_total':amount,'errors':errors}}
            batch['state'] = 'validated'
            for ex in self.data['exceptions']:
                if ex['batch_id']==batch['id'] and ex['status']=='open': ex['status']='resolved'
            self.audit('BATCH_VALIDATED',f"{batch['employer_id']} / {batch['id']} amount ${amount:.2f}")
            return {'message':'Payroll batch validated; Operations can now post it','evidence':{'batch_id':batch['id'],'amount':amount,'checks':'participant, duplicate, remittance, limits, timing'}}

        if action == 'repair_batch':
            batch = self._get('batches',payload.get('id'))
            self.allowed(batch['employer_id'],['ops','platform'])
            if batch['state'] != 'exception':
                raise WorkflowError('Repair requires an exception-state batch')
            repair = payload.get('repair')
            if repair=='reconcile_amount':
                amount, problems = self.analyze_batch(batch)
                if any(code in ('UNKNOWN_PARTICIPANT','INVALID_GROSS','DUPLICATE_BATCH','DEFERRAL_REVIEW') for code,_ in problems):
                    raise WorkflowError('Resolve blocking data and identity issues before reconciling')
                batch['remitted_total']=amount
            elif repair=='remove_unmatched':
                batch['lines']=[l for l in batch['lines'] if any(p['id']==l['person_id'] and p['employer_id']==batch['employer_id'] for p in self.data['people'])]
                amount,_=self.analyze_batch(batch)
                batch['remitted_total']=amount
            elif repair=='new_external_id':
                batch['external_id']=f"{batch['external_id']}-CORRECTED-{batch['id']}"
            elif repair=='acknowledge_timing':
                batch['flag']='review_acknowledged'
            else:
                raise WorkflowError('Unknown repair action',400)
            self.audit('EXCEPTION_REMEDIATED',f"{batch['employer_id']} / {batch['id']} · {repair} · human approval simulated")
            return {'message':'Correction recorded. Re-run validation before posting.','evidence':{'repair':repair,'batch_id':batch['id']}}

        if action=='post_batch':
            batch=self._get('batches',payload.get('id'))
            self.allowed(batch['employer_id'],['ops','platform'])
            if batch['state']!='validated':
                raise WorkflowError('Posting requires successful validation')
            amount,problems=self.analyze_batch(batch)
            if problems: raise WorkflowError('Batch changed since validation. Revalidate before posting')
            new_entries=[]
            for line in batch['lines']:
                person=self._get('people',line['person_id'])
                ee,er=self.contribution(line['gross'],person)
                for kind,value in [('employee',ee),('employer',er)]:
                    new_entries.append({'id':f"L-{len(self.data['ledger'])+len(new_entries)+1:05d}",'batch_id':batch['id'],'employer_id':batch['employer_id'],'person_id':person['id'],'kind':kind,'amount':value,'date':batch['pay_date']})
                person['balance']=round(person['balance']+ee+er,2)
                person['ytd_deferral']=round(person['ytd_deferral']+ee,2)
            self.data['ledger'].extend(new_entries)
            batch['state']='posted'
            self.audit('CONTRIBUTIONS_POSTED',f"{batch['employer_id']} / {batch['id']} · {len(new_entries)} entries · ${amount:.2f}")
            return {'message':'Fictional contributions posted to participant ledgers','evidence':{'batch_id':batch['id'],'entries':new_entries,'posted_total':amount,'external_funds_moved':False}}

        if action=='set_deferral':
            person=self._get('people',payload.get('person_id'))
            self.allowed(person['employer_id'],['participant','platform'])
            if self.identity['role']=='participant' and self.identity['person_id']!=person['id']:
                raise WorkflowError('Participants can only update their own election',403)
            try: pct=float(payload.get('pct'))
            except (TypeError,ValueError): raise WorkflowError('A numeric election is required',400)
            if pct<0 or pct>50 or pct*10 != round(pct*10):
                raise WorkflowError('Election must be between 0–50%, in 0.1% increments',400)
            old=person['deferral_pct']
            person['deferral_pct']=pct
            self.audit('ELECTION_CHANGED',f"{person['employer_id']} / {person['id']} · {old}% → {pct}% · next payroll")
            return {'message':'Election saved for the next unprocessed payroll. Prior contributions unchanged.','evidence':{'old_pct':old,'new_pct':pct,'effective':'next unprocessed payroll','person_id':person['id']}}

        if action=='advance_plan':
            employer=self._get('employers',payload.get('id'))
            self.allowed(employer['id'],['sponsor','ops','platform'])
            next_state={'draft':'configured','configured':'live'}.get(employer['status'])
            if not next_state: raise WorkflowError('Plan is already live')
            if next_state=='live' and self.identity['role']=='sponsor':
                raise WorkflowError('Operations approval is required to activate a configured plan',403)
            previous=employer['status']; employer['status']=next_state
            self.audit('PLAN_STATE_CHANGED',f"{employer['id']} / {previous} → {next_state}")
            return {'message':f"Plan moved from {previous} to {next_state}",'evidence':{'from':previous,'to':next_state,'owner':self.actor}}

        if action=='request_distribution':
            person=self._get('people',payload.get('person_id'))
            self.allowed(person['employer_id'],['participant','platform'])
            if self.identity['role']=='participant' and self.identity['person_id']!=person['id']:
                raise WorkflowError('Not your participant account',403)
            try: amount=round(float(payload.get('amount')),2)
            except (ValueError,TypeError): raise WorkflowError('Invalid amount',400)
            if amount<=0 or amount>person['balance']:
                raise WorkflowError('Requested amount must be positive and no more than illustrative balance',400)
            entry={'id':f"DIST-{len(self.data['requests'])+1:04d}",'person_id':person['id'],'employer_id':person['employer_id'],'amount':amount,'status':'needs_review','note':'Eligibility, tax, withholding, and plan terms require specialist assessment'}
            self.data['requests'].append(entry)
            self.audit('DISTRIBUTION_REQUESTED',f"{person['employer_id']} / {person['id']} · ${amount:.2f} · review pending")
            return {'message':'Request submitted for specialist review; no funds moved','evidence':entry}

        if action=='review_distribution':
            entry=self._get('requests',payload.get('id'))
            self.allowed(entry['employer_id'],['ops','platform'])
            if entry['status']!='needs_review': raise WorkflowError('Request already reviewed')
            entry['status']='reviewed_no_disbursement'
            self.audit('DISTRIBUTION_REVIEWED',f"{entry['employer_id']} / {entry['id']} · simulated checklist only")
            return {'message':'Specialist review recorded. Disbursement intentionally unsupported.','evidence':entry}

        raise WorkflowError('Unsupported operation',400)
