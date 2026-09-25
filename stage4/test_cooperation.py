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
        self.page.wait_for_function('!roundDiagnostics().busy')
        expect(self.page.locator('#cooperation-recap')).not_to_be_visible()
        expect(self.page.locator('#recovery')).to_be_visible()
        expect(self.page.locator('#fire-time')).to_be_visible()
        expect(self.page.locator('#recap-open')).to_be_visible()
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
        self.role('room')
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
        self.assertEqual(self.page.locator('#with,#without').count(),0)
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
        self.propose('removal','A'); self.role('room')
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
        self.commit()
        expect(self.page.locator('#fire-controls')).to_be_visible()
        self.page.locator('#recovery').focus();self.page.locator('#recovery').press('ArrowRight')
        self.page.wait_for_function('roundDiagnostics().clock > 0');self.shot('laptop-small-ignition')
        self.seek('recovery');expect(self.page.locator('#fire-note')).to_contain_text('pasture C')
        self.shot('laptop-grazing-spread')

    def test_debt_recap_and_joint_projection(self):
        for role,key in [('ecology','A'),('removal','C'),('community','B')]: self.propose(role,key)
        self.role('room')
        expect(self.page.locator('#terms')).to_contain_text('Debt:')
        expect(self.page.get_by_role('button',name='Commit plan')).to_be_enabled()
        self.shot('debt-review'); self.commit()
        self.page.get_by_role('button',name='Recap',exact=True).click()
        expect(self.page.locator('#cooperation-recap li')).to_have_count(0)
        copy=self.page.locator('#cooperation-recap .prelude-copy').bounding_box()
        graph=self.page.locator('#cooperation-recap figure').bounding_box()
        self.assertGreater(graph['width'],copy['width']*1.7)
        expect(self.page.locator('#cooperation-recap')).not_to_contain_text('Returning crews')
        expect(self.page.locator('#cooperation-recap')).not_to_contain_text('These are game estimates')
        old=self.page.evaluate('roundDiagnostics().state.revision')
        self.page.locator('#earnings-health circle').first.click()
        expect(self.page.locator('#recap-plan')).to_contain_text('Restore')
        self.assertEqual(old,self.page.evaluate('roundDiagnostics().state.revision'))
        self.shot('debt-recap'); self.page.locator('#recap-one-back').click()
        # Two full, smooth clearance/return cycles across the slider.
        self.page.locator('#recovery').focus()
        for step,year in enumerate([2.5,5,7.5,10]):
            for _ in range(25): self.page.locator('#recovery').press('ArrowRight')
            cover=self.page.evaluate('roundDiagnostics().projection.removalCover')
            if step%2==0: self.assertEqual(cover,0)
            else: self.assertGreater(cover,.8)
            self.shot('two-cycles-year-'+str(year))
        self.seek('recovery')
        self.assertGreater(self.page.evaluate('roundDiagnostics().projection.coffeePoints'),100)
        self.assertEqual(self.page.evaluate('roundDiagnostics().projection.restoration'),1)
        self.page.get_by_role('button',name='Forest',exact=True).click(); self.ready(); self.shot('joint-projection-year-ten')
        self.assertEqual(self.page.locator('#with,#without').count(),0)
        self.page.get_by_role('button',name='Revise plan').click()
        expect(self.page.locator('#plan-community')).to_be_enabled()
        self.page.locator('#plan-community').select_option('A')
        self.page.wait_for_function('roundDiagnostics().state.proposals.community === "A"')
        self.commit()
        self.assertEqual(self.page.evaluate('roundDiagnostics().projection.coffeePoints'),0)

    def test_room_starts_editable_and_plain_ecology_copy(self):
        self.role('ecology')
        for key,copy in [('A','healthy natives and newly arriving invasives'),('B','degraded into open land')]:
            self.page.locator(f'[data-patch="{key}"]').click()
            expect(self.page.locator('#finding')).to_contain_text(copy)
        self.role('room')
        self.assertEqual(self.page.get_by_role('button',name='Reveal plans').count(),0)
        expect(self.page.get_by_role('button',name='Commit plan')).to_be_disabled()
        for team,key in [('ecology','A'),('removal','C'),('community','B')]:
            expect(self.page.locator('#plan-'+team)).to_be_enabled()
            expect(self.page.locator('#plan-'+team)).to_have_value('')
            self.page.locator('#plan-'+team).select_option(key)
            self.page.wait_for_function('([team,key])=>roundDiagnostics().state.proposals[team]===key',arg=[team,key])
        self.shot('direct-room-edit');self.commit()

    def test_tradeoff_stories_and_recap_time_are_read_only(self):
        self.page.set_viewport_size({'width':1280,'height':800})
        self.role('room')
        for team in ['ecology','removal','community']:
            self.page.locator('#plan-'+team).select_option('A')
            self.page.wait_for_function('(team)=>roundDiagnostics().state.proposals[team] === "A"',arg=team)
        self.commit();self.page.locator('#game-mode').select_option('recap-one')
        expect(self.page.locator('#cooperation-recap')).to_have_attribute('aria-label','Prelude I')
        expect(self.page.locator('#recap-map')).to_be_visible()
        before=self.page.evaluate('({state:roundDiagnostics().state,years:roundDiagnostics().years,clock:roundDiagnostics().clock})')
        for key,copy in [('AAA','All three teams'),('CCB','Restoring C helps shelter'),('CAB','Removal in A brings a large return')]:
            self.page.locator(f'#earnings-health [data-plan="{key}"]').click()
            expect(self.page.locator('#recap-story')).to_contain_text(copy)
            self.page.mouse.move(20,20)
            expect(self.page.locator(f'#earnings-health [data-plan="{key}"]')).to_have_attribute('aria-pressed','true')
            self.shot('recap-tradeoff-'+key)
        self.page.locator('#recap-time-open').click()
        expect(self.page.locator('#recap-time-chart [data-series]')).to_have_count(6)
        expect(self.page.locator('#recap-year')).to_have_count(0)
        expect(self.page.locator('#recap-story')).to_contain_text('6 credits')
        expect(self.page.locator('#recap-map')).to_be_visible()
        map_colours=self.page.locator('#recap-map').evaluate('(e)=>new Set(e.getContext("2d").getImageData(0,0,e.width,e.height).data).size')
        self.assertGreater(map_colours,50)
        for choice in ['nursery','coffee','sequence']:
            self.page.locator(f'[data-choice="{choice}"]').click()
            expect(self.page.locator(f'[data-choice="{choice}"]')).to_have_attribute('aria-pressed','true')
            self.shot('recap-time-'+choice)
        layout=self.page.locator('#cooperation-recap').evaluate('(e)=>({height:e.clientHeight,content:e.scrollHeight})')
        self.assertLessEqual(layout['content'],layout['height']+2)
        self.page.locator('#recap-space-open').click()
        expect(self.page.locator('#recap-map')).to_be_visible()
        expect(self.page.locator('#cooperation-recap')).to_have_attribute('aria-label','Prelude III: possibilities')
        self.page.locator('#recap-space-plan').select_option('ABA')
        expect(self.page.locator('#hinge-title')).to_have_text('The crew clears B again')
        expect(self.page.locator('#recap-story')).to_contain_text('more earnings as well as lower health')
        self.shot('prelude-hinge-returning-crew')
        self.page.locator('#hinge-choices button').first.click()
        expect(self.page.locator('#hinge-title')).to_have_text('The nursery order is filled')
        self.page.locator('#recap-space-chart [data-hinge="2"]').click()
        expect(self.page.locator('#hinge-title')).to_have_text('The crew clears B again')
        expect(self.page.locator('#recap-space-plan option')).to_have_count(21)
        expect(self.page.locator('#recap-space-chart [data-plan]')).to_have_count(60)
        expect(self.page.locator('#recap-space-chart [data-trail]')).to_have_count(1)
        self.shot('recap-space-initial')
        for key,count in [('AAA','One field plot'),('CCB','2 field plots'),('ABC','3 field plots')]:
            self.page.locator('#recap-space-plan').select_option(key)
            expect(self.page.locator('#recap-work')).to_contain_text(count)
            self.shot('recap-space-'+key)
        chart=self.page.locator('#recap-space-chart')
        old_path=chart.locator('[data-trail]').get_attribute('d')
        bounds=chart.bounding_box()
        self.page.mouse.move(bounds['x']+bounds['width']*.5,bounds['y']+bounds['height']*.85)
        self.page.mouse.down();self.page.mouse.move(bounds['x']+bounds['width']*.65,bounds['y']+bounds['height']*.75,steps=10);self.page.mouse.up()
        self.assertNotEqual(old_path,chart.locator('[data-trail]').get_attribute('d'))
        self.shot('recap-space-turned')
        chart.focus();chart.press('Home')
        # Every plan remains reachable without judging depth or a precise click.
        dot=chart.locator('[data-plan="AAA"]').last
        dot.focus();dot.press('Enter')
        expect(self.page.locator('#recap-space-plan')).to_have_value('AAA')
        # A real pointer tap must survive pointer capture used for rotation.
        chart.locator('[data-plan="ABC"]').last.click()
        expect(self.page.locator('#recap-space-plan')).to_have_value('ABC')
        chart.focus()
        for direction in ['ArrowRight','ArrowDown','ArrowLeft','ArrowUp']:
            for _ in range(20):chart.press(direction)
            # The time planes must not clip even at the steepest allowed tilt.
            extent=chart.evaluate('(e)=>[...e.querySelectorAll("polygon")].flatMap(p=>[...p.points].map(p=>[p.x,p.y]))')
            self.assertTrue(all(0<x<620 and 0<y<480 for x,y in extent))
        chart.press('Home')
        layout=self.page.locator('#cooperation-recap').evaluate('(e)=>({height:e.clientHeight,content:e.scrollHeight})')
        self.assertLessEqual(layout['content'],layout['height']+2)
        self.page.locator('#recap-time-return').click()
        expect(self.page.locator('[data-choice="sequence"]')).to_have_attribute('aria-pressed','true')
        self.page.locator('#recap-one-return').click()
        expect(self.page.locator('#earnings-health [data-plan="CAB"]')).to_have_attribute('aria-pressed','true')
        self.page.locator('#recap-one-back').click()
        after=self.page.evaluate('({state:roundDiagnostics().state,years:roundDiagnostics().years,clock:roundDiagnostics().clock})')
        self.assertEqual(before,after)

    def test_fire_at_projected_year_and_explicit_prelude_to_game(self):
        self.page.set_viewport_size({'width':1280,'height':800})
        self.role('room')
        self.assertEqual(self.page.locator('#game-mode option').all_text_contents(),['Start Here','The Players','Prelude','The Game','Recap'])
        for team,key in [('ecology','A'),('removal','C'),('community','A')]:
            self.page.locator('#plan-'+team).select_option(key)
            self.page.wait_for_function('(a)=>roundDiagnostics().state.proposals[a[0]]===a[1]',arg=[team,key])
        self.commit()
        slider=self.page.locator('#recovery')
        burned=[]
        for year in [2.5,5]:
            slider.focus()
            for _ in range(25):slider.press('ArrowRight')
            self.seek('fire-time',False);self.seek('fire-time')
            expect(self.page.locator('#fire-note')).to_contain_text('year '+str(year).removesuffix('.0'))
            burned.append(float(self.page.locator('#burned').inner_text().split()[0]))
            panel=self.page.locator('#round-panel').bounding_box()
            recap=self.page.locator('#recap-open').bounding_box()
            self.assertLessEqual(recap['y']+recap['height'],panel['y']+panel['height'])
            self.shot('fire-current-fuel-'+str(year))
        self.assertGreater(burned[1],burned[0]+2)
        # The same independent test is available even when Projection includes grazing.
        self.page.get_by_role('button',name='Revise plan').click()
        self.page.locator('#plan-community').select_option('C')
        self.page.wait_for_function('roundDiagnostics().state.proposals.community==="C"')
        self.commit();self.seek('recovery')
        expect(self.page.locator('#fire-note')).to_contain_text('first season')
        self.seek('fire-time',False);self.seek('fire-time')
        expect(self.page.locator('#fire-note')).to_contain_text('year 10')
        slider.focus();slider.press('ArrowLeft')
        expect(self.page.locator('#fire-note')).to_contain_text('first season')
        self.page.get_by_role('button',name='Recap',exact=True).click()
        self.page.locator('#recap-time-open').click();self.page.locator('#recap-space-open').click()
        expect(self.page.locator('#cooperation-recap h1')).to_have_text('How much can we keep tending?')
        expect(self.page.locator('#cooperation-recap')).not_to_contain_text('In Combined')
        self.shot('prelude-play-game')
        self.page.get_by_role('button',name='Play game',exact=True).click()
        self.page.wait_for_url('**/strategy.html#*')
        self.page.locator('#loading').wait_for(state='hidden',timeout=60000)
        expect(self.page.locator('#strategy-intro')).to_be_visible()
        expect(self.page.locator('#stage [value=combined]')).to_have_text('The Game')
        self.page.locator('#begin').click()
        self.assertEqual(self.page.locator('#stage option').all_text_contents(),['Start Here','The Players','Prelude','The Game','Recap'])
        before=self.page.evaluate('strategyDiagnostics().game')
        self.page.locator('#stage').select_option('recap-one')
        expect(self.page.locator('#recap-plan')).to_contain_text('Restore A, remove C, grazing C')
        self.page.locator('#recap-time-open').click();self.page.locator('#recap-space-open').click()
        self.page.locator('#recap-play').click()
        self.assertEqual(self.page.evaluate('strategyDiagnostics().game'),before)
        self.page.locator('#stage').select_option('recap')
        self.page.locator('#prelude-next').click()
        expect(self.page.locator('#prelude-caption')).to_have_text('The Players - simulated fire scar')
        self.shot('recap-new-fuel-corridor')
        self.page.keyboard.press('Escape')
        self.page.locator('#stage').select_option('play')
        self.page.wait_for_url('**/round.html#*');self.ready()
        self.assertEqual(self.page.evaluate('roundDiagnostics().state.phase'),'committed')

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
        self.commit()
        self.seek('recovery'); self.shot('software-original-fire')
        self.assertGreater(self.page.evaluate('roundDiagnostics().fire'),0)
