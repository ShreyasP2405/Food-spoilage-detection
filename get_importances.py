import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'ml', 'src'))
from simulator import BananaSimulator

data = []
# Sweep through different temperatures to break the linear time correlation
for temp in [10, 15, 20, 25, 30, 35]:
    sim = BananaSimulator(initial_ripeness=1.5)
    for reading in sim.stream(total_hours=200, dt_h=1.0, temp_profile=temp, rh_profile=90.0):
        data.append(reading.as_dict())

df = pd.DataFrame(data)

features = [
    "temp_c",
    "humidity_pct",
    "co2_ppm",
    "ethylene_ppm",
    "methane_ppm",
    "hours_since_harvest",
    "ripeness_estimate"
]
target = "days_until_spoilage"

X = df[features]
y = df[target]

rf = RandomForestRegressor(n_estimators=50, random_state=42)
rf.fit(X, y)

importances = rf.feature_importances_
feature_imp = list(zip(features, importances))
feature_imp.sort(key=lambda x: x[1], reverse=True)

print("--- Exact Feature Importances (%) ---")
for feat, imp in feature_imp:
    print(f"{feat}: {imp * 100:.2f}%")
