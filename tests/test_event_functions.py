# Example of co-simulation setup
import fmpy
import pytest
from fmpy import simulate_fmu
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from simulation import _simulateCS
fmpy.simulation.simulateCS = _simulateCS

def test_run(show:bool):
    # Simulate the PID controller FMU
    result = simulate_fmu(
    filename=Path(__file__).parent.resolve().parent / 'examples' / 'TwoState.fmu',
    start_time=0.0,
    stop_time=10.0,
    step_size=0.01,
    start_values={
        'mttf': 0.9005,
        'mttr': 0.0995,
        'seed': 1,
        'deterministic': True
    },
    output = ['state'],
    use_event_mode = True,
    )

    if show:
        # Plot results
        plt.figure(figsize=(12, 6))
        plt.subplot()
        plt.plot(result['time'], result['state'], label='State')
        #plt.plot(result['time'], result['measurement'], label='Measurement')
        plt.ylabel('Value')
        plt.legend()
        plt.grid(True)
        plt.show()

if __name__ == "__main__":
    #retcode = pytest.main(["-rA", "-v", "--rootdir", "../", "--show", "True", __file__])
    #assert retcode == 0, f"Non-zero return code {retcode}"
    test_run(show=True)
    # test_py_type()