"""Deterministic generator for fictional employers, participants and payroll files."""
from pathlib import Path
import csv

DATA=Path(__file__).parent/'data'; DATA.mkdir(exist_ok=True)
def out(name,cols,rows):
    with (DATA/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)

employers=[
 dict(id='EMP-101',name='Cedar Arc Design Co.',industry='Architecture & Design',location='Austin, TX',status='live',plan_type='401(k)',payroll_partner='Northstar Payroll',participants='12',match='50% of first 4%',owner='Alicia Grant',onboarding='Complete',next_payroll='2026-11-20'),
 dict(id='EMP-102',name='Summitfield Manufacturing',industry='Light Manufacturing',location='Columbus, OH',status='live',plan_type='401(k)',payroll_partner='ForgePay',participants='12',match='50% of first 4%',owner='Daniel Brooks',onboarding='Complete',next_payroll='2026-11-20'),
 dict(id='EMP-103',name='Harborline Clinics',industry='Outpatient Healthcare',location='Sacramento, CA',status='configured',plan_type='403(b)',payroll_partner='CarePay Connect',participants='12',match='50% of first 4%',owner='Priya Raman',onboarding='Verification',next_payroll='2026-11-27'),
 dict(id='EMP-104',name='Blue Mesa Kitchens',industry='Construction Services',location='Phoenix, AZ',status='draft',plan_type='401(k)',payroll_partner='Northstar Payroll',participants='12',match='50% of first 4%',owner='Ethan Cole',onboarding='Plan configuration',next_payroll='2026-12-04'),
 dict(id='EMP-105',name='Redwood Learning Group',industry='Professional Education',location='Seattle, WA',status='live',plan_type='401(k)',payroll_partner='AtlasPay',participants='12',match='50% of first 4%',owner='Nora Patel',onboarding='Complete',next_payroll='2026-11-20'),
]
out('employers.csv',list(employers[0]),employers)
first=['Maya','Evan','Sofia','Noah','Amara','Leo','Grace','Owen','Isla','Arjun','Nina','Kai','Elena','Mateo','Priya','Liam','Chloe','Miles','Zara','Julian','Hana','Theo','Ava','Ishan','Emma','Jasper','Mila','Caleb','Leila','Rowan','Anika','Finn','Sage','Ravi','Ella','Remy','Lucy','Nolan','Ivy','Micah','Elise','Hugo','Tara','Dylan','Mira','Arthur','Tessa','Rohan','Clara','Zane','Anya','Amir','Bea','Ezra','Skye','Neel','Lara','Dev','Holly','Aria']
last=['Chen','Morales','Patel','Turner','Okafor','Kim','Reed','Foster','Morris','Shah','Diaz','Nguyen','Park','Ellis','Singh','Baker','Jones','Brooks','Meyer','Lopez','Khan','Wright','Scott','Murphy','Davis','Cruz','Stone','Russell','Adams','Price','Rivera','Hart','Santos','Gupta','Bell','Cole','Wong','Hill','Wood','Evans','Rossi','Green','Parker','Kelly','Rao','Young','Hughes','Das','Perry','Lane','Iyer','Brown','Ward','Fox','West','Ali','Hall','Long','Bose','Ross']
people=[]
for i in range(60):
    e=employers[i//12];p= (i%12)
    people.append(dict(id=f'P-{1001+i}',employer_id=e['id'],name=f'{first[i]} {last[i]}',email=f'{first[i].lower()}.{last[i].lower()}@example.test',status='active' if p<10 else 'eligible',salary=round(59000+i*1930,-2),deferral_pct=[4,6,3,5,8,0,7,4,10,2,6,5][p],ytd_deferral=round(650+p*810+i*24,2),balance=round(6200+i*935+p*48,2)))
out('participants.csv',list(people[0]),people)

batches=[
 dict(id='PAY-6001',external_id='NSTAR-20261113-A',employer_id='EMP-101',pay_date='2026-11-13',state='received',remitted_total=0,flag='',scenario='Happy path: valid pay run'),
 dict(id='PAY-6002',external_id='NSTAR-20261113-B',employer_id='EMP-101',pay_date='2026-11-13',state='received',remitted_total=0,flag='',scenario='Unknown employee identifier'),
 dict(id='PAY-6003',external_id='FORGE-20261113-A',employer_id='EMP-102',pay_date='2026-11-13',state='received',remitted_total=0,flag='',scenario='Remittance does not reconcile'),
 dict(id='PAY-6004',external_id='NSTAR-20261113-A',employer_id='EMP-101',pay_date='2026-11-13',state='received',remitted_total=0,flag='',scenario='Duplicate payroll file'),
 dict(id='PAY-6005',external_id='ATLAS-20260918',employer_id='EMP-105',pay_date='2026-09-18',state='received',remitted_total=0,flag='timeliness_review',scenario='Potential late contribution: review required'),
 dict(id='PAY-6006',external_id='FORGE-20261106',employer_id='EMP-102',pay_date='2026-11-06',state='posted',remitted_total=0,flag='',scenario='Previously posted source for duplicate control'),
 dict(id='PAY-6007',external_id='ATLAS-20261113',employer_id='EMP-105',pay_date='2026-11-13',state='received',remitted_total=0,flag='',scenario='Second valid pay run'),
]
lines=[]
for b in batches:
    root=int(b['employer_id'].split('-')[1])-101
    members=people[root*12:root*12+12]
    for p in members[:4]:
        lines.append(dict(batch_id=b['id'],person_id=p['id'],gross=round(float(p['salary'])/26,2)))
    if b['id']=='PAY-6002': lines[-1]['person_id']='P-UNKNOWN'

def expected(b):
    total=0
    for l in lines:
        if l['batch_id']!=b['id']:continue
        p=next((p for p in people if p['id']==l['person_id']),None)
        if not p:continue
        gross=float(l['gross']);pct=float(p['deferral_pct'])
        total += round(gross*pct/100,2) + round(gross*min(pct,4)/100*.5,2)
    return round(total,2)
for b in batches:
    b['remitted_total']=expected(b)
    if b['id']=='PAY-6003': b['remitted_total']=round(b['remitted_total']-125,2)
    if b['id']=='PAY-6002': b['remitted_total']=round(b['remitted_total']+100,2)
out('payroll_batches.csv',list(batches[0]),batches)
out('payroll_lines.csv',list(lines[0]),lines)
print(f'Seeded {len(employers)} employers, {len(people)} participants, {len(batches)} payroll batches, {len(lines)} lines.')
