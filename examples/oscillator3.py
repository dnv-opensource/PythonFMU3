import logging
import numpy as np
import numpy.typing as npt
from scipy import integrate
from pythonfmu3 import Fmi3Slave
from pythonfmu3.cosimulation import Fmi3StepResult
from pythonfmu3.enums import Fmi3Variability, Fmi3Causality, Fmi3Initial, Fmi3Status
from pythonfmu3.variables import Boolean, Float64, Int32, UInt64, Dimension
from pythonfmu3.model_returns import Fmi3UpdateDiscreteStatesResult
from pythonfmu3.model_options import Fmi3ModelOptionsCS

LOGGER = logging.getLogger(__name__)


class Oscillator(Fmi3Slave):
    """Construct a simple model of a general harmonic oscillator, potentially driven by a force.

    The system obeys the equation F(t) - k*x - c*dx/dt = m*d^2x/dt^2
    See also `Wikipedia <https://en.wikipedia.org/wiki/Harmonic_oscillator>`_

    where x shall be a 3D vector with an initial position. F(t)=0 as long as there is not external driving force.

    We use the scipy.integrate.solve_ivp algorithm for the integration (see do_step)

    Args:
        k (tuple)=(1.0, 1.0, 1.0): spring constant in N/m. May vary in 3D
        c (tuple)=(0.0, 0.0, 0.0): Viscous damping coefficient in N.s/m. May vary in 3D
        m (float | tuple)=1.0: Mass of the spring load (spring mass negligible) in kg. Same in all dim. if float
        tolerance (float)=1e-5: Optional tolerance in m, i.e. maximum uncertainty in displacement x.
    """

    def __init__(self, **kwargs):
        kwargs.update({'model_options_cs' : Fmi3ModelOptionsCS(canHandleVariableCommunicationStepSize = True,
                                                               mightReturnEarlyFromDoStep = False,
                                                               hasEventMode = False),
                       'model_options_me' : None,
                       })
        super().__init__(**kwargs)
        self.log(f"FMU instantiating: visible:{self.visible}, use events?{self.eventModeUsed}")
        self.author = "Siegfried Eisinger"
        self.description = "FMI3 version of the oscillator component model"
        
        self.time = 0.0
        self.k = np.array((1.0, 1.0, 1.0), np.float64)
        self.dim = len(self.k) # internal variable
        self.c = np.array((0.0, 0.0, 0.0), np.float64)
        self.m = np.array((1.0,) * self.dim, np.float64)
        self.tolerance = 1e-5
        self.x = np.array((0,) * self.dim, np.float64)
        self.v = np.array((0,) * self.dim, np.float64)
        self.f = np.array((0,) * self.dim, np.float64)
        self.ode : npt.NDArray[np.float64] # Defined after initialization:
        
        # Register variables
        self.register_variable(Float64("time", causality=Fmi3Causality.independent))
        self._dim = UInt64("dim",
                           variability=Fmi3Variability.fixed,
                           causality=Fmi3Causality.structuralParameter, 
                           initial=Fmi3Initial.exact,
                           start=self.dim)
        self.register_variable(self._dim)
        self.register_variable(Float64("k", 
                                       variability=Fmi3Variability.fixed,
                                       causality=Fmi3Causality.parameter, 
                                       initial=Fmi3Initial.exact,
                                       dimensions=[Dimension(valueReference=self._dim.value_reference)],
                                       start="1.0 1.0 1.0"))
        self.register_variable(Float64("c", 
                                       variability=Fmi3Variability.fixed,
                                       causality=Fmi3Causality.parameter, 
                                       initial=Fmi3Initial.exact,
                                       dimensions=[Dimension(valueReference=self._dim.value_reference)],
                                       start="0.0 0.0 0.0"))
        self.register_variable(Float64("x", 
                                       causality=Fmi3Causality.output,
                                       variability=Fmi3Variability.continuous,
                                       initial=Fmi3Initial.exact,
                                       dimensions=[Dimension(valueReference=self._dim.value_reference)],
                                       start="1.0 0.0 0.0"))
        self.register_variable(Float64("v", 
                                       causality=Fmi3Causality.output,
                                       variability=Fmi3Variability.continuous,
                                       initial=Fmi3Initial.exact,
                                       dimensions=[Dimension(valueReference=self._dim.value_reference)],
                                       start="0.0 0.0 0.0"))
        self.register_variable(Float64("f", 
                                       causality=Fmi3Causality.input,
                                       dimensions=[Dimension(valueReference=self._dim.value_reference)]))


    def exit_initialization_mode(self):
        self.ode = [ # standard ODE matrix (homogeneous system).
            np.array(((-self.c[i] / self.m[i], -self.k[i] / self.m[i]), (1, 0)), float) for i in range(self.dim)
        ]


    def ode_func(
        self,
        t: float,  # scalar time
        y: np.ndarray,  # combined array of position and speed for component i
        i: int,  # dimension
        f: float,
    ) -> np.ndarray:  # force for component i
        res = self.ode[i].dot(y)
        if f != 0:
            res += np.array((f, 0), float)
        return res

    def do_step(self,
                current_time: float,
                step_size: float,
                noSetFmuStatePriorToCurrentPoint:bool=True) -> Fmi3StepResult:
        """Do one simulation step of size dt.

        We implement a very simplistic algoritm based on difference calculus.
        """
        self.time = current_time + step_size
        for i in range(self.dim):  # this is a xD oscillator
            if self.x[i] != 0 or self.v[i] != 0 or self.f[i] != 0:
                y0 = np.array([self.v[i], self.x[i]], float)
                sol = integrate.solve_ivp(
                    fun=self.ode_func,
                    t_span=[current_time, current_time + step_size],
                    y0=y0,
                    args=(i, self.f[i]),  # axis and force as extra arguments to fun
                    atol=self.tolerance,
                )
                self.x[i] = sol.y[1][-1]
                self.v[i] = sol.y[0][-1]
        ret = Fmi3StepResult(eventHandlingNeeded = False,
                             lastSuccessfullTime = self.time)
        return ret

    @property
    def period(self):
        """Calculate the natural period of the oscillator (without damping an)."""
        w2 = []
        for i in range(self.dim):
            w2i = self.k[i] / self.m[i] - (self.c[i] / 2 / self.m[i]) ** 2
            if w2i > 0:
                w2.append(2 * np.pi / np.sqrt(w2i))
            else:
                w2.append(float("nan"))  # critically or over-damped. There is no period
        return w2

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
