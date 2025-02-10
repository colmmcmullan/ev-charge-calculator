import unittest
from app import calculate_charging_time

class TestCalculateChargingTime(unittest.TestCase):
    def test_standard_charging_scenario(self):
        """Test a typical charging scenario with standard values"""
        result = calculate_charging_time(
            battery_size=26.8,
            voltage=230,
            amperage=10,
            start_percentage=20,
            end_percentage=80
        )
        
        self.assertEqual(result['amperage'], 10)
        self.assertEqual(result['power_kw'], 2.3)
        self.assertEqual(result['duration'], "6h 59m")  # (26.8 * 0.6) / 2.3 = 6.991 hours
        self.assertEqual(result['time_per_10_percent'], "1h 9m")  # (26.8 * 0.1) / 2.3 = 1.165 hours

    def test_minimum_amperage(self):
        """Test charging with minimum amperage (6A)"""
        result = calculate_charging_time(
            battery_size=26.8,
            voltage=230,
            amperage=6,
            start_percentage=20,
            end_percentage=80
        )
        
        self.assertEqual(result['amperage'], 6)
        self.assertEqual(result['power_kw'], 1.38)
        self.assertEqual(result['duration'], "11h 39m")  # (26.8 * 0.6) / 1.38 = 11.652 hours
        self.assertEqual(result['time_per_10_percent'], "1h 56m")  # (26.8 * 0.1) / 1.38 = 1.942 hours

    def test_maximum_amperage(self):
        """Test charging with maximum amperage (16A)"""
        result = calculate_charging_time(
            battery_size=26.8,
            voltage=230,
            amperage=16,
            start_percentage=20,
            end_percentage=80
        )
        
        self.assertEqual(result['amperage'], 16)
        self.assertEqual(result['power_kw'], 3.68)
        self.assertEqual(result['duration'], "4h 22m")  # (26.8 * 0.6) / 3.68 = 4.37 hours
        self.assertEqual(result['time_per_10_percent'], "0h 43m")  # (26.8 * 0.1) / 3.68 = 0.728 hours

    def test_full_charge_cycle(self):
        """Test a full charge cycle from 0% to 100%"""
        result = calculate_charging_time(
            battery_size=26.8,
            voltage=230,
            amperage=10,
            start_percentage=0,
            end_percentage=100
        )
        
        self.assertEqual(result['duration'], "11h 39m")  # (26.8 * 1.0) / 2.3 = 11.65 hours

    def test_small_charge_increment(self):
        """Test a small charging increment (10% to 20%)"""
        result = calculate_charging_time(
            battery_size=26.8,
            voltage=230,
            amperage=10,
            start_percentage=10,
            end_percentage=20
        )
        
        self.assertEqual(result['duration'], "1h 9m")  # (26.8 * 0.1) / 2.3 = 1.165 hours

    def test_invalid_percentage_range(self):
        """Test that end percentage is greater than start percentage"""
        with self.assertRaises(ValueError):
            calculate_charging_time(
                battery_size=26.8,
                voltage=230,
                amperage=10,
                start_percentage=80,
                end_percentage=20
            )

    def test_percentage_bounds(self):
        """Test that percentages are within valid bounds"""
        with self.assertRaises(ValueError):
            calculate_charging_time(
                battery_size=26.8,
                voltage=230,
                amperage=10,
                start_percentage=-10,
                end_percentage=80
            )
        
        with self.assertRaises(ValueError):
            calculate_charging_time(
                battery_size=26.8,
                voltage=230,
                amperage=10,
                start_percentage=20,
                end_percentage=110
            )

if __name__ == '__main__':
    unittest.main()
