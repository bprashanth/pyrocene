import unittest
from .shared_round import RoundStore, RoundError, budget

class SharedRoundRules(unittest.TestCase):
 def setUp(self):
  self.store=RoundStore();self.s=self.store.request('new',{})
 def action(self,action,role='room',**extra):
  token=self.s['token'] if role=='room' else self.s['teams'][role]
  body={'session':self.s['id'],'token':token,'revision':self.s['revision'],**extra}
  result=self.store.request(action,body)
  self.s=self.store.request('state',{'session':self.s['id'],'token':self.s['token']})
  return result
 def propose(self,team,key):
  self.action('visit',role=team,patch=key);return self.action('propose',role=team,patch=key)
 def test_nine_plans_validate_funds_and_commit_once(self):
  for r in 'ABC':
   for e in 'ABC':
    self.action('replay');self.propose('removal',r);self.propose('ecology',e);self.action('reveal')
    if budget(r,e)['left']<0:
     with self.assertRaises(RoundError):self.action('commit')
     self.assertEqual(self.s['phase'],'review')
    else:
     got=self.action('commit');self.assertEqual(got['committed']['left'],budget(r,e)['left'])
     with self.assertRaises(RoundError):self.action('commit')
 def test_roles_hidden_proposals_and_stale_revision(self):
  with self.assertRaises(RoundError):self.action('propose',role='removal',patch='A')
  self.propose('removal','A');e=self.action('state',role='ecology')
  self.assertIsNone(e['proposals']['removal']);self.assertTrue(e['ready']['removal']);self.assertNotIn('teams',e)
  with self.assertRaises(RoundError):self.action('visit',role='ecology',team='removal',patch='B')
  with self.assertRaises(RoundError):self.action('reveal',role='ecology')
  with self.assertRaises(RoundError):self.action('reveal')
  self.propose('ecology','B');self.action('reveal');self.assertEqual(self.action('state',role='ecology')['proposals']['removal'],'A')
  with self.assertRaises(RoundError):self.store.request('commit',{'session':self.s['id'],'token':self.s['token'],'revision':0})
 def test_replay_resets_survey_and_plan(self):
  self.propose('removal','C');self.propose('ecology','C');self.action('reveal');self.action('commit');self.action('replay')
  self.assertEqual(self.s['phase'],'survey');self.assertIsNone(self.s['committed']);self.assertEqual(self.s['visited']['removal'],[])
  self.assertEqual(self.s['proposals'],{'removal':None,'ecology':None})
 def test_simultaneous_surveys_and_independent_proposals_do_not_conflict(self):
  initial=self.s['revision'];self.action('visit',role='removal',patch='A')
  body={'session':self.s['id'],'token':self.s['teams']['ecology'],'revision':initial,'patch':'B','round':self.s['round']}
  self.store.request('visit',body)
  self.s=self.store.request('state',{'session':self.s['id'],'token':self.s['token']})
  revision=self.s['revision'];self.action('propose',role='removal',patch='A')
  self.store.request('propose',{**body,'revision':revision,'round':1,'phase':'survey','prior':None})
  self.assertTrue(all(self.action('state')['ready'].values()))
  self.action('reveal')
  with self.assertRaises(RoundError):self.store.request('propose',{**body,'revision':revision,'round':1,'phase':'survey','prior':None})
  self.action('replay')
  with self.assertRaises(RoundError):self.store.request('visit',body)
