"""All data is fictional and deterministic; this is not a retirement recordkeeper."""
from pathlib import Path
import csv

ROOT = Path(__file__).parent
DATA = ROOT / 'data'

def read_csv(filename):
    with (DATA / filename).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))

def seed_state():
    employers = read_csv('employers.csv')
    people = read_csv('participants.csv')
    for person in people:
        for field in ('deferral_pct','ytd_deferral','balance','salary'):
            person[field] = float(person[field])
    batches = read_csv('payroll_batches.csv')
    lines = read_csv('payroll_lines.csv')
    for line in lines:
        line['gross'] = float(line['gross'])
    for batch in batches:
        batch['remitted_total'] = float(batch['remitted_total'])
        batch['lines'] = [dict(line) for line in lines if line['batch_id'] == batch['id']]
    ledger = []
    for batch in batches:
        if batch['state'] != 'posted': continue
        for line in batch['lines']:
            person = next((p for p in people if p['id'] == line['person_id']), None)
            if not person: continue
            gross = line['gross']; pct = person['deferral_pct']
            for kind, amount in [('employee', round(gross*pct/100,2)),('employer',round(gross*min(pct,4)/100*0.5,2))]:
                ledger.append({'id':f'L-{len(ledger)+1:05d}','batch_id':batch['id'],'employer_id':batch['employer_id'],'person_id':person['id'],'kind':kind,'amount':amount,'date':batch['pay_date']})
    return {
        'employers': employers, 'people': people, 'batches': batches,
        'ledger': ledger, 'exceptions': [], 'requests': [],
        'audit': [{'id':'EVT-0001','time':'2026-11-14T08:00:00Z','actor':'seed','event':'DATA_SEEDED','detail':'Synthetic plan, participant, and payroll fixtures loaded'}],
        'seq': 1
    }

ACTORS = [
    {'id':'platform','label':'Platform Admin','role':'platform','employer_id':None,'person_id':None,'note':'Portfolio-wide oversight and support'},
    {'id':'ops','label':'Operations Analyst','role':'ops','employer_id':None,'person_id':None,'note':'Review exceptions, reconcile and post batches'},
    {'id':'sponsor','label':'Employer Administrator · Cedar Arc','role':'sponsor','employer_id':'EMP-101','person_id':None,'note':'Plan administration and workforce view'},
    {'id':'payroll','label':'Payroll Specialist · Cedar Arc','role':'payroll','employer_id':'EMP-101','person_id':None,'note':'Validate incoming payroll files'},
    {'id':'participant','label':'Employee · Maya Chen','role':'participant','employer_id':'EMP-101','person_id':'P-1001','note':'Self-service deferral election'},
]
