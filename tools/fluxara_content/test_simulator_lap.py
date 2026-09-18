"""Offline tests of log recognition, not gameplay acceptance."""
import unittest

from simulator_lap import completion


class CompletionTests(unittest.TestCase):
    def test_empty_log_is_not_completion(self):
        result = completion("")
        self.assertFalse(result['frame_summary'])
        self.assertFalse(result['aggregate_summary'])
        self.assertEqual(result['kart_results'], [])

    def test_startup_and_invalid_positions_are_not_finish_rows(self):
        result = completion('profile: kart Skidding 0 1 10.0 extra\n'
                            'profile: kart Skidding 1 5 10.0 extra\n'
                            'profile: kart Skidding 1 1 0.0 extra\n')
        self.assertEqual(result['kart_results'], [])

    def test_four_finish_rows_are_recognized(self):
        log = 'Number of frames: 100 time 2 Average FPS: 50\n'
        log += 'profile: min 10 max 20 av 15\n'
        log += ''.join('profile: kart Skidding %d %d 77.5 extra\n' % (i, i)
                       for i in range(1, 5))
        result = completion(log)
        self.assertTrue(result['frame_summary'])
        self.assertTrue(result['aggregate_summary'])
        self.assertEqual(len(result['kart_results']), 4)
        self.assertFalse(result['fatal_marker'])

    def test_crash_markers_remain_visible(self):
        for marker in ('[fatal]', 'SIGSEGV', 'EXC_BAD_ACCESS'):
            with self.subTest(marker=marker):
                self.assertTrue(completion(marker)['fatal_marker'])


if __name__ == '__main__':
    unittest.main()
