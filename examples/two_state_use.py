# Example of co-simulation setup
import fmpy
from fmpy import simulate_fmu
import matplotlib.pyplot as plt
import numpy as np

# Simulate the PID controller FMU
result = simulate_fmu(
    filename='TwoState.fmu',
    start_time=0.0,
    stop_time=10.0,
    step_size=0.01,
    start_values={
        'mttf': 1.0,
        'mttr': 0.01,
        'seed': 1,
    },
    output = ['state'],
)

# Plot results
plt.figure(figsize=(12, 6))
plt.subplot(2, 1, 1)
plt.plot(result['time'], result['state'], label='State')
#plt.plot(result['time'], result['measurement'], label='Measurement')
plt.ylabel('Value')
plt.legend()
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(result['time'], result['state'], label='State')
plt.xlabel('Time [s]')
plt.ylabel('Control Signal')
plt.legend()
plt.grid(True)
plt.show()