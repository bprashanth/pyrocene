"""Visible-control solo and two-team playthroughs of the shared round."""
import threading
import unittest
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright, expect
from .serve import create_server

QA=Path('/mnt/seagate/models/pyrocene/stage4/qa-expedition')
class RoundPlay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  QA.mkdir(exist_ok=True,parents=True);cls.server=create_server(port=0)
  threading.Thread(target=cls.server.serve_forever,daemon=True).start();cls.base=f'http://127.0.0.1:{cls.server.server_port}'
  cls.p=sync_playwright().start();cls.browser=cls.p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.p.stop();cls.server.shutdown();cls.server.server_close()
 def setUp(self):
  self.ctx=self.browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce');self.page=self.ctx.new_page();self.errors=[]
  self.watch(self.page)
 def watch(self,p):
  p.on('pageerror',lambda e:self.errors.append(str(e)))
  p.on('console',lambda m:self.errors.append(m.text) if m.type=='error' and ('Shader' in m.text or 'VALIDATE_STATUS' in m.text) else None)
 def tearDown(self):self.ctx.close();self.assertEqual(self.errors,[])
 def click(self,name,p=None):(p or self.page).get_by_role('button',name=name,exact=True).click()
 def start(self,p=None,url=None):
  p=p or self.page;p.goto(url or self.base+'/round.html');p.locator('#loading').wait_for(state='hidden',timeout=60000)
 def inspect(self,key,p=None):
  p=p or self.page;self.click('Patch '+key,p);p.wait_for_function('!roundDiagnostics().busy')
  if p.evaluate('roundDiagnostics().view')!='close':self.click('Close view',p)
  p.wait_for_function('!roundDiagnostics().busy');expect(p.get_by_role('button',name='Propose '+key,exact=True)).to_be_visible()
 def shot(self,name):self.page.wait_for_timeout(200);self.page.screenshot(path=str(QA/(name+'.png')))
 def seek(self,value):self.page.locator('#time').fill(str(value));self.page.locator('#time').dispatch_event('input');self.page.wait_for_timeout(120)
 def test_solo_survey_recovery_fire_and_replay(self):
  self.start();self.shot('round-01-survey');self.inspect('A')
  self.click('Structure');self.page.wait_for_function('roundDiagnostics().lab.draws>0');self.click('Look through');self.page.locator('#structure-focus').select_option('liana');self.shot('round-structure')
  self.page.locator('#structure-lab').get_by_role('button',name='Back',exact=True).click();self.click('Propose A');expect(self.page.locator('#role')).to_have_value('ecology')
  self.inspect('C');self.shot('round-02-close');self.click('Propose C');self.click('Reveal plans');self.click('Forest');self.page.wait_for_function('!roundDiagnostics().busy')
  self.seek(0);self.shot('round-03-before');canvas=self.page.locator('#landscape>canvas');before=Image.open(BytesIO(canvas.screenshot()))
  self.seek(1);self.shot('round-03-recovery');after=Image.open(BytesIO(canvas.screenshot()))
  self.assertGreater(sum(ImageStat.Stat(ImageChops.difference(before,after)).mean),.05)
  self.assertGreater(self.page.evaluate('roundDiagnostics().growthPoints'),2000)
  self.click('Commit plan');self.click('Run fire');self.seek(0.15);self.shot('round-04-fire')
  self.click('Without plan');self.seek(0.45);self.shot('round-04-fire-without');self.seek(1);self.shot('round-05-without');before=Image.open(BytesIO(canvas.screenshot()))
  self.click('With plan');self.shot('round-06-with');after=Image.open(BytesIO(canvas.screenshot()))
  self.assertGreater(sum(ImageStat.Stat(ImageChops.difference(before,after)).mean),.1)
  self.assertLess(self.page.evaluate('roundDiagnostics().fire.future'),self.page.evaluate('roundDiagnostics().fire.baseline'))
  elevation=self.page.evaluate('roundDiagnostics().forest.elevation')
  self.page.mouse.move(1080,460);self.page.mouse.down();self.page.mouse.move(1190,545,steps=12);self.page.mouse.up()
  self.page.wait_for_function('(old)=>Math.abs(roundDiagnostics().forest.elevation-old)>.01',arg=elevation)
  self.shot('round-07-orbit');self.click('Close view');self.page.wait_for_function('!roundDiagnostics().busy')
  self.click('See recovery');self.seek(1);self.shot('round-08-restored-close')
  self.assertTrue(self.page.evaluate('roundDiagnostics().forest.detailPoints>2000'))
  self.page.reload();self.page.locator('#loading').wait_for(state='hidden');self.assertEqual(self.page.evaluate('roundDiagnostics().state.phase'),'committed')
  self.click('Teams');self.click('Replay the same forest');self.page.wait_for_function('roundDiagnostics().state.phase==="survey"');self.assertEqual(self.page.evaluate('roundDiagnostics().mode'),'survey')
 def test_two_team_privacy_reveal_revision_and_shared_commit(self):
  self.start();self.click('Teams');links=[self.page.get_by_label(role+' team link').input_value() for role in ['Removal','Ecology']];self.click('Back')
  contexts=[self.browser.new_context(viewport={'width':1280,'height':900},reduced_motion='reduce') for _ in links]
  try:
   pages=[c.new_page() for c in contexts]
   for p,url in zip(pages,links):self.watch(p);self.start(p,url);expect(p.locator('#role')).to_be_disabled()
   r,e=pages;self.inspect('C',r);self.click('Propose C',r);self.inspect('A',e);self.click('Propose A',e)
   e.wait_for_function('roundDiagnostics().state.ready.removal');self.assertIsNone(e.evaluate('roundDiagnostics().state.proposals.removal'))
   self.page.locator('#role').select_option('room');self.page.wait_for_function('Object.values(roundDiagnostics().state.ready).every(Boolean)');self.click('Reveal plans')
   expect(self.page.get_by_role('button',name='Commit plan',exact=True)).to_be_disabled();expect(self.page.locator('#status')).to_contain_text('-2 credits')
   e.wait_for_function('roundDiagnostics().state.phase==="review"');self.inspect('C',e);self.click('Propose C',e)
   expect(self.page.get_by_role('button',name='Commit plan',exact=True)).to_be_enabled();self.click('Commit plan')
   for p in pages:
    p.wait_for_function('roundDiagnostics().state.phase==="committed"');self.assertEqual(p.evaluate('roundDiagnostics().state.committed.left'),2)
    self.assertEqual(p.get_by_role('button',name='Propose C',exact=True).count(),0)
   self.shot('round-two-team-commit')
  finally:
   for c in contexts:c.close()
 def test_phone_without_webgl_still_explores_and_plays(self):
  b=self.p.chromium.launch(args=['--disable-webgl'])
  try:
   self.page=b.new_page(viewport={'width':390,'height':844},reduced_motion='reduce');self.watch(self.page);self.start()
   self.assertTrue(self.page.evaluate('roundDiagnostics().forest.fallback'))
   self.inspect('B');self.click('Propose B');self.click('Propose B');self.click('Reveal plans');self.click('Forest');self.page.wait_for_function('!roundDiagnostics().busy')
   self.seek(1);self.shot('round-phone-recovery');self.click('Commit plan');self.click('Run fire');self.seek(0.5);self.shot('round-phone-fire')
   self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),390)
   self.click('See recovery');self.assertEqual(self.page.evaluate('roundDiagnostics().mode'),'recovery')
  finally:b.close()

if __name__=='__main__':unittest.main()
