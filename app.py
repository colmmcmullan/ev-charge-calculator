import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# HTML template with external CSS
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EV Charge Calculator</title>
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="container">
        <h1>EV Charge Calculator</h1>
        
        <form method="post">
            <input type="hidden" name="voltage" value="230">
            <div class="form-group">
                <label for="battery_size">Battery Size (kWh):</label>
                <input type="number" id="battery_size" name="battery_size" value="{{ request.form.get('battery_size', '26.8') }}" step="0.1" required>
            </div>
            <div class="form-group">
                <label for="cost_per_kwh">Electricity Cost (€/kWh before TVA):</label>
                <input type="number" id="cost_per_kwh" name="cost_per_kwh" value="{{ request.form.get('cost_per_kwh', '0.16428') }}" step="0.00001" required>
            </div>
            <div class="form-group slider-group">
                <label for="start_percentage">Start Battery Percentage: <span class="percentage-value">20%</span></label>
                <div class="range-container">
                    <input type="range" 
                           id="start_percentage" 
                           name="start_percentage" 
                           value="{{ request.form.get('start_percentage', '20') }}" 
                           min="0" 
                           max="100" 
                           step="1" 
                           required>
                    <div class="range-labels">
                        <span>0%</span>
                        <span>50%</span>
                        <span>100%</span>
                    </div>
                </div>
            </div>
            <div class="form-group slider-group">
                <label for="end_percentage">Target Battery Percentage: <span class="percentage-value">80%</span></label>
                <div class="range-container">
                    <input type="range" 
                           id="end_percentage" 
                           name="end_percentage" 
                           value="{{ request.form.get('end_percentage', '80') }}" 
                           min="0" 
                           max="100" 
                           step="1" 
                           required>
                    <div class="range-labels">
                        <span>0%</span>
                        <span>50%</span>
                        <span>100%</span>
                    </div>
                </div>
            </div>
            <div class="form-group" style="grid-column: 1 / -1;">
                <button type="submit">Calculate Charging Times</button>
            </div>
        </form>
        
        {% if charge_times %}
            <div class="results">
                <h2>Charging Time Estimates</h2>
                <p>For EU standard voltage (230V):</p>
                <table>
                    <thead>
                        <tr>
                            <th>Current</th>
                            <th>Power</th>
                            <th>Total Charging Time</th>
                            <th>Time per 10%</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for time in charge_times %}
                        <tr>
                            <td>{{ time.amperage }}A</td>
                            <td>{{ time.power_kw }}kW</td>
                            <td>{{ time.duration }}</td>
                            <td>{{ time.time_per_10_percent }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                
                <div class="cost-summary">
                    <h2>Cost Summary</h2>
                    <p>Electricity rate: €{{ "%.5f"|format(cost_per_kwh) }}/kWh (before TVA)</p>
                    <p>Rate with TVA (20%): €{{ "%.5f"|format(cost_per_kwh * 1.2) }}/kWh</p>
                    <p>Total energy needed: {{ "%.1f"|format(energy_needed) }} kWh</p>
                    <p>Total cost: {{ total_cost }}</p>
                    <p>Cost for full 100% charge: {{ cost_for_full }}</p>
                </div>
            </div>
            
            <div class="environmental-impact">
                <h2>Environmental Impact</h2>
                <p>Estimated range: {{ environmental.ev_range }} km</p>
                <p>EV CO2 emissions: {{ environmental.ev_emissions }}</p>
                <p>CO2 savings vs petrol: {{ environmental.petrol_savings }} kg</p>
                <p>CO2 savings vs diesel: {{ environmental.diesel_savings }} kg</p>
                
                <h3>Air Quality Impact</h3>
                <p>NOx emissions avoided:</p>
                <ul>
                    <li>vs petrol: {{ environmental.petrol_nox_saved }}g</li>
                    <li>vs diesel: {{ environmental.diesel_nox_saved }}g</li>
                </ul>
                <p>Particulate Matter (PM) emissions avoided:</p>
                <ul>
                    <li>vs petrol: {{ environmental.petrol_pm_saved }}g</li>
                    <li>vs diesel: {{ environmental.diesel_pm_saved }}g</li>
                </ul>
                <small>Based on Ireland's grid carbon intensity and Euro 6 vehicle emission standards (2023)</small>
            </div>
        {% endif %}
    </div>
    <script>
        // Wait for the DOM to be fully loaded
        window.addEventListener('load', function() {
            // Get all the elements we need
            const startSlider = document.getElementById('start_percentage');
            const endSlider = document.getElementById('end_percentage');
            const startValue = document.querySelector('label[for="start_percentage"] .percentage-value');
            const endValue = document.querySelector('label[for="end_percentage"] .percentage-value');
            
            // Function to update the percentage display
            function updatePercentageValue(slider, valueDisplay) {
                valueDisplay.textContent = slider.value + '%';
            }
            
            // Function to ensure end percentage is not less than start percentage
            function validateRange() {
                const start = parseInt(startSlider.value);
                const end = parseInt(endSlider.value);
                
                if (start > end) {
                    endSlider.value = start;
                    updatePercentageValue(endSlider, endValue);
                }
            }
            
            // Add event listeners for the start slider
            startSlider.addEventListener('input', function() {
                updatePercentageValue(this, startValue);
                validateRange();
            });
            
            // Add event listeners for the end slider
            endSlider.addEventListener('input', function() {
                updatePercentageValue(this, endValue);
                validateRange();
            });
            
            // Initialize the displays
            updatePercentageValue(startSlider, startValue);
            updatePercentageValue(endSlider, endValue);
        });
    </script>
</body>
</html>
'''

def calculate_environmental_impact(energy_needed):
    """
    Calculate environmental impact and savings compared to ICE vehicles.
    
    Args:
        energy_needed (float): Energy needed for charging in kWh
        
    Returns:
        dict: Environmental impact metrics including CO2 and air pollutants
    """
    # Average CO2 emissions per kWh of electricity in Ireland (2023)
    grid_carbon_intensity = 0.220  # kg CO2/kWh
    
    # Average petrol car emissions for the same distance
    # Assuming 0.2 kWh/km for EV efficiency
    ev_range = energy_needed / 0.2  # km
    petrol_emissions_per_km = 0.120  # kg CO2/km (average new car 2023)
    diesel_emissions_per_km = 0.110  # kg CO2/km (average new car 2023)
    
    # Air pollutant emissions per km (mg/km) - Euro 6 standards
    petrol_nox = 60.0  # mg/km NOx
    diesel_nox = 80.0  # mg/km NOx
    petrol_pm = 4.5   # mg/km PM (both PM2.5 and PM10)
    diesel_pm = 4.5   # mg/km PM (both PM2.5 and PM10)
    
    # Calculate CO2 emissions
    ev_emissions = energy_needed * grid_carbon_intensity
    petrol_emissions = ev_range * petrol_emissions_per_km
    diesel_emissions = ev_range * diesel_emissions_per_km
    
    # Calculate CO2 savings
    petrol_savings = petrol_emissions - ev_emissions
    diesel_savings = diesel_emissions - ev_emissions
    
    # Calculate air pollutant savings (in grams)
    petrol_nox_saved = (ev_range * petrol_nox) / 1000  # Convert mg to g
    diesel_nox_saved = (ev_range * diesel_nox) / 1000
    petrol_pm_saved = (ev_range * petrol_pm) / 1000
    diesel_pm_saved = (ev_range * diesel_pm) / 1000
    
    # Convert CO2 to more readable units if small
    if ev_emissions < 1:
        ev_emissions_str = f"{ev_emissions * 1000:.1f} g"
    else:
        ev_emissions_str = f"{ev_emissions:.2f} kg"
    
    return {
        'ev_emissions': ev_emissions_str,
        'ev_range': f"{ev_range:.1f}",
        'petrol_savings': f"{petrol_savings:.2f}",
        'diesel_savings': f"{diesel_savings:.2f}",
        'petrol_nox_saved': f"{petrol_nox_saved:.1f}",
        'diesel_nox_saved': f"{diesel_nox_saved:.1f}",
        'petrol_pm_saved': f"{petrol_pm_saved:.1f}",
        'diesel_pm_saved': f"{diesel_pm_saved:.1f}"
    }


def calculate_costs(battery_size, start_percentage, end_percentage, cost_per_kwh):
    """Calculate electricity costs for charging.
    
    Args:
        battery_size (float): Battery capacity in kWh
        start_percentage (float): Starting battery percentage
        end_percentage (float): Target battery percentage
        cost_per_kwh (float): Electricity cost per kWh before TVA
        
    Returns:
        tuple: (energy_needed, total_cost, cost_per_10_percent)
    """
    # Calculate energy needed
    energy_needed = battery_size * (end_percentage - start_percentage) / 100
    energy_for_full = battery_size  # Energy needed for 0-100%
    
    # Calculate costs with TVA (20%)
    tva_multiplier = 1.20
    energy_cost_with_tva = cost_per_kwh * tva_multiplier
    
    # Format costs with euro symbol and 2 decimal places
    total_cost = f"€{energy_needed * energy_cost_with_tva:.2f}"
    cost_for_full = f"€{energy_for_full * energy_cost_with_tva:.2f}"
    
    return energy_needed, total_cost, cost_for_full


def calculate_charging_time(battery_size, voltage, amperage, start_percentage, end_percentage):
    # Validate percentage bounds
    if not (0 <= start_percentage <= 100) or not (0 <= end_percentage <= 100):
        raise ValueError("Percentages must be between 0 and 100")
    
    # Validate charging direction
    if end_percentage <= start_percentage:
        raise ValueError("End percentage must be greater than start percentage")
    
    # Calculate power in kilowatts (voltage * amperage = watts, divide by 1000 for kW)
    power_kw = (voltage * amperage) / 1000
    
    # Calculate energy needed (kWh)
    energy_needed = battery_size * (end_percentage - start_percentage) / 100
    
    # Calculate hours needed (energy needed / power)
    hours = energy_needed / power_kw
    
    # Calculate time for 10% charge
    time_for_10_percent = (battery_size * 0.1) / power_kw
    time_10_hours = int(time_for_10_percent)
    time_10_minutes = int((time_for_10_percent - time_10_hours) * 60)
    
    # Convert total time to hours and minutes
    hours_whole = int(hours)
    minutes = int((hours - hours_whole) * 60)
    
    return {
        'amperage': amperage,
        'power_kw': power_kw,
        'duration': f"{hours_whole}h {minutes}m",
        'time_per_10_percent': f"{time_10_hours}h {time_10_minutes}m"
    }

@app.route('/', methods=['GET', 'POST'])
def home():
    charge_times = None
    if request.method == 'POST':
        try:
            battery_size = float(request.form['battery_size'])
            voltage = float(request.form['voltage'])  # Hidden field, always 230V
            start_percentage = float(request.form['start_percentage'])
            end_percentage = float(request.form['end_percentage'])
            
            # Calculate for different amperage values
            amperages = [6, 8, 10, 16]
            cost_per_kwh = float(request.form['cost_per_kwh'])
            
            # Calculate costs
            energy_needed, total_cost, cost_for_full = calculate_costs(
                battery_size, start_percentage, end_percentage, cost_per_kwh
            )
            
            # Calculate environmental impact
            environmental_impact = calculate_environmental_impact(energy_needed)
            
            # Calculate charging times for different amperages
            charge_times = [
                calculate_charging_time(
                    battery_size, voltage, amperage,
                    start_percentage, end_percentage
                )
                for amperage in amperages
            ]
            
            return render_template_string(HTML_TEMPLATE,
                                   charge_times=charge_times,
                                   cost_per_kwh=cost_per_kwh,
                                   energy_needed=energy_needed,
                                   total_cost=total_cost,
                                   cost_for_full=cost_for_full,
                                   environmental=environmental_impact)
        except ValueError:
            charge_times = [{'amperage': 0, 'power_kw': 0, 'duration': "Error: Please enter valid numbers"}]
    
    # Provide default values for cost variables when form hasn't been submitted
    return render_template_string(HTML_TEMPLATE,
                               charge_times=charge_times,
                               cost_per_kwh=0.16428,
                               energy_needed=0,
                               total_cost="€0.00",
                               cost_for_full="€0.00",
                               environmental={'ev_emissions': '0 g',
                                            'ev_range': '0',
                                            'petrol_savings': '0.00',
                                            'diesel_savings': '0.00'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)

