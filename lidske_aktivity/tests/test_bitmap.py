from unittest import TestCase

from lidske_aktivity.bitmap import gen_random_slices, hue_from_index


class TextBitmap(TestCase):

    def test_hue_from_index(self):
        result = [
            hue_from_index(i, steps=4)
            for i in range(10)
        ]
        expected = [
            1 * 0.25,
            2 * 0.25,
            3 * 0.25,
            4 * 0.25,
            0 * 0.25 + 0.25 / 2,
            1 * 0.25 + 0.25 / 2,
            2 * 0.25 + 0.25 / 2,
            3 * 0.25 + 0.25 / 2,
            0 * 0.25 + 0.25 / 3,
            1 * 0.25 + 0.25 / 3,
        ]
        self.assertListEqual(result, expected)

    def test_gen_random_slices(self):
        for _ in range(20):
            result = list(gen_random_slices(3, 8))
            self.assertTrue(3 <= len(result) <= 8)
