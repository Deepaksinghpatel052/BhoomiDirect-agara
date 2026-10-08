from decimal import Decimal

from django.test import SimpleTestCase, TestCase, override_settings

from core.tests.helpers import make_locality
from locations.services import estimate_price
from locations.units import convert, to_sq_meter, trim_number


class UnitConversionTests(SimpleTestCase):
    def test_basic_units(self):
        self.assertEqual(to_sq_meter(1, "sqm"), Decimal("1.00"))
        self.assertEqual(to_sq_meter(100, "sqft"), Decimal("9.29"))
        self.assertEqual(to_sq_meter(1, "sqyard"), Decimal("0.84"))
        self.assertEqual(to_sq_meter(1, "acre"), Decimal("4046.86"))
        self.assertEqual(to_sq_meter(1, "hectare"), Decimal("10000.00"))

    def test_bigha_and_biswa_use_settings(self):
        self.assertEqual(to_sq_meter(1, "bigha"), Decimal("2529.29"))
        self.assertEqual(to_sq_meter(20, "biswa"), to_sq_meter(1, "bigha"))

    @override_settings(AREA_BIGHA_SQ_METER=1618.7)
    def test_bigha_is_configurable(self):
        self.assertEqual(to_sq_meter(1, "bigha"), Decimal("1618.70"))

    def test_convert_between_units(self):
        self.assertEqual(convert(1, "sqyard", "sqft"), Decimal("9.00"))
        self.assertEqual(convert(8, "bigha", "acre"), Decimal("5.00"))

    def test_trim_number_keeps_whole_number_zeros(self):
        self.assertEqual(trim_number(Decimal("800")), "800")
        self.assertEqual(trim_number(Decimal("2200.00")), "2200")
        self.assertEqual(trim_number(Decimal("2.50")), "2.5")

    def test_blank_and_invalid(self):
        self.assertIsNone(to_sq_meter("", "sqft"))
        with self.assertRaises(ValueError):
            to_sq_meter(1, "kanal")


class EstimatorTests(TestCase):
    def test_estimate_range(self):
        loc = make_locality()
        result = estimate_price(loc, "residential_plot", 200, "sqyard")
        # 200 gaj = 167.23 sq m x 30,000 = 50.17 lakh circle value
        self.assertEqual(result["circle_value"], Decimal("5016900"))
        self.assertLess(result["low"], result["high"])
        self.assertIsNone(estimate_price(loc, "commercial_plot", 200, "sqyard"))
