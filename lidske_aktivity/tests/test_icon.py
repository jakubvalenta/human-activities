from unittest import TestCase

from lidske_aktivity.icon import gen_random_slices


class TestIcon(TestCase):
    def test_gen_random_slices(self):
        for _ in range(20):
            result = list(gen_random_slices(3, 8))
            self.assertTrue(3 <= len(result) <= 8)
