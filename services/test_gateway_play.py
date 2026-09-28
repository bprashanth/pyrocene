"""Play through the single-host gateway on temporary ports, including stage jumps."""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright, expect
from services.test_gateway import GatewayTests, AUTH
from stage2 import server as room

QA=Path('/tmp/pyrocene-event-qa')

class GatewayPlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        GatewayTests.setUpClass()
        cls.base=f'http://127.0.0.1:{GatewayTests.port}'
        cls.old_fast=room.FAST;room.FAST=True
        cls.pw=sync_playwright().start()
        cls.browser=cls.pw.chromium.launch(args=['--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        QA.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.pw.stop();room.FAST=cls.old_fast;GatewayTests.tearDownClass()

    def setUp(self):
        room.ROOM=room.Room(seed=5,stage=1)
        self.context=self.browser.new_context(viewport={'width':1365,'height':900},http_credentials=dict(zip(['username','password'],AUTH.split(':',1))))
        self.page=self.context.new_page();self.errors=[]
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))

    def tearDown(self):
        self.context.close();self.assertEqual(self.errors,[])

    def shot(self,name):self.page.screenshot(path=str(QA/(name+'.png')))

    def test_01_stage2_no_action_demo_then_stage1_then_stage2(self):
        p=self.page;p.goto(self.base+'/start')
        self.shot('start')
        p.locator('a[href="/gm?stage=2"]').click()
        expect(p.locator('#phase')).to_have_text('stage 2 - lobby')
        p.locator('#seed').click();expect(p.locator('#count')).to_have_text('12')
        p.locator('#start').click()
        projector=self.context.new_page();projector.goto(self.base+'/projector')
        before=room.ROOM.game.view()
        def settle():
            p.wait_for_function('S && S.mode !== "playing"',timeout=20000)
            if p.locator('#advance').is_visible():
                p.locator('#advance').click()
                p.wait_for_function('S && S.mode === "idle"',timeout=20000)
        for _ in range(10):
            settle()
            if room.ROOM.game.phase=='ended':break
            expect(p.locator('#finishnight')).to_be_visible();p.locator('#finishnight').click()
            p.wait_for_function('S && (S.step === "day" || S.phase === "ended")')
            settle()
            p.wait_for_function('document.querySelector("#phase").textContent.includes("game over") || !document.querySelector("#day").hidden',timeout=20000)
            if room.ROOM.game.phase=='ended':break
            # Hunt with no one voted out means no removal or resilience work.
            p.locator('[name=choice][value=hunt]').check();p.locator('#finishvote').click()
            p.wait_for_function('S && (S.step === "night" || S.phase === "ended")')
        settle()
        self.assertGreater(room.ROOM.game.round,1)
        self.assertNotEqual(before,room.ROOM.game.view())
        self.assertTrue(any(rec.get('fire') for rec in room.ROOM.game.events))
        projector.screenshot(path=str(QA/'stage2-no-action-map.png'))
        self.shot('stage2-no-action-gm')
        p.goto(self.base+'/start');p.locator('a[href="/gm?stage=1"]').click()
        expect(p.locator('#phase')).to_have_text('stage 1 - lobby');expect(p.locator('#count')).to_have_text('12')
        self.shot('back-to-stage1')
        p.locator('#start').click();expect(p.locator('#phase')).to_have_text('stage 1 - in play')
        p.goto(self.base+'/start');p.locator('a[href="/gm?stage=2"]').click()
        expect(p.locator('#phase')).to_have_text('stage 2 - lobby')
        self.shot('jump-to-stage2')
        p.locator('#backto1').click();expect(p.locator('#phase')).to_have_text('stage 1 - lobby')
        p.reload();expect(p.locator('#phase')).to_have_text('stage 1 - lobby')

    def test_02_stage4_explore_room_commit_prelude_game(self):
        p=self.page;p.goto(self.base+'/start');p.locator('#stage4').click()
        p.locator('#loading').wait_for(state='hidden',timeout=60000)
        expect(p).to_have_url(self.base+'/stage4/expedition.html')
        p.locator('#role').select_option('room');p.locator('#game-mode').select_option('play')
        p.wait_for_function('globalThis.roundDiagnostics && roundDiagnostics().state && !roundDiagnostics().busy',timeout=60000)
        if p.locator('#briefing').is_visible():p.locator('#briefing-begin').click()
        for team in ['ecology','removal','community']:
            p.locator('#plan-'+team).select_option('A')
            p.wait_for_function('(t)=>roundDiagnostics().state.proposals[t]==="A"',arg=team)
        p.locator('#teams-open').click()
        for link in p.locator('#team-links input').all():self.assertIn('/stage4/round.html#',link.input_value())
        p.locator('#teams-back').click()
        p.get_by_role('button',name='Commit plan',exact=True).click()
        p.wait_for_function('roundDiagnostics().state.phase==="committed" && !roundDiagnostics().busy')
        p.locator('#recovery').focus();p.locator('#recovery').press('End')
        self.shot('stage4-committed')
        p.locator('#recap-open').click();p.locator('#recap-time-open').click();p.locator('#recap-space-open').click()
        self.shot('stage4-prelude')
        p.locator('#recap-play').click();p.wait_for_url('**/stage4/strategy.html#*')
        p.locator('#loading').wait_for(state='hidden',timeout=60000)
        p.locator('#begin').click();self.shot('stage4-game')
        p.locator('#stage').select_option('play');p.wait_for_url('**/stage4/round.html#*')
        p.wait_for_function('globalThis.roundDiagnostics && roundDiagnostics().state && !roundDiagnostics().busy',timeout=60000)
        self.assertEqual(p.evaluate('roundDiagnostics().state.phase'),'committed')

    def test_03_stage3_boots_at_local_prefix(self):
        p=self.page;p.goto(self.base+'/start');p.locator('#stage3').click()
        self.assertTrue(p.evaluate('crossOriginIsolated'))
        # Wait for the game's actual input prompt, not just its HTML shell.
        p.locator('.xterm-screen').wait_for(timeout=30000)
        p.locator('#hint.show').wait_for(timeout=120000)
        p.keyboard.press('Enter');p.locator('#boot').wait_for(state='hidden')
        self.shot('stage3-browser-game')

if __name__=='__main__':unittest.main()
