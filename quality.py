"""Public, safe, side-effect-free test bench executed in a fresh isolated engine."""
from engine import Engine,WorkflowError

def run_checks():
    results=[]
    def check(category,name,fn,evidence):
        try:
            fn();results.append({'category':category,'name':name,'status':'PASS','evidence':evidence})
        except Exception as e:
            results.append({'category':category,'name':name,'status':'FAIL','evidence':f'{type(e).__name__}: {e}'})
    def expect_error(fn,code):
        try: fn()
        except WorkflowError as e:
            assert e.code==code, f'Expected {code}, got {e.code}'
            return
        raise AssertionError(f'Expected workflow error HTTP {code}')
    def fresh():return Engine()
    check('Unit','Employer match formula',lambda: (lambda x:assert_equal(x,(100,40)))(fresh().contribution(2000,{'deferral_pct':5})), '5% employee + 50% match up to 4% on $2,000 = $100 + $40')
    check('Unit','Zero deferral produces no contribution',lambda:assert_equal(fresh().contribution(2000,{'deferral_pct':0}),(0,0)), 'Employee $0, Employer $0')
    check('Unit','Deferral rounding',lambda:assert_equal(fresh().contribution(2351.16,{'deferral_pct':3}),(70.53,35.27)), 'Currency rounded to cents')
    check('Integration','Seeded master-data joins',lambda:assert_equal(len([p for p in fresh().data['people'] if any(e['id']==p['employer_id'] for e in fresh().data['employers'])]),60),'60 participant foreign keys resolve')
    check('Integration','Payroll amount reconciles',lambda:assert_equal(fresh().analyze_batch(fresh()._get('batches','PAY-6001'))[1],[]),'PAY-6001: no validation exceptions')
    check('Integration','Unknown participant identified',lambda:assert_true(any(c=='UNKNOWN_PARTICIPANT' for c,_ in fresh().analyze_batch(fresh()._get('batches','PAY-6002'))[1])),'PAY-6002: unmatched participant')
    check('Integration','Remittance mismatch identified',lambda:assert_true(any(c=='REMITTANCE_MISMATCH' for c,_ in fresh().analyze_batch(fresh()._get('batches','PAY-6003'))[1])),'PAY-6003: short by $125')
    check('Integration','Timeliness review flagged',lambda:assert_true(any(c=='TIMELINESS_REVIEW' for c,_ in fresh().analyze_batch(fresh()._get('batches','PAY-6005'))[1])),'PAY-6005: human review rather than auto-judgment')
    def happy():
        e=fresh();e.switch('payroll');e.apply('validate_batch',{'id':'PAY-6001'});e.switch('ops');before=len(e.data['ledger']);e.apply('post_batch',{'id':'PAY-6001'});assert len(e.data['ledger'])-before==8
    check('E2E','Payroll → validate → post → ledger',happy,'8 balanced employee/employer entries and batch posted')
    def replay():
        e=fresh();e.switch('payroll');e.apply('validate_batch',{'id':'PAY-6001'});e.switch('ops');e.apply('post_batch',{'id':'PAY-6001'});expect_error(lambda:e.apply('post_batch',{'id':'PAY-6001'}),409)
    check('E2E','Posting replay protection',replay,'Second posting rejected; no double credit')
    def repair():
        e=fresh();e.switch('ops');e.apply('validate_batch',{'id':'PAY-6003'});e.apply('repair_batch',{'id':'PAY-6003','repair':'reconcile_amount'});e.apply('validate_batch',{'id':'PAY-6003'});assert e._get('batches','PAY-6003')['state']=='validated'
    check('E2E','Exception → repair → revalidate',repair,'Short-remittance case remediated with review history')
    def sponsor():
        e=fresh();e.switch('sponsor');expect_error(lambda:e.apply('post_batch',{'id':'PAY-6001'}),403)
    check('RBAC','Employer cannot post funds',sponsor,'HTTP 403 enforced on backend')
    def isolation():
        e=fresh();e.switch('sponsor');expect_error(lambda:e.apply('advance_plan',{'id':'EMP-104'}),403)
    check('RBAC','Cross-employer action forbidden',isolation,'Cedar Arc cannot modify Blue Mesa')
    def participant():
        e=fresh();e.switch('participant');expect_error(lambda:e.apply('set_deferral',{'person_id':'P-1002','pct':5}),403)
    check('RBAC','Participant cannot edit peer election',participant,'HTTP 403 for another employee')
    def input_validation():
        e=fresh();e.switch('participant');expect_error(lambda:e.apply('set_deferral',{'person_id':'P-1001','pct':80}),400)
    check('Security','Out-of-range election rejected',input_validation,'Percent > 50 rejected')
    def distribution():
        e=fresh();before=len(e.data['ledger']);e.switch('participant');e.apply('request_distribution',{'person_id':'P-1001','amount':100});r=e.data['requests'][0];assert r['status']=='needs_review';assert len(e.data['ledger'])==before
    check('UAT','Distribution is review-only',distribution,'Request does not debit balance or send money')
    def plan():
        e=fresh();e.switch('ops');e.apply('advance_plan',{'id':'EMP-104'});e.apply('advance_plan',{'id':'EMP-104'});assert e._get('employers','EMP-104')['status']=='live'
    check('UAT','Plan activation state machine',plan,'draft → configured → live')
    def scope():
        e=fresh();e.switch('participant');s=e.snapshot();assert len(s['people'])==1 and len(s['batches'])==0
    check('RBAC','Participant scoped read model',scope,'Only own profile; no employer payroll feed')
    return {'total':len(results),'passed':sum(x['status']=='PASS' for x in results),'failed':sum(x['status']=='FAIL' for x in results),'results':results,'execution':'isolated deterministic state; active visitor data unchanged'}

def assert_equal(actual,want):
    assert actual==want,f'{actual!r} != {want!r}'
def assert_true(value):
    assert value
