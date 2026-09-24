"""Main-game integration, played through visible UI with screenshot review."""
from pathlib import Path
import threading
import unittest
from playwright.sync_api import sync_playwright, expect
from .serve import create_server

QA = Path('/mnt/seagate/models/pyrocene/stage4/qa-cooperation-integrated')


class CooperationPlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        QA.mkdir(parents=True, exist_ok=True)
        cls.server = create_server(port=0)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.server.shutdown(); cls.server.server_close()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width':1440, 'height':1000}, reduced_motion='reduce')
        self.page = self.context.new_page(); self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.on('console', lambda m: self.errors.append(m.text) if m.type == 'error' and 'Shader' in m.text else None)
        self.page.goto(self.base+'/round.html')
        self.ready(); self.begin()

    def tearDown(self):
        self.context.close(); self.assertEqual(self.errors, [])

    def ready(self, page=None):
        p=page or self.page
        p.wait_for_function('globalThis.roundDiagnostics && roundDiagnostics().state && !roundDiagnostics().busy', timeout=60000)
        if p.locator('#cooperation-recap').is_visible():
            p.screenshot(path=str(QA/'recap-I.png'))
            expect(p.locator('#earnings-health circle')).to_have_count(21)
            p.locator('#recap-one-back').click()

    def commit(self):
        self.page.get_by_role('button',name='Commit plan').click()
        self.page.wait_for_function('roundDiagnostics().state.phase === "committed"')
        self.ready()

    def begin(self, page=None):
        p = page or self.page
        if p.locator('#briefing').is_visible(): p.locator('#briefing-begin').click()

    def role(self, role):
        self.page.locator('#role').select_option(role); self.begin()

    def propose(self, role, key):
        self.role(role); self.page.locator(f'[data-patch="{key}"]').click()
        self.page.get_by_role('button', name='Propose', exact=True).click()
        expect(self.page.locator('#status')).to_contain_text('Proposed '+key)

    def shot(self, name):
        self.page.evaluate('() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')
        self.page.screenshot(path=str(QA/(name+'.png')))

    def seek(self, name, end=True):
        self.page.locator('#'+name).focus(); self.page.locator('#'+name).press('End' if end else 'Home')
        expect(self.page.locator('#'+name)).to_have_value(self.page.locator('#'+name).get_attribute('max' if end else 'min'))
        if name=='fire-time': self.assertEqual(self.page.evaluate('roundDiagnostics().clock'),24 if end else 0)

    def test_three_roles_conflict_review_preview_and_original_fire_renderer(self):
        self.assertEqual(self.page.evaluate('roundDiagnostics().renderer'), 'RoundForest')
        self.assertEqual(self.page.locator('#game-mode [value="negligence"]').count(), 0)
        self.role('community'); self.page.locator('[data-patch="B"]').click()
        expect(self.page.locator('#choice-title')).to_contain_text('Shade-grown coffee')
        expect(self.page.locator('#finding')).to_contain_text('shade trees')
        self.shot('community-coffee')
        self.propose('community','C'); self.propose('ecology','C'); self.propose('removal','A')
        self.role('room'); self.page.get_by_role('button',name='Reveal plans').click()
        expect(self.page.get_by_role('button',name='Commit plan')).to_be_disabled()
        expect(self.page.locator('#status')).to_contain_text('pasture')
        self.shot('land-use-conflict')
        self.propose('community','B'); self.role('room')
        expect(self.page.locator('#outcomes')).to_be_hidden()
        expect(self.page.locator('#patches')).to_be_hidden()
        for key in ['A','B','C']:
            self.page.locator('#plan-ecology').select_option(key)
            self.page.wait_for_function('(key)=>roundDiagnostics().state.proposals.ecology===key',arg=key)
            self.assertIsNone(self.page.evaluate('roundDiagnostics().previewPlan'))
            if key=='B': expect(self.page.get_by_role('button',name='Commit plan')).to_be_disabled()
        self.commit()
        self.seek('recovery')
        self.assertEqual(self.page.locator('#run-fire').count(),0)
        self.assertEqual(self.page.evaluate('roundDiagnostics().projection.shadeHeight'),12)
        self.assertEqual(self.page.evaluate('roundDiagnostics().projection.coffeeHeight'),2)
        self.assertEqual(self.page.evaluate('roundDiagnostics().ignition'),27)
        self.seek('fire-time'); mature = self.page.evaluate('roundDiagnostics().fire')
        self.shot('restored-C-original-fire')
        self.seek('recovery',False)
        self.assertGreater(self.page.evaluate('roundDiagnostics().fire'),mature)
        self.shot('young-C-fire')
        self.page.get_by_role('button',name='Without plan',exact=True).click()
        self.shot('without-plan-original-fire')
        self.page.reload(); self.ready()
        self.assertEqual(self.page.evaluate('roundDiagnostics().state.phase'),'committed')

    def test_three_private_links_and_expedition_reset(self):
        self.page.locator('#teams-open').click()
        links = self.page.locator('#team-links input').evaluate_all('(els)=>els.map(e=>e.value)')
        self.assertEqual(len(links),4); self.assertTrue(all('/round.html#' in link for link in links))
        self.page.locator('#teams-back').click()
        member = self.context.new_page(); member.goto(links[2]); self.ready(member); self.begin(member)
        expect(member.locator('#role')).to_have_value('community'); expect(member.locator('#role')).to_be_disabled()
        self.propose('ecology','C')
        member.bring_to_front()
        member.wait_for_function('roundDiagnostics().state.ready.ecology')
        self.assertIsNone(member.evaluate('roundDiagnostics().state.proposals.ecology'))
        member.locator('[data-patch="B"]').click(); member.get_by_role('button',name='Propose',exact=True).click()
        self.page.bring_to_front(); self.page.wait_for_function('roundDiagnostics().state.ready.community')
        self.propose('removal','A'); self.role('room'); self.page.get_by_role('button',name='Reveal plans').click()
        self.commit()
        member.bring_to_front(); member.wait_for_function('roundDiagnostics().state.phase === "committed"')
        self.page.bring_to_front(); self.page.locator('#game-mode').select_option('expedition')
        self.page.wait_for_url('**/expedition.html?fresh=1#*'); self.page.locator('#loading').wait_for(state='hidden')
        member.bring_to_front(); member.wait_for_url(lambda url: '/expedition.html' in url)
        self.page.bring_to_front(); self.page.locator('#game-mode').select_option('play'); self.ready(); self.begin()
        self.assertFalse(any(self.page.evaluate('roundDiagnostics().state.ready').values()))
        self.assertEqual(self.page.evaluate('roundDiagnostics().state.generation'),1)

    def test_laptop_grazing_ignition(self):
        self.page.set_viewport_size({'width':1280,'height':800})
        self.propose('community','C'); self.propose('ecology','A'); self.propose('removal','A'); self.role('room')
        self.page.get_by_role('button',name='Reveal plans').click(); self.commit()
        expect(self.page.locator('#fire-controls')).to_be_hidden()
        self.page.locator('#recovery').focus();self.page.locator('#recovery').press('ArrowRight')
        self.page.wait_for_function('roundDiagnostics().clock > 0');self.shot('laptop-small-ignition')
        self.seek('recovery');expect(self.page.locator('#fire-note')).to_contain_text('pasture C')
        self.shot('laptop-grazing-spread')

    def test_debt_recap_and_joint_projection(self):
        for role,key in [('ecology','A'),('removal','C'),('community','B')]: self.propose(role,key)
        self.role('room'); self.page.get_by_role('button',name='Reveal plans').click()
        expect(self.page.locator('#terms')).to_contain_text('Debt:')
        expect(self.page.get_by_role('button',name='Commit plan')).to_be_enabled()
        self.shot('debt-review'); self.commit()
        self.page.locator('#game-mode').select_option('recap-one')
        old=self.page.evaluate('roundDiagnostics().state.revision')
        self.page.locator('#earnings-health circle').first.click()
        expect(self.page.locator('#recap-plan')).to_contain_text('Restore')
        self.assertEqual(old,self.page.evaluate('roundDiagnostics().state.revision'))
        self.shot('debt-recap'); self.page.locator('#recap-one-back').click()
        # Twenty actual keyboard steps reach year two; ten more clear it again.
        self.page.locator('#recovery').focus()
        for _ in range(20): self.page.locator('#recovery').press('ArrowRight')
        self.assertGreater(self.page.evaluate('roundDiagnostics().projection.removalCover'),.7)
        self.shot('joint-projection-year-two')
        for _ in range(10): self.page.locator('#recovery').press('ArrowRight')
        self.assertEqual(self.page.evaluate('roundDiagnostics().projection.removalCover'),0)
        self.shot('joint-projection-year-three')
        self.seek('recovery')
        self.assertGreater(self.page.evaluate('roundDiagnostics().projection.coffeePoints'),100)
        self.assertEqual(self.page.evaluate('roundDiagnostics().projection.restoration'),1)
        self.page.get_by_role('button',name='Forest',exact=True).click(); self.ready(); self.shot('joint-projection-year-ten')
        self.page.get_by_role('button',name='Without plan',exact=True).click()
        self.assertIsNone(self.page.evaluate('roundDiagnostics().projection'))
        expect(self.page.locator('#livelihood')).to_contain_text('without the proposed work')

    def test_survey_flanks_structure_and_species(self):
        self.page.locator('[data-patch="C"]').click(); self.page.get_by_role('button',name='Close view',exact=True).click(); self.ready()
        expect(self.page.locator('#finding')).to_contain_text('continuous layer')
        self.shot('C-close-fuel')
        self.page.locator('#plot-plants').select_option('urochloa_brizantha')
        self.page.get_by_role('tab',name='Dispersal',exact=True).click(); self.shot('C-dispersal')
        self.page.locator('#record-close').click(); self.page.get_by_role('button',name='Structure',exact=True).click()
        self.page.wait_for_function('roundDiagnostics().lab.draws > 0'); self.shot('C-structure')
        self.page.locator('#structure-lab').get_by_role('button',name='Back',exact=True).click()
        self.page.get_by_role('button',name='Overhead',exact=True).click(); self.ready()
        self.page.locator('#landscape').click(position={'x':650,'y':680}); self.ready()
        self.assertEqual(self.page.evaluate('roundDiagnostics().selected'),26)
        expect(self.page.locator('#finding')).to_contain_text('no invasive grass')
        self.assertNotIn('Marandu grass',self.page.locator('#plot-plants').inner_text())
        self.shot('survey-flank')
        self.page.get_by_role('button',name='Close view',exact=True).click(); self.ready()
        self.page.get_by_role('button',name='Structure',exact=True).click()
        expect(self.page.locator('.structure-panel').nth(1).locator('.structure-caption')).to_contain_text('no invasive grass')

    def test_expedition_entry_community_briefing_recap_combined(self):
        self.page.goto(self.base+'/expedition.html?fresh=1'); self.page.locator('#loading').wait_for(state='hidden',timeout=60000)
        x=self.page.locator('#game-mode').bounding_box()['x']
        self.assertGreater(x,900); self.shot('expedition-header-right')
        self.assertEqual(self.page.locator('#game-mode [value="negligence"]').count(),0)
        self.page.locator('#role').select_option('community'); self.page.locator('#game-mode').select_option('play'); self.ready()
        expect(self.page.locator('#briefing-role')).to_have_text('Role: community'); self.shot('community-briefing'); self.begin()
        self.assertLess(abs(self.page.locator('#game-mode').bounding_box()['x']-x),25)
        before = self.page.evaluate('roundDiagnostics().state')
        self.page.locator('#game-mode').select_option('recap')
        expect(self.page.get_by_text('Why the edge keeps burning',exact=True)).to_be_visible()
        # Close the recap without starting another game.
        self.page.keyboard.press('Escape')
        self.assertEqual(self.page.evaluate('roundDiagnostics().state'),before)
        self.page.locator('#game-mode').select_option('combined')
        self.page.wait_for_url('**/strategy.html#*'); self.page.locator('#loading').wait_for(state='hidden',timeout=60000)
        expect(self.page.locator('#strategy-intro')).to_be_visible()

    def test_negligence_flag_restores_archived_flow(self):
        self.page.goto(self.base+'/round.html?negligence=1'); self.page.locator('#loading').wait_for(state='hidden',timeout=60000); self.begin()
        self.assertEqual(self.page.locator('#game-mode [value="negligence"]').count(),1)
        self.assertEqual(self.page.locator('#role [value="community"]').count(),0)
        self.assertEqual(self.page.evaluate('roundDiagnostics().state.mission'),'cooperation')
        for _ in range(2):
            self.page.locator('[data-patch="A"]').click()
            self.page.wait_for_function('!roundDiagnostics().busy')
            if self.page.evaluate('roundDiagnostics().view')!='close':
                self.page.get_by_role('button',name='Close view',exact=True).click()
            self.page.wait_for_function('!roundDiagnostics().busy')
            self.page.get_by_role('button',name='Propose',exact=True).click()
            self.page.locator('#briefing[open]').wait_for(); self.begin()
        self.page.get_by_role('button',name='Reveal plans').click()
        self.page.get_by_role('button',name='Commit plan').click()
        self.page.locator('#game-mode').select_option('negligence')
        self.page.wait_for_function('roundDiagnostics().state.mission === "negligence"')
        self.begin(); self.shot('archived-negligence-flag')


class CooperationSoftware(CooperationPlay):
    def shot(self, name):
        super().shot('software-'+name)

    @classmethod
    def setUpClass(cls):
        super().setUpClass(); cls.browser.close()
        cls.browser = cls.pw.chromium.launch(args=['--disable-webgl','--disable-webgl2'])

    def test_software_fire(self):
        self.propose('community','C'); self.propose('ecology','A'); self.propose('removal','A'); self.role('room')
        self.page.get_by_role('button',name='Reveal plans').click(); self.commit()
        self.seek('recovery'); self.shot('software-original-fire')
        self.assertGreater(self.page.evaluate('roundDiagnostics().fire'),0)
