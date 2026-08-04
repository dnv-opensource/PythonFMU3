# Example of co-simulation setup
import fmpy
from fmpy import simulate_fmu
import matplotlib.pyplot as plt
import numpy as np

# Simulate the PID controller FMU
result = simulate_fmu(
    filename='PIDController.fmu',
    start_time=0.0,
    stop_time=10.0,
    step_size=0.01,
    start_values={
        'kp': 2.0,
        'ki': 0.5,
        'kd': 0.1,
        'setpoint': 1.0
    },
    input= np.array( [(0.0, 0.0, 1.0), (1.0, 0.3, 1.0), (5.0, 0.8, 1.0), (10.0, 1.0, 1.0)],
                     dtype=[('time', np.double),('measurement', np.double),('setpoint', np.double)]),
    output = ['output','setpoint','measurement'],
)

# Plot results
plt.figure(figsize=(12, 6))
plt.subplot(2, 1, 1)
plt.plot(result['time'], result['setpoint'], label='Setpoint')
plt.plot(result['time'], result['measurement'], label='Measurement')
plt.ylabel('Value')
plt.legend()
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(result['time'], result['output'], label='Control Output')
plt.xlabel('Time [s]')
plt.ylabel('Control Signal')
plt.legend()
plt.grid(True)
plt.show()