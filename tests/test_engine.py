import unittest
from engine import Engine, WorkflowError
from quality import run_checks

class WorkflowTests(unittest.TestCase):
    def setUp(self):self.e=Engine()
    def reject(self,fn,code=409):
        with self.assertRaises(WorkflowError) as raised:fn()
        self.assertEqual(raised.exception.code,code)
    def test_quality_suite(self):
        result=run_checks()
        self.assertEqual(result['passed'],18,str([x for x in result['results'] if x['status']=='FAIL']))
    def test_fixture_volume(self):
        self.assertEqual([len(self.e.data[k]) for k in ['employers','people','batches','ledger']],[5,60,7,8])
    def test_validate_clean_batch(self):
        self.e.switch('payroll');r=self.e.apply('validate_batch',{'id':'PAY-6001'})
        self.assertIn('validated',r['message']);self.assertEqual(self.e._get('batches','PAY-6001')['state'],'validated')
    def test_reconciliation_blocks(self):
        self.e.switch('ops');r=self.e.apply('validate_batch',{'id':'PAY-6003'})
        self.assertEqual(self.e._get('batches','PAY-6003')['state'],'exception')
        self.assertTrue(any(c=='REMITTANCE_MISMATCH' for c,m in r['evidence']['errors']))
    def test_unmatched_employee_blocks(self):
        self.e.switch('ops');self.e.apply('validate_batch',{'id':'PAY-6002'});
        self.assertTrue(any(x['code']=='UNKNOWN_PARTICIPANT' for x in self.e.data['exceptions']))
    def test_posting_only_after_validation(self):
        self.e.switch('ops');self.reject(lambda:self.e.apply('post_batch',{'id':'PAY-6001'}))
    def test_double_post_rejected(self):
        self.e.switch('ops');self.e.apply('validate_batch',{'id':'PAY-6001'});r=self.e.apply('post_batch',{'id':'PAY-6001'});count=len(self.e.data['ledger']);self.reject(lambda:self.e.apply('post_batch',{'id':'PAY-6001'}));self.assertEqual(len(self.e.data['ledger']),count)
    def test_posting_balances(self):
        self.e.switch('ops');p=self.e._get('people','P-1001');before=p['balance'];self.e.apply('validate_batch',{'id':'PAY-6001'});self.e.apply('post_batch',{'id':'PAY-6001'});gross=self.e._get('batches','PAY-6001')['lines'][0]['gross'];ee,er=self.e.contribution(gross,{'deferral_pct':4});self.assertAlmostEqual(p['balance'],before+ee+er,places=2)
    def test_actor_cannot_cross_tenant(self):
        self.e.switch('sponsor');self.reject(lambda:self.e.apply('advance_plan',{'id':'EMP-104'}),403)
    def test_sponsor_cannot_activate_configured(self):
        self.e.switch('sponsor');self.e._get('employers','EMP-101')['status']='configured';self.reject(lambda:self.e.apply('advance_plan',{'id':'EMP-101'}),403)
    def test_employee_scoped_read(self):
        self.e.switch('participant');d=self.e.snapshot();self.assertEqual(len(d['people']),1);self.assertEqual(len(d['batches']),0);self.assertEqual(len(d['employers']),1)
    def test_deferral_does_not_modify_historical_batch(self):
        self.e.switch('participant');self.e.apply('set_deferral',{'person_id':'P-1001','pct':6});self.assertEqual(self.e._get('people','P-1001')['deferral_pct'],6);self.assertEqual(self.e._get('batches','PAY-6006')['state'],'posted')
    def test_invalid_deferral(self):
        self.e.switch('participant');self.reject(lambda:self.e.apply('set_deferral',{'person_id':'P-1001','pct':'abc'}),400)
    def test_bad_role(self):
        self.reject(lambda:self.e.switch('hacker'),400)
    def test_repair_requires_exception(self):
        self.e.switch('ops');self.reject(lambda:self.e.apply('repair_batch',{'id':'PAY-6001','repair':'reconcile_amount'}))
    def test_repair_and_validate(self):
        self.e.switch('ops');self.e.apply('validate_batch',{'id':'PAY-6003'});self.e.apply('repair_batch',{'id':'PAY-6003','repair':'reconcile_amount'});self.e.apply('validate_batch',{'id':'PAY-6003'});self.assertEqual(self.e._get('batches','PAY-6003')['state'],'validated')
    def test_duplicate_detection(self):
        self.e.switch('ops');self.e.apply('validate_batch',{'id':'PAY-6001'});r=self.e.apply('validate_batch',{'id':'PAY-6004'});self.assertIn('DUPLICATE_BATCH',[x[0] for x in r['evidence']['errors']])
    def test_human_review_gate(self):
        self.e.switch('participant');r=self.e.apply('request_distribution',{'person_id':'P-1001','amount':250});self.assertFalse('ledger' in r['evidence']);self.e.switch('ops');r=self.e.apply('review_distribution',{'id':'DIST-0001'});self.assertEqual(r['evidence']['status'],'reviewed_no_disbursement')
    def test_plan_stages(self):
        self.e.switch('ops');self.e.apply('advance_plan',{'id':'EMP-104'});self.e.apply('advance_plan',{'id':'EMP-104'});self.reject(lambda:self.e.apply('advance_plan',{'id':'EMP-104'}))
    def test_reset_isolated(self):
        self.e.switch('ops');self.e.apply('validate_batch',{'id':'PAY-6001'});self.e.reset();self.assertEqual(self.e._get('batches','PAY-6001')['state'],'received')
    def test_unsupported_action(self):
        self.reject(lambda:self.e.apply('set_balance',{'person_id':'P-1001','amount':9999}),400)

if __name__=='__main__':unittest.main()
