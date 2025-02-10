import unittest
from app import calculate_charging_time, calculate_costs, calculate_environmental_impact

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

class TestCalculateCosts(unittest.TestCase):
    """Test cases for cost calculations"""
    
    def test_standard_cost_calculation(self):
        """Test cost calculation with standard values"""
        energy_needed, total_cost, cost_for_full = calculate_costs(
            battery_size=26.8,
            start_percentage=20,
            end_percentage=80,
            cost_per_kwh=0.16428
        )
        
        self.assertAlmostEqual(energy_needed, 16.08, places=2)  # 26.8 * 0.6
        self.assertEqual(total_cost, "€3.17")  # 16.08 * (0.16428 * 1.2)
        self.assertEqual(cost_for_full, "€5.28")  # 26.8 * (0.16428 * 1.2)
    
    def test_full_charge_cost(self):
        """Test cost calculation for a full charge"""
        energy_needed, total_cost, cost_for_full = calculate_costs(
            battery_size=26.8,
            start_percentage=0,
            end_percentage=100,
            cost_per_kwh=0.16428
        )
        
        self.assertAlmostEqual(energy_needed, 26.8, places=2)  # Full battery
        self.assertEqual(total_cost, "€5.28")  # 26.8 * (0.16428 * 1.2)
        self.assertEqual(cost_for_full, "€5.28")  # 26.8 * (0.16428 * 1.2)
    
    def test_small_charge_cost(self):
        """Test cost calculation for a small charge"""
        energy_needed, total_cost, cost_for_full = calculate_costs(
            battery_size=26.8,
            start_percentage=20,
            end_percentage=30,
            cost_per_kwh=0.16428
        )
        
        self.assertAlmostEqual(energy_needed, 2.68, places=2)  # 26.8 * 0.1
        self.assertEqual(total_cost, "€0.53")  # 2.68 * (0.16428 * 1.2)
        self.assertEqual(cost_for_full, "€5.28")  # 26.8 * (0.16428 * 1.2)


class TestEnvironmentalImpact(unittest.TestCase):
    """Test environmental impact calculations"""
    
    def test_standard_charge_impact(self):
        """Test environmental impact for a standard charge"""
        impact = calculate_environmental_impact(16.08)  # 60% of 26.8 kWh battery
        
        self.assertEqual(impact['ev_range'], '80.4')  # 16.08 kWh / 0.2 kWh/km
        self.assertEqual(impact['ev_emissions'], '3.54 kg')  # 16.08 * 0.220
        self.assertEqual(impact['petrol_savings'], '6.11')  # (80.4 * 0.120) - 3.54
        self.assertEqual(impact['diesel_savings'], '5.31')  # (80.4 * 0.110) - 3.54
    
    def test_small_charge_impact(self):
        """Test environmental impact for a small charge"""
        impact = calculate_environmental_impact(2.68)  # 10% of 26.8 kWh battery
        
        self.assertEqual(impact['ev_range'], '13.4')  # 2.68 kWh / 0.2 kWh/km
        self.assertEqual(impact['ev_emissions'], '589.6 g')  # 2.68 * 0.220 * 1000
        self.assertEqual(impact['petrol_savings'], '1.02')  # (13.4 * 0.120) - 0.5896
        self.assertEqual(impact['diesel_savings'], '0.88')  # (13.4 * 0.110) - 0.5896


if __name__ == '__main__':
    unittest.main()
