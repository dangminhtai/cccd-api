import unittest

from services.cccd_parser import parse_cccd, parse_gender_century


class TestCCCDParser(unittest.TestCase):
    def test_parse_gender_century(self):
        # digit 4 is gender/century
        self.assertEqual(parse_gender_century("0000").gender, "Nam")
        self.assertEqual(parse_gender_century("0000").century, 20)
        self.assertEqual(parse_gender_century("0001").gender, "Nữ")
        self.assertEqual(parse_gender_century("0002").century, 21)
        self.assertEqual(parse_gender_century("0008").gender, "Nam")
        self.assertEqual(parse_gender_century("0008").century, 24)

    def test_parse_cccd_basic(self):
        # province 079, gender code 2 (Nam/2000s => century 21), yy=03 -> 2003
        cccd = "079203012345"
        out = parse_cccd(cccd)
        self.assertEqual(out["province_code"], "079")
        self.assertEqual(out["gender"], "Nam")
        self.assertEqual(out["century"], 21)
        self.assertEqual(out["birth_year"], 2003)


if __name__ == "__main__":
    unittest.main()


