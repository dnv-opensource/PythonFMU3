"""Test some FMUs using fmpy."""
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


def test_function(*, show: bool):
    """Test the Function.fmu in isolation."""
    fmu_file = EXAMPLES_DIR / 'Function.fmu'
    assert fmu_file.exists()
    result = simulate_fmu(
        filename=fmu_file,
        start_time=0.0,
        stop_time=10.0,
        step_size=0.01,
        start_values={
            'func_name' : "sum",
            'inputs' : "1.0 5.0",
        },
        #input= np.array( [(0.0, 0.0, 1.0), (1.0, 0.3, 1.0), (5.0, 0.8, 1.0), (10.0, 1.0, 1.0)],
        #                 dtype=[('time', np.double),('inputs[0]', np.double), ('inputs[1]', np.double)]),
        output = ['output'],
    )
    assert all( _sum == 6 for _sum in result['output'][2:])
    LOGGER.warning("TODO: find out how to provide input to array inputs")
    if show:
        do_show(result['time'], result['output'], label='Output')

def test_table(*, show: bool):
    """Test the Table.fmu in isolation."""
    fmu_file = EXAMPLES_DIR / 'Table.fmu'
    assert fmu_file.exists()
    result = simulate_fmu(
        filename=fmu_file,
        start_time=0.0,
        stop_time=10.0,
        step_size=0.01,
        start_values={
        },
        #input= np.array( [(0.0, 0.0, 1.0), (1.0, 0.3, 1.0), (5.0, 0.8, 1.0), (10.0, 1.0, 1.0)],
        #                 dtype=[('time', np.double),('inputs[0]', np.double), ('inputs[1]', np.double)]),
        output = ['outputs'],
        use_event_mode = True,        
    )
    if show:
        do_show(result['time'], result['outputs'], label='Outputs')


def test_function(*, show: bool):
    """Test the Function.fmu in isolation."""
    fmu_file = EXAMPLES_DIR / 'Function.fmu'
    assert fmu_file.exists()
    result = simulate_fmu(
        filename=fmu_file,
        start_time=0.0,
        stop_time=10.0,
        step_size=0.01,
        start_values={
            'func_name' : "sum",
            'inputs' : "1.0 5.0",
        },
        #input= np.array( [(0.0, 0.0, 1.0), (1.0, 0.3, 1.0), (5.0, 0.8, 1.0), (10.0, 1.0, 1.0)],
        #                 dtype=[('time', np.double),('inputs[0]', np.double), ('inputs[1]', np.double)]),
        output = ['output'],
    )
    assert all( _sum == 6 for _sum in result['output'][2:])


def test_linear_transform():
    fmu_file = EXAMPLES_DIR / 'LinearTransform.fmu'
    assert fmu_file.exists()
    result = simulate_fmu(
        filename=fmu_file,
        start_time=0.0,
        stop_time=10.0,
        step_size=0.1,
        start_values={
            'a': 2.0,
            'b': 3.0,
            'x': 9.0,
        },
        output = ['y'],
        use_event_mode = True,
    )
    assert all( _y == 2.0+3.0*9.0 for _y in result['y'][2:])
    

def test_two_state(*, show: bool):
    """Test the TwoState.fmu simulation in isolation through fmpy."""
    fmu_file = EXAMPLES_DIR / 'TwoState.fmu'
    assert fmu_file.exists()
    result = simulate_fmu(
        filename=fmu_file,
        start_time=0.0,
        stop_time=10.0,
        step_size=0.1,
        start_values={
            'mttf': 0.5,
            'mttr': 0.1,
            'deterministic': True,
            'seed': 1,
        },
        output = ['state'],
        use_event_mode = True,
    )
    if show:
        do_show(result['time'], result['state'], label='State')

def test_pid(*, show:bool):
    fmu_file = EXAMPLES_DIR / 'PIDController.fmu'
    assert fmu_file.exists()
    result = simulate_fmu(
        filename=fmu_file,
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
    if show:
        do_show( result['time'], result['measurement'], 'Measurement',
                 result['time'], result['output'], 'Control Output') 

if __name__ == "__main__":
    retcode = 0#pytest.main(["-rA", "-v", "--rootdir", "../", "--show", "False", __file__])
    assert retcode == 0, f"Non-zero return code {retcode}"
    # test_linear_transform()
    # test_function(show=True)
    # test_two_state(show=True)
    test_table(show=True)
    # test_pid( show=True)