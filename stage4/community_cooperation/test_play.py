"""UI-only proposal playthroughs plus read-only diagnostics and screenshots."""
from pathlib import Path
import threading
import unittest
from playwright.sync_api import sync_playwright, expect
from ..serve import create_server

QA = Path('/mnt/seagate/models/pyrocene/stage4/qa-community-cooperation')


class Play(unittest.TestCase):
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
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.page.goto(self.base+'/community-cooperation/')
        self.ready()

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def ready(self, page=None):
        (page or self.page).wait_for_function('globalThis.communityCooperationDiagnostics && communityCooperationDiagnostics().state && !communityCooperationDiagnostics().busy', timeout=60000)

    def shot(self, name):
        self.page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(resolve))))')
        self.page.screenshot(path=str(QA/(name+'.png')))

    def propose(self, role, patch):
        self.page.locator('#role').select_option(role)
        self.page.locator(f'#patches [data-patch="{patch}"]').click()
        self.page.get_by_role('button', name='Propose', exact=True).click()
        expect(self.page.locator('#status')).to_contain_text('Proposed '+patch)

    def reveal(self):
        self.page.locator('#role').select_option('room')
        self.page.get_by_role('button', name='Reveal plans').click()
        expect(self.page.locator('#phase')).to_have_text('DISCUSS')

    def commit(self):
        self.page.get_by_role('button', name='Commit plan').click()
        expect(self.page.locator('#phase')).to_have_text('SHARED PLAN')
        self.ready()

    def slider(self, selector, value):
        # Native range control keyboard input, no game-state injection.
        slider = self.page.locator(selector)
        slider.focus()
        slider.press('Home')
        for _ in range(value):
            slider.press('ArrowRight')

    def test_community_cards_and_dense_close_view(self):
        for key, name in [('A','Native nursery'),('B','Cupuaçu under shade'),('C','Pasture grazing')]:
            self.page.locator(f'[data-patch="{key}"]').click()
            expect(self.page.locator('#choice-title')).to_contain_text(name)
            self.shot('choice-'+key)
        self.page.get_by_role('button', name='Close view', exact=True).click()
        self.ready()
        self.shot('pasture-close')
        self.assertGreater(self.page.evaluate('communityCooperationDiagnostics().forest.detailPoints'),10000)
        self.page.locator('#plot-plants').select_option('urochloa_brizantha')
        expect(self.page.locator('#plant-guide')).to_be_visible()
        self.page.get_by_role('tab', name='Dispersal').click()
        self.shot('plant-dispersal')

    def test_land_conflict_then_shaded_cooperation(self):
        self.propose('community','C')
        self.propose('ecology','C')
        self.propose('removal','A')
        self.reveal()
        expect(self.page.get_by_role('button',name='Commit plan')).to_be_disabled()
        expect(self.page.locator('#status')).to_contain_text('pasture')
        self.shot('land-conflict')
        self.propose('community','B')
        self.page.locator('#role').select_option('room')
        self.commit()
        expect(self.page.locator('#livelihood')).to_contain_text('shelters')
        self.page.locator('#fire-time').focus()
        self.page.locator('#fire-time').press('End')
        self.shot('restored-connection-fire')
        future=self.page.evaluate('communityCooperationDiagnostics().fire')
        self.page.locator('#without').click()
        self.shot('without-work-fire')
        self.assertGreater(self.page.evaluate('communityCooperationDiagnostics().fire'),future*2)
        self.page.locator('#with').click()
        self.slider('#recovery',0)
        self.assertGreater(self.page.evaluate('communityCooperationDiagnostics().fire'),future)
        expect(self.page.locator('#livelihood')).to_contain_text('Fire reached')
        self.page.locator('#fire-time').focus();self.page.locator('#fire-time').press('Home')
        expect(self.page.locator('#livelihood')).to_contain_text('not started')
        self.page.get_by_role('button',name='Revise plan').click()
        expect(self.page.locator('#phase')).to_have_text('DISCUSS')

    def test_nursery_and_grazing_alternatives(self):
        self.propose('ecology','A')
        self.propose('removal','A')
        self.propose('community','A')
        self.reveal();self.commit()
        expect(self.page.locator('#livelihood')).to_contain_text('buyer')
        self.shot('nursery-order')
        self.page.get_by_role('button',name='Revise plan').click()
        self.propose('community','C')
        self.page.locator('#role').select_option('room')
        self.commit()
        self.page.get_by_role('button',name='Run fire',exact=True).click()
        self.page.wait_for_function('communityCooperationDiagnostics().clock > 2')
        self.page.get_by_role('button',name='Pause',exact=True).click()
        self.shot('grazing-small-ignition')
        self.page.locator('#fire-time').focus();self.page.locator('#fire-time').press('End')
        self.shot('grazing-spread')
        expect(self.page.locator('#livelihood')).to_contain_text('feed')

    def test_team_links_hide_choices_and_sync(self):
        self.page.locator('#teams-open').click()
        links=self.page.locator('#team-links input').evaluate_all('(els)=>els.map(e=>e.value)')
        self.page.locator('#teams-back').click()
        member=self.context.new_page()
        member.goto(links[2]);self.ready(member)
        expect(member.locator('#role')).to_be_disabled()
        self.propose('ecology','C')
        self.assertIsNone(member.evaluate('communityCooperationDiagnostics().state.proposals.ecology'))
        member.locator('[data-patch="B"]').click()
        member.get_by_role('button',name='Propose',exact=True).click()
        expect(member.locator('#status')).to_contain_text('Proposed B')
        self.page.bring_to_front()
        self.page.wait_for_function('communityCooperationDiagnostics().state.proposals.community === "B"')
        self.propose('removal','A');self.reveal();self.commit()
        member.bring_to_front()
        expect(member.locator('#phase')).to_have_text('SHARED PLAN',timeout=15000)
        member.reload();self.ready(member)
        expect(member.locator('#phase')).to_have_text('SHARED PLAN')

    def test_unfunded_shade_and_unordered_nursery(self):
        self.propose('ecology','A');self.propose('removal','B');self.propose('community','B')
        self.reveal()
        expect(self.page.get_by_role('button',name='Commit plan')).to_be_disabled()
        expect(self.page.locator('#status')).to_contain_text('more credits')
        self.shot('shade-needs-investment')
        self.propose('ecology','B');self.propose('community','A')
        self.page.locator('#role').select_option('room')
        expect(self.page.locator('#status')).to_contain_text('no buyer')
        self.commit()
        expect(self.page.locator('#livelihood')).to_contain_text('No order')
        self.shot('nursery-without-order')

    def test_fire_review_without_proposals(self):
        before=self.page.evaluate('communityCooperationDiagnostics().state')
        review=self.context.new_page();review.goto(self.base+'/community-cooperation/#fire=1');self.ready(review)
        expect(review.locator('#task')).to_have_text('Follow the fire')
        self.assertEqual(review.locator('#patch-actions button,#decision button').count(),0)
        expect(review.locator('#role')).to_be_hidden()
        review.locator('#fire-time').focus();review.locator('#fire-time').press('End')
        base=review.evaluate('communityCooperationDiagnostics().fire')
        review.screenshot(path=str(QA/'review-current-forest.png'))
        review.locator('#with').click()
        self.assertLess(review.evaluate('communityCooperationDiagnostics().fire'),base)
        review.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
        review.screenshot(path=str(QA/'review-restored-C.png'))
        review.locator('#review-ignition').select_option('A')
        review.locator('#fire-time').focus();review.locator('#fire-time').press('End')
        review.locator('#teams-open').click()
        expect(review.locator('#teams h1')).to_have_text('Sources')
        expect(review.locator('#teams > p')).to_be_hidden()
        self.assertEqual(self.page.evaluate('communityCooperationDiagnostics().state'),before)

    def test_community_recap_has_fire_review_link(self):
        self.page.goto(self.base+'/community/')
        expect(self.page.locator('#community-prelude')).to_be_visible(timeout=60000)
        link=self.page.locator('#community-prelude').get_by_role('link',name='Review fire')
        expect(link).to_be_visible()
        with self.page.expect_popup() as popup:link.click()
        review=popup.value;self.ready(review)
        expect(review.locator('#task')).to_have_text('Follow the fire')

    def test_zoom_out_keeps_labels_and_leaders_fixed(self):
        self.page.locator('[data-patch="C"]').click()
        self.page.get_by_role('button',name='Close view',exact=True).click();self.ready()
        before=self.page.locator('[data-specimen]').evaluate_all('(els)=>els.map(e=>getComputedStyle(e).fontSize)')
        self.page.mouse.move(1050,600);self.page.mouse.wheel(0,2400)
        self.page.wait_for_function('communityCooperationDiagnostics().forest.distance > 1200')
        self.assertEqual(self.page.locator('[data-specimen]').evaluate_all('(els)=>els.map(e=>getComputedStyle(e).fontSize)'),before)
        heights=self.page.locator('[data-specimen]:visible').evaluate_all('(els)=>els.map(e=>parseFloat(getComputedStyle(e,"::after").height))')
        self.assertTrue(heights);self.assertTrue(all(h==12 for h in heights))
        self.shot('close-wide-no-stilts')

    def test_main_expedition_zoom_out_has_no_stilts(self):
        self.page.goto(self.base+'/expedition.html?fresh=1')
        self.page.locator('#loading').wait_for(state='hidden',timeout=60000)
        for name in ['More','Map','Explore E4','Close view']:
            self.page.get_by_role('button',name=name,exact=True).click()
        self.page.wait_for_function('pyroceneDiagnostics().detailBlend === 1')
        self.page.mouse.move(1100,600);self.page.mouse.wheel(0,2400)
        self.page.wait_for_function('pyroceneDiagnostics().distance > 1200')
        heights=self.page.locator('[data-specimen]:visible').evaluate_all('(els)=>els.map(e=>parseFloat(getComputedStyle(e,"::after").height))')
        self.assertTrue(heights);self.assertTrue(all(h==12 for h in heights))
        self.shot('expedition-wide-no-stilts')

    def test_laptop_layout_and_intact_flank(self):
        self.page.set_viewport_size({'width':1280,'height':800})
        self.page.locator('[data-patch="B"]').click()
        self.shot('laptop-cupuaçu')
        expect(self.page.get_by_role('button',name='Propose',exact=True)).to_be_in_viewport()
        self.page.set_viewport_size({'width':1440,'height':1000})
        self.page.get_by_role('button',name='Overhead',exact=True).click();self.ready()
        # A visible square immediately west of C in the overhead screenshot.
        self.page.locator('#landscape').click(position={'x':650,'y':680})
        self.ready()
        self.assertEqual(self.page.evaluate('communityCooperationDiagnostics().selected'),26)
        expect(self.page.locator('#finding')).to_contain_text('no invasive grass')
        self.assertNotIn('Marandu grass',self.page.locator('#plot-plants').inner_text())
        self.shot('flank-survey')


class SoftwarePlay(unittest.TestCase):
    def test_no_webgl_forest_close_and_fire(self):
        server=create_server(port=0)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(args=['--disable-webgl'])
                page=browser.new_page(viewport={'width':1280,'height':800},reduced_motion='reduce')
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(f'http://127.0.0.1:{server.server_port}/community-cooperation/')
                page.wait_for_function('globalThis.communityCooperationDiagnostics && communityCooperationDiagnostics().state && !communityCooperationDiagnostics().busy',timeout=60000)
                page.locator('[data-patch="C"]').click()
                page.get_by_role('button',name='Close view',exact=True).click()
                page.wait_for_function('!communityCooperationDiagnostics().busy')
                page.screenshot(path=str(QA/'software-close.png'))
                for role,patch in [('community','C'),('ecology','A'),('removal','A')]:
                    page.locator('#role').select_option(role);page.locator(f'[data-patch="{patch}"]').click()
                    page.wait_for_function('!communityCooperationDiagnostics().busy')
                    page.get_by_role('button',name='Propose',exact=True).click()
                    expect(page.locator('#status')).to_contain_text('Proposed '+patch)
                page.locator('#role').select_option('room')
                page.get_by_role('button',name='Reveal plans').click()
                page.get_by_role('button',name='Commit plan').click()
                page.wait_for_function('!communityCooperationDiagnostics().busy')
                page.locator('#fire-time').focus();page.locator('#fire-time').press('End')
                expect(page.locator('#burned')).to_contain_text('ha burned')
                page.wait_for_function('communityCooperationDiagnostics().renderedFireTime === 1')
                page.screenshot(path=str(QA/'software-fire.png'))
                self.assertEqual(errors,[])
                browser.close()
        finally:
            server.shutdown();server.server_close()


if __name__ == '__main__':
    unittest.main()
