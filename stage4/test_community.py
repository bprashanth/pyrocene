"""Community UI play, separate saves and real point-cloud inspection."""
import threading
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from .serve import create_server

QA=Path('/mnt/seagate/models/pyrocene/stage4/qa-community')

class CommunityPlay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  QA.mkdir(parents=True,exist_ok=True)
  cls.server=create_server(port=0)
  threading.Thread(target=cls.server.serve_forever,daemon=True).start()
  cls.base=f'http://127.0.0.1:{cls.server.server_port}'
  cls.p=sync_playwright().start()
  cls.browser=cls.p.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 @classmethod
 def tearDownClass(cls):
  cls.browser.close();cls.p.stop();cls.server.shutdown();cls.server.server_close()
 def setUp(self):
  self.context=self.browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
  self.page=self.context.new_page();self.errors=[]
  self.page.on('pageerror',lambda e:self.errors.append(str(e)))
 def tearDown(self):
  self.context.close();self.assertEqual(self.errors,[])
 def ready(self):self.page.wait_for_function('globalThis.communityDiagnostics && !communityDiagnostics().busy')
 def start(self,enterprise='shade',seed=113):
  self.page.goto(self.base+f'/community/#prototype=1&fresh=1&seed={seed}')
  self.page.locator('#loading').wait_for(state='hidden',timeout=60000)
  self.page.locator(f'[data-enterprise="{enterprise}"]').click()
  self.page.locator('#begin').click();self.ready()
 def shot(self,name):self.page.screenshot(path=str(QA/(name+'.png')))
 def test_three_page_recap_finishes_without_starting_community(self):
  self.page.goto(self.base+'/community/#fresh=1')
  self.page.locator('#loading').wait_for(state='hidden',timeout=60000)
  expect(self.page.locator('#community-prelude')).to_be_visible()
  expect(self.page.locator('#prelude-title')).to_have_text('Why the edge keeps burning')
  expect(self.page.locator('#prelude-back')).to_be_hidden()
  self.assertEqual(self.page.locator('#community-prelude img').count(),0)
  expect(self.page.locator('#prelude-step')).to_have_text('RECAP / 1 OF 3')
  expect(self.page.locator('#prelude-text')).to_contain_text('the last stage')
  before=self.page.evaluate('communityDiagnostics().game')
  self.shot('recap-edge')
  self.page.locator('.prelude-sources summary').click()
  expect(self.page.locator('#prelude-sources-body')).to_contain_text('NIDM')
  self.page.locator('.prelude-sources summary').click()
  self.page.locator('#prelude-next').click()
  expect(self.page.locator('#prelude-title')).to_have_text('How fire reaches the forest')
  expect(self.page.locator('#prelude-caption')).to_have_text('Cooperation - simulated fire scar')
  expect(self.page.locator('#prelude-map')).to_have_attribute('aria-label',__import__('re').compile('.*fuel corridor.*'))
  self.shot('recap-connectivity')
  self.page.locator('#prelude-back').click()
  expect(self.page.locator('#prelude-title')).to_have_text('Why the edge keeps burning')
  self.page.locator('#prelude-next').click();self.page.locator('#prelude-next').click()
  expect(self.page.locator('#prelude-title')).to_have_text('Forest Stewards')
  expect(self.page.locator('#prelude-text')).to_contain_text('Aadhimalai')
  expect(self.page.locator('#prelude-next')).to_have_text('Finish')
  expect(self.page.locator('#strategy-intro')).not_to_be_visible()
  self.assertEqual(self.page.evaluate('communityDiagnostics().game'),before)
  self.shot('recap-stewards')
  self.page.locator('#prelude-next').click();self.page.wait_for_url('**/strategy.html')
 def choose(self,id):
  self.page.locator(f'.strategy-pins button').filter(has_text=__import__('re').compile('^'+chr(65+id//12)+str(id%12+1)+'$')).click();self.ready()
  self.assertEqual(self.page.evaluate('communityDiagnostics().selected'),id)
 def action(self,verb):
  self.page.locator('#next-season' if verb=='wait' else f'[data-action="{verb}"]').click();self.ready()
  expect(self.page.locator('#toast')).to_be_hidden()
 def test_direct_entry_choices_and_centered_strip(self):
  self.start();expect(self.page).to_have_title('Community - Pyrocene')
  expect(self.page.locator('#enterprise-name')).to_have_text('Shade crops')
  box=self.page.locator('#ledger-strip').bounding_box();self.assertAlmostEqual(box['x']+box['width']/2,720,delta=1)
  self.assertEqual(self.page.locator('.buffer-outlines polygon').count(),2)
  self.shot('opening-shade')
  self.page.locator('#replay-open').click();self.page.locator('#retry').click()
  self.page.locator('[data-enterprise="nursery"]').click();self.page.locator('#begin').click();self.ready()
  expect(self.page.locator('#enterprise-name')).to_have_text('Seed nursery')
  self.assertEqual(self.page.evaluate('communityDiagnostics().game.turn'),0)
 def test_partnership_close_species_and_refresh(self):
  self.start();before=self.page.evaluate('communityDiagnostics().game.credits')
  self.action('partner');self.assertEqual(self.page.evaluate('communityDiagnostics().game.credits'),before-5)
  expect(self.page.locator('#community-account')).to_be_visible()
  self.page.get_by_role('button',name='Close view',exact=True).click();self.ready()
  self.assertGreater(self.page.evaluate('communityDiagnostics().forest.detailPoints'),10000)
  self.page.locator('#plot-plants').select_option('theobroma_grandiflorum')
  expect(self.page.locator('#plant-guide')).to_contain_text('Cupuaçu')
  self.page.get_by_role('tab',name='Dispersal').click();self.shot('buffer-dispersal')
  self.page.get_by_role('tab',name='Germination').click();self.shot('buffer-germination')
  self.page.locator('#record-close').click();self.shot('young-buffer-close')
  before=self.page.evaluate('communityDiagnostics().game');self.page.reload();self.ready()
  self.assertEqual(self.page.evaluate('communityDiagnostics().game'),before)
 def test_local_income_never_enters_player_wallet(self):
  self.start('nursery');self.action('partner')
  credits=self.page.evaluate('communityDiagnostics().game.credits')
  for _ in range(6):self.action('wait')
  self.assertEqual(self.page.evaluate('communityDiagnostics().game.credits'),credits)
  self.assertGreater(self.page.evaluate('communityDiagnostics().game.plots[56].community.earned'),0)
  self.assertGreater(self.page.evaluate('communityDiagnostics().game.plots[56].community.upkeep'),0)
  self.shot('nursery-account')
 def test_cpu_close_and_buffer_outline(self):
  browser=self.p.chromium.launch(args=['--disable-webgl'])
  try:
   self.page=browser.new_page(viewport={'width':1280,'height':900},reduced_motion='reduce')
   self.page.on('pageerror',lambda e:self.errors.append(str(e)))
   self.start();self.action('partner')
   self.page.get_by_role('button',name='Close view',exact=True).click();self.ready()
   self.assertTrue(self.page.evaluate('communityDiagnostics().forest.fallback'))
   self.assertGreater(self.page.evaluate('communityDiagnostics().forest.detailPoints'),10000)
   self.shot('cpu-buffer-close')
  finally:browser.close()
 def test_success_offers_replay_without_forcing_empty_turns(self):
  self.start(seed=991)
  self.page.get_by_role('button',name='Overhead',exact=True).click();self.ready()
  for id,verb in [(56,'partner'),(68,'partner'),(67,'remove'),(55,'remove'),(55,'wait'),(55,'wait'),(67,'remove')]:
   self.choose(id);self.action(verb)
  expect(self.page.locator('#replay-dialog')).to_be_visible()
  expect(self.page.locator('#run-summary')).to_contain_text('2 of 2 young edge plots recovered')
  self.assertEqual(self.page.evaluate('communityDiagnostics().game.turn'),7)
  self.page.get_by_role('button',name='Keep exploring').click()
  self.choose(56);self.page.get_by_role('button',name='Close view',exact=True).click();self.ready()
  self.shot('recovered-shade-buffer-close')
  self.action('wait');expect(self.page.locator('#replay-dialog')).not_to_be_visible()
 def test_prototype_does_not_change_combined_save(self):
  self.page.goto(self.base+'/strategy.html#fresh=1')
  self.page.locator('#loading').wait_for(state='hidden',timeout=60000);self.page.locator('#begin').click()
  self.page.wait_for_function('!strategyDiagnostics().busy')
  self.page.locator('#patch-actions button').first.click();self.page.wait_for_function('!strategyDiagnostics().busy')
  before=self.page.evaluate('strategyDiagnostics().game')
  self.start();self.action('partner')
  self.page.get_by_role('link',name='Back to Combined').click()
  self.page.wait_for_url('**/strategy.html')
  self.page.locator('#loading').wait_for(state='hidden',timeout=60000)
  self.page.wait_for_function('globalThis.strategyDiagnostics && !strategyDiagnostics().busy')
  self.assertEqual(self.page.evaluate('strategyDiagnostics().game'),before)
 def test_recap_does_not_overwrite_parked_prototype_save(self):
  self.start(seed=113);self.action('partner')
  before=self.page.evaluate('communityDiagnostics().game')
  self.page.goto(self.base+'/community/#prelude=1&seed=999')
  self.page.reload()
  self.page.locator('#loading').wait_for(state='hidden',timeout=60000)
  expect(self.page.locator('#community-prelude')).to_be_visible()
  self.page.goto(self.base+'/community/#prototype=1&seed=113')
  self.page.reload()
  self.page.locator('#loading').wait_for(state='hidden',timeout=60000);self.ready()
  self.assertEqual(self.page.evaluate('communityDiagnostics().game'),before)
 def test_main_combined_recap_returns_to_same_map_and_state(self):
  self.page.goto(self.base+'/strategy.html#fresh=1')
  self.page.locator('#loading').wait_for(state='hidden',timeout=60000)
  self.page.locator('#begin').click();self.page.wait_for_function('!strategyDiagnostics().busy')
  before=self.page.evaluate('strategyDiagnostics().game');url=self.page.url
  self.page.locator('#stage').select_option('recap')
  for _ in range(2):self.page.locator('#prelude-next').click()
  expect(self.page.locator('#prelude-text')).to_contain_text('IDESAM and WeForest')
  expect(self.page.locator('#prelude-map')).to_have_attribute('aria-label',__import__('re').compile('.*forest edge.*'))
  self.shot('main-recap-stewards')
  self.page.locator('#prelude-next').click()
  expect(self.page.locator('#community-prelude')).not_to_be_visible()
  self.assertEqual(self.page.url,url)
  self.assertEqual(self.page.evaluate('strategyDiagnostics().game'),before)
  expect(self.page.locator('#stage')).to_have_value('combined')

if __name__=='__main__':unittest.main()
