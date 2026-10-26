"""Test bouncingBall using fmpy."""
import fmpy
from fmpy import simulate_fmu, instantiate_fmu
from fmpy.model_description import read_model_description
import matplotlib.pyplot as plt
import logging
import numpy as np
from pathlib import Path
import shutil
import zipfile


from simulation import _simulateCS
fmpy.simulation.simulateCS = _simulateCS

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

def do_show( x:list|np.ndarray,
             y:list|np.ndarray,
             label:str,
             x2:list|np.ndarray|None = None,
             y2:list|np.ndarray|None = None,
             label2:str=""):
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(x, y, label=label)
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    
    if x2 is not None and y2 is not None:
        plt.subplot(2, 1, 2)
        plt.plot(x2, y2, label=label2)
        plt.xlabel('Time')
        plt.ylabel('Value2')
        plt.legend()
        plt.grid(True)
    plt.show()


def test_bouncing(*, show: bool):
    """Test the Function.fmu in isolation."""
    fmu_file = EXAMPLES_DIR / 'BouncingBall.fmu'
    assert fmu_file.exists()
    result = simulate_fmu(
        filename=fmu_file,
        start_time=0.0,
        stop_time=4.0,
        step_size=0.5,
        start_values={
            'h' : 1.0,
            'v' : 1.0,
            'g' : -9.81,
            'e' : 0.7,
        },
        output = ['h','v'],
    )
    if show:
        do_show(result['time'], result['h'], label='Height',
                x2=result['time'], y2=result['v'], label2='Speed')


if __name__ == "__main__":
    retcode = 0#pytest.main(["-rA", "-v", "--rootdir", "../", "--show", "False", __file__])
    assert retcode == 0, f"Non-zero return code {retcode}"
    test_bouncing(show=True)
    