import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# HTML template with inline CSS
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>EV Charge Calculator</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        form {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="number"] {
            width: 200px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            background-color: #e7f3fe;
            border-radius: 4px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
        }
    </style>
</head>
<body>
    <h1>EV Charge Calculator</h1>
    <form method="post">
        <input type="hidden" name="voltage" value="230">
        <div class="form-group">
            <label for="battery_size">Battery Size (kWh):</label>
            <input type="number" id="battery_size" name="battery_size" value="26.8" step="0.1" required>
        </div>
        <div class="form-group">
            <label for="start_percentage">Start Battery Percentage (%):</label>
            <input type="number" id="start_percentage" name="start_percentage" value="20" min="0" max="100" required>
        </div>
        <div class="form-group">
            <label for="end_percentage">Target Battery Percentage (%):</label>
            <input type="number" id="end_percentage" name="end_percentage" value="80" min="0" max="100" required>
        </div>
        <div class="form-group">
            <label for="cost_per_kwh">Electricity Cost (€/kWh before TVA):</label>
            <input type="number" id="cost_per_kwh" name="cost_per_kwh" value="0.16428" step="0.00001" required>
        </div>
        <button type="submit">Calculate Charging Times</button>
    </form>
    {% if charge_times %}
    <div class="result">
        <h2>Charging Time Estimates</h2>
        <p>For EU standard voltage (230V):</p>
        <table>
            <tr>
                <th>Current</th>
                <th>Power</th>
                <th>Total Charging Time</th>
                <th>Time per 10%</th>
            </tr>
            {% for time in charge_times %}
            <tr>
                <td>{{ time.amperage }}A</td>
                <td>{{ time.power_kw }}kW</td>
                <td>{{ time.duration }}</td>
                <td>{{ time.time_per_10_percent }}</td>
            </tr>
            {% endfor %}
        </table>
        
        <div class="result" style="margin-top: 20px;">
            <h2>Cost Summary</h2>
            <p>Electricity rate: €{{ "%.5f"|format(cost_per_kwh) }}/kWh (before TVA)</p>
            <p>Rate with TVA (20%): €{{ "%.5f"|format(cost_per_kwh * 1.2) }}/kWh</p>
            <p>Total energy needed: {{ "%.1f"|format(energy_needed) }} kWh</p>
            <p>Total cost: {{ total_cost }}</p>
            <p>Cost for full 100% charge: {{ cost_for_full }}</p>
        </div>
    {% endif %}
</body>
</html>
'''

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
                                   cost_for_full=cost_for_full)
        except ValueError:
            charge_times = [{'amperage': 0, 'power_kw': 0, 'duration': "Error: Please enter valid numbers"}]
    
    # Provide default values for cost variables when form hasn't been submitted
    return render_template_string(HTML_TEMPLATE,
                               charge_times=charge_times,
                               cost_per_kwh=0.16428,
                               energy_needed=0,
                               total_cost="€0.00",
                               cost_for_full="€0.00")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)

