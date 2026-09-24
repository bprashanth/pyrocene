"""Three-role Cooperation rooms; separate from archived two-role saves."""
from collections import OrderedDict
from pathlib import Path
import json
import secrets
import threading

from ..shared_round import RoundError as BaseRoundError


class RoundError(BaseRoundError):
    def __init__(self, message, status):
        super().__init__(status, message)

CONFIG = json.loads(Path(__file__).with_name('config.json').read_text())
ROUND = json.loads(Path(__file__).parents[1].joinpath('round-config.json').read_text())
PATCHES = {p['key']: p for p in ROUND['candidates']}
ROLES = ('ecology', 'removal', 'community')


def assessment(proposals):
    if any(proposals.get(role) not in PATCHES for role in ROLES):
        return None
    e, r, c = (proposals[role] for role in ROLES)
    removal, ecology = PATCHES[r], PATCHES[e]
    investment = CONFIG['opportunities'][c]['investment']
    cost = ecology['planting'] + (0 if e == r else ROUND['clearingCost']) + removal['removalCost'] + investment
    returns = removal['income'] + removal['removalCost']
    left = CONFIG['grant'] + returns - cost
    conflict = ''
    if e == c and c in ('B', 'C'):
        conflict = f'{c} cannot be both native restoration and '+('a coffee plot.' if c == 'B' else 'pasture.')
    return dict(cost=cost, returns=returns, left=left, conflict=conflict,
                nurseryOrder=c == 'A' and e == 'A',
                issue=conflict or (f'The plan needs {-left} more credits.' if left < 0 else ''))


class Store:
    def __init__(self):
        self.rooms = OrderedDict()
        self.lock = threading.RLock()

    def view(self, room, role):
        reveal = room['phase'] != 'survey' or role == 'room'
        proposals = {r: room['proposals'][r] if reveal or r == role else None for r in ROLES}
        result = {k: room[k] for k in ('id', 'phase', 'revision', 'screen', 'generation')}
        result.update(role=role, proposals=proposals,
                      ready={r: room['proposals'][r] is not None for r in ROLES},
                      assessment=assessment(proposals))
        if role == 'room':
            result['tokens'] = room['tokens'].copy()
        return result

    def request(self, action, body):
        with self.lock:
            if action == 'new':
                ident = secrets.token_urlsafe(9)
                room = dict(id=ident, phase='survey', revision=0, generation=0,
                            screen='expedition' if body.get('screen') == 'expedition' else 'play',
                            proposals={r: None for r in ROLES},
                            tokens={r: secrets.token_urlsafe(24) for r in (*ROLES, 'room')})
                self.rooms[ident] = room
                while len(self.rooms) > 64:
                    self.rooms.popitem(last=False)
                return self.view(room, 'room')
            ident = body.get('session')
            if not isinstance(ident, str) or ident not in self.rooms:
                raise RoundError('This room has ended. Open a new room.', 404)
            room = self.rooms[ident]
            role = next((r for r, token in room['tokens'].items() if token == body.get('token')), None)
            if role is None:
                raise RoundError('Use your team link.', 403)
            if action == 'state':
                return self.view(room, role)
            if body.get('revision') != room['revision']:
                raise RoundError('Another team just updated its plan. Try again.', 409)
            if action == 'enter':
                room['screen'] = 'play'
            elif action == 'reset':
                if role != 'room':
                    raise RoundError('Only the room host resets the shared game.', 403)
                room['proposals'] = {r: None for r in ROLES}
                room['phase'] = 'survey'
                room['screen'] = 'expedition'
                room['generation'] += 1
            elif action == 'propose':
                team, patch = body.get('team'), body.get('patch')
                if not isinstance(team, str) or team not in ROLES or (role != 'room' and team != role):
                    raise RoundError('Only your team can change this proposal.', 403)
                if not isinstance(patch, str) or patch not in PATCHES or room['phase'] == 'committed':
                    raise RoundError('Choose A, B or C before committing.', 400)
                room['proposals'][team] = patch
            elif action == 'reveal':
                if role != 'room':
                    raise RoundError('The room host brings the plans together.', 403)
                if room['phase'] != 'survey' or not all(room['proposals'].values()):
                    raise RoundError('Wait for all three proposals.', 409)
                room['phase'] = 'review'
            elif action == 'commit':
                if role != 'room':
                    raise RoundError('The room host commits the shared plan.', 403)
                a = assessment(room['proposals'])
                if room['phase'] != 'review' or not a or a['issue']:
                    raise RoundError(a['issue'] if a and a['issue'] else 'Discuss the three proposals first.', 409)
                room['phase'] = 'committed'
            elif action == 'revise':
                if role != 'room' or room['phase'] != 'committed':
                    raise RoundError('Only the room host can reopen the plan.', 403)
                room['phase'] = 'review'
            else:
                raise RoundError('Unknown action.', 404)
            room['revision'] += 1
            return self.view(room, role)
