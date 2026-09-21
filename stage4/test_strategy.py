"""Visible Strategy play, private handoff, CPU rendering and replay checks."""
import json
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright, expect
from .serve import create_server

QA = Path('/mnt/seagate/models/pyrocene/stage4/qa-expedition')

class StrategyPlay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  QA.mkdir(parents=True, exist_ok=True)
  cls.server = create_server(port=0)
  threading.Thread(target=cls.server.serve_forever, daemon=True).start()
  cls.base = f'http://127.0.0.1:{cls.server.server_port}'
  cls.p = sync_playwright().start()
  cls.browser = cls.p.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
 @classmethod
 def tearDownClass(cls):
  cls.browser.close(); cls.p.stop(); cls.server.shutdown(); cls.server.server_close()
 def setUp(self):
  self.context = self.browser.new_context(viewport={'width':1440,'height':1000}, reduced_motion='reduce')
  self.page = self.context.new_page(); self.errors=[]
  self.page.on('pageerror',lambda e:self.errors.append(str(e)))
  self.page.on('console',lambda e:self.errors.append(e.text) if e.type=='error' and ('Shader' in e.text or 'VALIDATE_STATUS' in e.text) else None)
 def tearDown(self):
  self.context.close(); self.assertEqual(self.errors,[])
 def ready(self): self.page.wait_for_function('globalThis.strategyDiagnostics && !strategyDiagnostics().busy')
 def start(self, suffix=''):
  self.page.goto(self.base+'/strategy.html'+suffix); self.page.locator('#loading').wait_for(state='hidden',timeout=60000)
  self.page.get_by_role('button',name='Begin',exact=True).click(); self.ready()
 def action(self, index):
  self.page.locator('#patch-actions button').nth(index).click(); self.ready()
  expect(self.page.locator('#toast')).to_be_hidden()
 def shot(self, name): self.page.screenshot(path=str(QA/(name+'.png')))
 def test_actions_field_guide_structure_replay_and_fire(self):
  self.start(); self.shot('strategy-tested-map')
  self.action(0); self.assertEqual(self.page.locator('.ledger-block').count(),1)
  self.action(1); expect(self.page.locator('#patch-title')).to_contain_text('young planting')
  self.page.get_by_role('button',name='Close view',exact=True).click(); self.ready(); self.shot('strategy-tested-close')
  self.page.locator('#plot-plants').select_option('urochloa_brizantha')
  expect(self.page.locator('#plant-guide')).to_be_visible()
  self.page.get_by_role('tab',name='Dispersal',exact=True).click(); self.shot('strategy-tested-dispersal')
  self.page.get_by_role('tab',name='Germination',exact=True).click(); self.shot('strategy-tested-germination')
  self.page.locator('#record-close').click(); self.page.locator('#structure').click()
  self.page.wait_for_function('strategyDiagnostics().lab.draws>0'); self.shot('strategy-tested-structure')
  self.page.locator('#structure-lab').get_by_role('button',name='Back',exact=True).click()
  self.page.get_by_role('button',name='Forest',exact=True).click(); self.ready()
  before=self.page.evaluate('strategyDiagnostics().game'); self.page.reload(); self.ready()
  self.assertEqual(self.page.evaluate('strategyDiagnostics().game'),before)
  # A neglected planting is left through twelve years. The visible result
  # must match the deterministic model, including the fire footprint.
  while self.page.evaluate('strategyDiagnostics().game.status')=='playing':
   self.page.locator('#wait').click(); self.ready()
  final=self.page.evaluate('strategyDiagnostics().game')
  self.assertEqual(final['turn'],24)
  self.assertTrue(final['burnedRecords'])
  self.assertTrue(any(e['outcome']=='reinvaded' for e in final['ledgerHistory']))
  self.shot('strategy-tested-neglected-end')
  self.page.locator('#retry').click(); self.page.locator('#begin').click(); self.ready()
  self.assertEqual(self.page.evaluate('strategyDiagnostics().game.turn'),0)
  self.action(0); self.action(1)
  self.assertEqual(self.page.evaluate('strategyDiagnostics().game'),before)
 def test_cpu_close_without_hardware_acceleration(self):
  browser=self.p.chromium.launch(args=['--disable-webgl'])
  try:
   self.page=browser.new_page(viewport={'width':1280,'height':900},reduced_motion='reduce')
   self.page.on('pageerror',lambda e:self.errors.append(str(e)))
   self.start(); self.assertTrue(self.page.evaluate('strategyDiagnostics().forest.fallback'))
   self.action(0); self.action(1)
   self.page.get_by_role('button',name='Close view',exact=True).click(); self.ready()
   self.assertGreater(self.page.evaluate('strategyDiagnostics().forest.detailPoints'),10000)
   self.shot('strategy-tested-cpu-close')
  finally: browser.close()
 def test_shared_handoff_does_not_change_room(self):
  # Fresh test-only room. Nothing touches the live event room.
  request=self.context.request
  s=request.post(self.base+'/api/round/new',data={}).json()
  credentials={'session':s['id'],'token':s['token']}
  def post(action, **extra):
   nonlocal s
   r=request.post(self.base+'/api/round/'+action,data={**credentials,'revision':s['revision'],'round':s['round'],**extra})
   self.assertTrue(r.ok,r.text()); s=r.json(); return s
  for team in ['removal','ecology']:
   post('visit',team=team,patch='C'); post('propose',team=team,patch='C')
  post('reveal'); post('commit'); post('advance')
  for team in ['removal','ecology']:
   post('visit',team=team,patch='C'); post('propose',team=team,patch='C')
  post('reveal'); post('commit'); snapshot=json.loads(json.dumps(s))
  url=self.base+'/round.html#'+urlencode({**credentials,'role':'room'})
  self.page.goto(url); self.page.locator('#loading').wait_for(state='hidden',timeout=60000)
  if self.page.locator('#briefing[open]').count(): self.page.locator('#briefing-begin').click()
  self.page.locator('#game-mode').select_option('strategy'); self.page.wait_for_url('**/strategy.html#*')
  self.page.locator('#loading').wait_for(state='hidden',timeout=60000); self.page.locator('#begin').click(); self.ready()
  self.assertEqual(self.page.evaluate('strategyDiagnostics().game.foundation.restored'),27)
  self.assertEqual(self.page.evaluate('strategyDiagnostics().game.credits'),snapshot['committed']['left'])
  self.action(0)
  actual=request.post(self.base+'/api/round/state',data=credentials).json()
  self.assertEqual(actual,snapshot)
  self.page.locator('#stage').select_option('shared'); self.page.wait_for_url('**/round.html#*')
  self.page.locator('#loading').wait_for(state='hidden',timeout=60000)
  self.assertEqual(self.page.evaluate('roundDiagnostics().state.committed'),snapshot['committed'])

if __name__=='__main__': unittest.main()
