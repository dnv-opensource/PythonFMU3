import logging
from functools import partial
from typing import Any, Callable
import numpy as np
import numpy.typing as npt
from pythonfmu3 import Fmi3Slave
from pythonfmu3.cosimulation import Fmi3StepResult
from pythonfmu3.enums import Fmi3Variability, Fmi3Causality, Fmi3Initial, Fmi3Status
from pythonfmu3.variables import Boolean, Float64, Int32, UInt64, Dimension
from pythonfmu3.model_returns import Fmi3UpdateDiscreteStatesResult
from pythonfmu3.model_options import Fmi3ModelOptionsCS

LOGGER = logging.getLogger(__name__)


# Note: PythonFMU (which component-model is built on) works on files and thus only one Model class allowed per file


def func(time: float, ampl: npt.NDArray[np.float64], omega: npt.NDArray[np.float64], d_omega: float = 0.0):
    """Generate a harmonic oscillating force function.
    Optionally it is possible to linearly change the angular frequency as omega + d_omega*time.
    The function is intended to be initialized through partial, so that only 'time' is left as variable.
    """
    if d_omega == 0.0:
        return ampl * np.sin(omega * time)
    else:
        _omega = omega + np.ones_like(omega)* d_omega* time
        return ampl * np.sin(_omega * time)


class DrivingForce(Fmi3Slave):
    """A driving force in 3 dimensions which produces an ouput per time and can be connected to the oscillator."""

    def __init__(self, **kwargs: Any):
        kwargs.update({'model_options_cs' : Fmi3ModelOptionsCS(canHandleVariableCommunicationStepSize = True,
                                                               mightReturnEarlyFromDoStep = False,
                                                               hasEventMode = False),
                       'model_options_me' : None,
                       })
        super().__init__(**kwargs)
        self.log(f"FMU instantiating: visible:{self.visible}, use events?{self.event_mode_used}")
        self.author = "Siegfried Eisinger"
        self.description = "FMI3 version of the oscillator component model"
        
        self.time = 0.0
        self.ampl = np.array((1.0,) * 3, np.float64)
        self.dim = len(self.ampl)
        self.freq = np.array( (1.0,) * self.dim, np.float64)
        self.d_freq = 0.0

        self.function = func
        self.func: Callable
        self.f = np.array((0.0,) * self.dim, np.float64)
        self.v_osc = np.array((0.0,) * self.dim, np.float64)
        
        self.register_variable(Float64("time", causality=Fmi3Causality.independent))
        self._dim = UInt64("dim",
                           variability=Fmi3Variability.fixed,
                           causality=Fmi3Causality.structuralParameter, 
                           initial=Fmi3Initial.exact,
                           start=self.dim)
        self.register_variable(self._dim)
        self.register_variable(Float64("ampl", 
                                       variability=Fmi3Variability.fixed,
                                       causality=Fmi3Causality.parameter, 
                                       initial=Fmi3Initial.exact,
                                       dimensions=[Dimension(valueReference=self._dim.value_reference)],
                                       start="1.0 1.0 1.0"))
        self.register_variable(Float64("freq", 
                                       variability=Fmi3Variability.fixed,
                                       causality=Fmi3Causality.parameter, 
                                       initial=Fmi3Initial.exact,
                                       dimensions=[Dimension(valueReference=self._dim.value_reference)],
                                       start="1.0 1.0 1.0"))
        self.register_variable(Float64("d_freq", 
                                       variability=Fmi3Variability.fixed,
                                       causality=Fmi3Causality.parameter, 
                                       initial=Fmi3Initial.exact,
                                       start="0.0"))
        self.register_variable(Float64("f", 
                                       causality=Fmi3Causality.output,
                                       dimensions=[Dimension(valueReference=self._dim.value_reference)]))
        self.register_variable(Float64("v_osc", 
                                       causality=Fmi3Causality.input,
                                       dimensions=[Dimension(valueReference=self._dim.value_reference)],
                                       start="0.0 0.0 0.0"))

    def do_step(self,
                current_time: float,
                step_size: float,
                no_set_fmu_state_prior_to_current_point:bool=True) -> Fmi3StepResult:
        self.time = current_time + step_size
        self.f = self.func(self.time)
        ret = Fmi3StepResult(eventHandlingNeeded = False,
                             lastSuccessfullTime = self.time)
        return ret

    def exit_initialization_mode(self):
        """Set internal state after initial variables are set."""
        assert isinstance(self.ampl, np.ndarray)
        assert isinstance(self.freq, np.ndarray)
        assert isinstance(self.d_freq, float)
        self.func = partial(
            self.function,
            ampl=np.array(self.ampl, np.float64),
            omega=np.array(2 * np.pi * self.freq, np.float64),
            d_omega=2 * np.pi * self.d_freq
        )
        self.f = self.func(self.time)

if __name__ == "__main__":
    from pathlib import Path
    from pythonfmu3.builder import FmuBuilder
    from fmpy import read_model_description

    dest = FmuBuilder.build_FMU(
        script_file = Path(__file__),
        dest = Path(__file__).parent.resolve(),
        #project_files: Iterable[FilePath] = set(),
        #documentation_folder: Optional[FilePath] = None,
        #terminals : Optional[FilePath] = None,
    )
    read_model_description(dest, True, True, True)
    print(f"Generated {dest}. Validated modelDescription.")

