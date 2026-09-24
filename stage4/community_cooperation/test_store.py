import unittest
from .store import Store, RoundError, assessment


class Rooms(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.host = self.store.request('new', {})

    def call(self, action, role='room', **extra):
        body = dict(session=self.host['id'], token=self.host['tokens'][role])
        state = self.store.request('state', body)
        return self.store.request(action, dict(body, revision=state['revision'], **extra))

    def plan(self, ecology, removal, community):
        for role, value in zip(('ecology', 'removal', 'community'), (ecology, removal, community)):
            self.call('propose', role, team=role, patch=value)
        self.call('reveal')

    def test_proposals_are_private_until_reveal(self):
        self.call('propose', 'ecology', team='ecology', patch='C')
        other = self.call('state', 'community')
        self.assertTrue(other['ready']['ecology'])
        self.assertIsNone(other['proposals']['ecology'])
        self.assertNotIn('tokens', other)

    def test_team_cannot_impersonate_or_reveal(self):
        for action, extra in [('propose', dict(team='ecology', patch='A')), ('reveal', {})]:
            with self.assertRaises(RoundError):
                self.call(action, 'community', **extra)

    def test_conflict_requires_revision(self):
        self.plan('C', 'A', 'C')
        with self.assertRaisesRegex(RoundError, 'pasture'):
            self.call('commit')
        self.call('propose', 'community', team='community', patch='B')
        self.assertEqual(self.call('commit')['phase'], 'committed')
        with self.assertRaises(RoundError):
            self.call('propose', 'community', team='community', patch='A')
        self.call('revise')
        self.call('propose', 'community', team='community', patch='A')

    def test_finances_and_order(self):
        good = assessment(dict(ecology='A', removal='A', community='A'))
        self.assertTrue(good['nurseryOrder'])
        self.assertEqual(good['left'], 7)
        self.plan('A', 'B', 'B')
        committed=self.call('commit')
        self.assertEqual(committed['phase'],'committed')
        self.assertGreater(committed['assessment']['debt'],0)
        self.assertLess(committed['assessment']['left'],0)

    def test_stale_revision_and_invalid_patch(self):
        self.call('propose', 'community', team='community', patch='A')
        with self.assertRaisesRegex(RoundError, 'updated'):
            self.store.request('propose', dict(session=self.host['id'], token=self.host['tokens']['community'], revision=0, team='community', patch='B'))
        with self.assertRaises(RoundError):
            self.call('propose', 'community', team='community', patch='D')

    def test_direct_host_commit_requires_complete_compatible_choices(self):
        with self.assertRaises(RoundError): self.call('commit')
        for role, choice in [('ecology','B'),('removal','C'),('community','B')]:
            self.call('propose', team=role, patch=choice)
        with self.assertRaisesRegex(RoundError, 'coffee'): self.call('commit')
        self.call('propose',team='ecology',patch='A')
        with self.assertRaises(RoundError): self.call('commit','community')
        result=self.call('commit')
        self.assertEqual(result['phase'],'committed')
        self.assertGreater(result['assessment']['debt'],0)
        with self.assertRaises(RoundError): self.call('commit')

    def test_separate_rooms(self):
        self.call('propose', 'community', team='community', patch='C')
        second = self.store.request('new', {})
        self.assertFalse(any(second['ready'].values()))

    def test_expedition_reset_preserves_capabilities_and_clears_three_plans(self):
        self.plan('C', 'A', 'B')
        self.call('commit')
        tokens = self.host['tokens'].copy()
        with self.assertRaisesRegex(RoundError, 'host'):
            self.call('reset', 'community')
        reset = self.call('reset')
        self.assertEqual(reset['tokens'], tokens)
        self.assertEqual(reset['screen'], 'expedition')
        self.assertEqual(reset['generation'], 1)
        self.assertFalse(any(reset['ready'].values()))
        self.assertEqual(self.call('enter', 'community')['screen'], 'play')


if __name__ == '__main__':
    unittest.main()
