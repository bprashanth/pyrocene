"""One small collaborative round. Role tokens are capabilities, not accounts."""
import copy
import json
import secrets
import threading
from collections import OrderedDict
from pathlib import Path

CONFIG = json.loads(Path(__file__).with_name('round-config.json').read_text())
CANDIDATES = {c['key']: c for c in CONFIG['candidates']}

def budget(removal, ecology):
    r, e = CANDIDATES[removal], CANDIDATES[ecology]
    cost = e['planting'] + (0 if removal == ecology else CONFIG['clearingCost'])
    return {'income': r['income'], 'cost': cost, 'left': CONFIG['grant'] + r['income'] - cost,
            'damage': r['damage'], 'cover': e['cover'], 'shared': removal == ecology}

class RoundError(Exception):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)

class RoundStore:
    def __init__(self):
        self.sessions = OrderedDict()
        self.lock = threading.RLock()

    def request(self, action, body):
        with self.lock:
            if action == 'new':
                sid = secrets.token_urlsafe(12)
                tokens = {r: secrets.token_urlsafe(24) for r in ('room','removal','ecology')}
                s = {'id': sid, 'tokens': tokens, 'revision': 0, 'phase': 'survey', 'round': 1,
                     'proposals': {'removal': None, 'ecology': None},
                     'visited': {'removal': [], 'ecology': []}, 'committed': None}
                self.sessions[sid] = s
                while len(self.sessions) > 128:
                    self.sessions.popitem(last=False)
                return self.view(s, 'room')
            sid, token = body.get('session'), body.get('token')
            if not isinstance(sid, str) or not isinstance(token, str):
                raise RoundError(403, 'Open your team link.')
            s = self.sessions.get(sid)
            if s is None:
                raise RoundError(404, 'This round has ended. Ask for a new team link.')
            role = next((r for r,t in s['tokens'].items() if secrets.compare_digest(t,token)), None)
            if not role:
                raise RoundError(403, 'Open your team link.')
            if action == 'state':
                return self.view(s, role)
            owner = body.get('team') if role == 'room' else role
            independent = action == 'visit' or (action == 'propose'
                and body.get('round') == s['round'] and body.get('phase') == s['phase']
                and isinstance(owner,str) and owner in s['proposals']
                and body.get('prior') == s['proposals'][owner])
            if type(body.get('revision')) is not int or (body['revision'] != s['revision'] and not independent):
                raise RoundError(409, 'The plan changed. Review it and try again.')
            if action in ('reveal','commit','replay') and role != 'room':
                raise RoundError(403, 'The room makes this decision.')
            if action == 'replay':
                s.update(phase='survey', proposals={'removal':None,'ecology':None}, committed=None, round=s['round']+1)
            elif s['phase'] == 'committed':
                raise RoundError(409, 'This plan is committed.')
            elif action in ('visit','propose'):
                team = body.get('team') if role == 'room' else role
                if team not in ('removal','ecology') or (role != 'room' and body.get('team',role) != role):
                    raise RoundError(403, 'Use your own team view.')
                patch = body.get('patch')
                if not isinstance(patch,str) or patch not in CANDIDATES:
                    raise RoundError(400, 'Choose A, B or C.')
                if action == 'visit':
                    if patch not in s['visited'][team]:
                        s['visited'][team].append(patch)
                elif patch not in s['visited'][team]:
                    raise RoundError(400, 'Look closely at this patch first.')
                else:
                    s['proposals'][team] = patch
            elif action == 'reveal':
                if not all(s['proposals'].values()):
                    raise RoundError(400, 'Both teams need a proposal.')
                s['phase'] = 'review'
            elif action == 'commit':
                if s['phase'] != 'review' or not all(s['proposals'].values()):
                    raise RoundError(400, 'Reveal both proposals first.')
                result = budget(**s['proposals'])
                if result['left'] < 0:
                    raise RoundError(400, 'This plan costs more than the available funds.')
                s['committed'] = {**s['proposals'], **result}
                s['phase'] = 'committed'
            else:
                raise RoundError(404, 'Unknown round action.')
            s['revision'] += 1
            return self.view(s, role)

    def view(self, s, role):
        shown = s['phase'] != 'survey' or role == 'room'
        view = {k: copy.deepcopy(s[k]) for k in ('id','revision','phase','round','committed')}
        view.update(role=role, token=s['tokens'][role], ready={k:v is not None for k,v in s['proposals'].items()},
                    proposals={k:v if shown or k==role else None for k,v in s['proposals'].items()},
                    visited={k:list(v) for k,v in s['visited'].items() if role=='room' or k==role})
        if role == 'room':
            view['teams'] = {k:v for k,v in s['tokens'].items() if k!='room'}
        if s['phase'] != 'survey' and all(s['proposals'].values()):
            view['budget'] = budget(**s['proposals'])
        return view
