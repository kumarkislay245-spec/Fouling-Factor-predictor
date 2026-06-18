import pandas as pd
import time
import numpy as np
import os

print("🚀 Industrial DCS Simulator Started... Writing to live_plant_data.csv")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, 'live_plant_data.csv')

df_init = pd.DataFrame(columns=['Hot_Fluid_Outlet_Temperature_T3_K', 'Cold_Fluid_Outlet_Temperature_T4_K'])
df_init.to_csv(csv_path, index=False)

base_t3 = 320.0
base_t4 = 310.0

for i in range(500):

    simulated_t3 = base_t3 + (i * 0.08) + np.random.normal(0, 0.2)
    simulated_t4 = base_t4 - (i * 0.04) + np.random.normal(0, 0.2)

    new_data = pd.DataFrame({
        'Hot_Fluid_Outlet_Temperature_T3_K': [simulated_t3],
        'Cold_Fluid_Outlet_Temperature_T4_K': [simulated_t4]
    })
    new_data.to_csv(csv_path, mode='a', header=False, index=False)
    print(f"Row {i}: Sent Live Data -> T3: {simulated_t3:.2f}K, T4: {simulated_t4:.2f}K")

    time.sleep(2)