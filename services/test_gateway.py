"""Isolated event deployment checks. Never resets the real event room."""
import base64
import http.client
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from stage2 import server as room
from stage2.films.serve import Handler as Films
from stage4.serve import create_server
from services.gateway import Gateway

AUTH='gm:test-password-for-isolated-room'

def background(server):
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server

class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        Path(cls.tmp.name,'clip.mp4').write_bytes(bytes(range(256))*4)
        cls.room=background(ThreadingHTTPServer(('127.0.0.1',0),room.Handler))
        cls.room.daemon_threads=True
        cls.films=ThreadingHTTPServer(('127.0.0.1',0),Films);cls.films.assets=cls.tmp.name
        background(cls.films)
        cls.forest=background(create_server(port=0))
        cls.gateway=background(Gateway(('127.0.0.1',0),room=cls.room.server_port,
            forest=cls.forest.server_port,films=cls.films.server_port,gm_credentials=AUTH))
        cls.port=cls.gateway.server_port

    @classmethod
    def tearDownClass(cls):
        for s in [cls.gateway,cls.forest,cls.films,cls.room]: s.shutdown();s.server_close()
        cls.tmp.cleanup()

    def setUp(self): room.ROOM=room.Room(seed=5,stage=1)

    def request(self,path,body=None,auth=False,headers=None,method=None):
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        h=dict(headers or {})
        if auth:h['Authorization']='Basic '+base64.b64encode(AUTH.encode()).decode()
        if body is not None:h['Content-Type']='application/json'
        c.request(method or ('POST' if body is not None else 'GET'),path,json.dumps(body) if body is not None else None,h)
        r=c.getresponse();result=(r.status,dict(r.getheaders()),r.read());c.close();return result

    def test_lore_start_local_stage3_and_prefix(self):
        status,_,page=self.request('/start');self.assertEqual(status,200);self.assertIn(b'pyrocene-gateway',page)
        for path in ['/lore','/lore/','/lore/lore.css','/stage4/expedition.html','/stage4/game-features.mjs']:
            self.assertEqual(self.request(path)[0],200,path)
        for path in ['/stage3','/stage4','/films']:
            status,h,_=self.request(path);self.assertEqual(status,308);self.assertEqual(h['Location'],path+'/')
        status,h,data=self.request('/stage3/')
        self.assertEqual(status,200);self.assertEqual(h['Cross-Origin-Opener-Policy'],'same-origin')
        self.assertEqual(h['Cross-Origin-Embedder-Policy'],'require-corp')
        self.assertEqual(self.request('/stage3/build.sh')[0],404)
        self.assertIn(b'<base href="/stage4/">',self.request('/stage4/community-cooperation/')[2])
        status,_,data=self.request('/stage4/api/community-cooperation/new',{})
        self.assertEqual(status,200);self.assertIn('tokens',json.loads(data))

    def test_gm_gate_covers_private_state_and_events(self):
        for path in ['/gm?stage=2','/api/state','/api/steps','/api/logs','/events?ch=gm','/static/gm.html']:
            self.assertEqual(self.request(path)[0],401,path)
        self.assertEqual(self.request('/api/gm/reset',{})[0],401)
        self.assertEqual(room.ROOM.stage,1)
        self.assertEqual(self.request('/gm?stage=2',auth=True)[0],200)
        self.assertEqual(room.ROOM.stage,2)
        self.assertEqual(self.request('/api/join',{'name':'Visitor'})[0],200)
        self.assertEqual(self.request('/api/gm/reset',{},auth=True,headers={'Origin':'https://elsewhere.example'})[0],403)

    def test_https_origin_through_tunnel_keeps_forest_actions_same_origin(self):
        path='/stage4/api/community-cooperation/new'
        for scheme in ['http','https']:
            status,_,data=self.request(path,{},headers={'Host':'pyrocene.idli.cc','Origin':scheme+'://pyrocene.idli.cc'})
            self.assertEqual(status,200,data);self.assertIn('tokens',json.loads(data))
        for origin in ['https://elsewhere.example','null','ftp://pyrocene.idli.cc','https://pyrocene.idli.cc.evil.example','https://pyrocene.idli.cc/path']:
            self.assertEqual(self.request(path,{},headers={'Host':'pyrocene.idli.cc','Origin':origin,'X-Forwarded-Host':'elsewhere.example','X-Forwarded-Proto':'https'})[0],403,origin)

    def test_stage_jump_retains_phones_clears_old_playback_and_refresh_is_safe(self):
        self.request('/api/gm/seed',{'n':6},auth=True)
        tokens=[p.token for p in room.ROOM.game.players.values()]
        self.request('/api/gm/start',{},auth=True)
        old=room.ROOM.game;self.assertNotEqual(old.phase,'lobby')
        self.request('/gm?stage=1',auth=True);self.assertIs(room.ROOM.game,old)
        room.ROOM.pair=({'old':True},{'old':True})
        epoch=room.ROOM.epoch
        self.request('/gm?stage=2',auth=True)
        self.assertEqual(room.ROOM.stage,2);self.assertGreater(room.ROOM.epoch,epoch)
        self.assertEqual([p.token for p in room.ROOM.game.players.values()],tokens)
        self.assertEqual(room.ROOM.mode,'idle');self.assertIsNone(room.ROOM.pair)
        self.assertEqual(room.ROOM.steps,[]);self.assertEqual(room.ROOM.replay,[])
        self.request('/api/gm/start',{},auth=True)
        self.request('/gm?stage=1',auth=True)
        self.assertEqual(room.ROOM.game.cfg['stage'],1)
        self.assertEqual(room.ROOM.game.phase,'lobby')
        room.ROOM.game.phase='ended';old=room.ROOM.game
        self.request('/gm?stage=1',auth=True);self.assertIsNot(room.ROOM.game,old)
        self.request('/?stage=2');self.assertEqual(room.ROOM.stage,1)

    def test_reset_during_animation_cannot_repaint_old_run(self):
        self.request('/api/gm/seed',{'n':6},auth=True)
        self.request('/api/gm/start',{},auth=True)
        self.request('/api/gm/advance',{},auth=True)
        self.request('/gm?stage=2',auth=True)
        frame=room.ROOM.frame;epoch=room.ROOM.epoch
        time.sleep(.3)
        self.assertEqual(room.ROOM.frame,frame);self.assertEqual(room.ROOM.epoch,epoch)
        self.assertEqual(room.ROOM.cursor,0);self.assertEqual(room.ROOM.mode,'idle')

    def test_projector_sse_arrives_without_buffering(self):
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=3)
        c.request('GET','/events?ch=projector');r=c.getresponse()
        self.assertEqual(r.status,200);self.assertEqual(r.readline(),b'event: frame\n')
        c.close()

    def test_ranges_and_path_boundaries(self):
        for header,expected in [('bytes=10-19',bytes(range(10,20))),('bytes=-5',bytes(range(251,256)))]:
            status,h,data=self.request('/films/clip.mp4',headers={'Range':header})
            self.assertEqual(status,206);self.assertEqual(data,expected);self.assertIn('Content-Range',h)
        self.assertEqual(self.request('/films/clip.mp4',headers={'Range':'bytes=9999-'})[0],416)
        for p in ['/stage3/../services/gateway.py','/stage3/%2e%2e/services/gateway.py','/lore/../api/state','/stage3/%252e%252e/secret']:
            self.assertEqual(self.request(p)[0],400,p)
        self.assertEqual(self.request('/stage4/api/community-cooperation/new',{},method='POST')[0],200)

if __name__=='__main__':unittest.main()
