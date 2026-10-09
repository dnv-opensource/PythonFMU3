import logging

import numpy as np

from pythonfmu3 import Fmi3Slave
from pythonfmu3.cosimulation import Fmi3StepResult
from pythonfmu3.enums import Fmi3Causality, Fmi3Initial, Fmi3Variability
from pythonfmu3.model_options import Fmi3ModelOptionsCS
from pythonfmu3.model_returns import Fmi3UpdateDiscreteStatesResult
from pythonfmu3.unit import Unit
from pythonfmu3.variables import Float64

LOGGER = logging.getLogger(__name__)

EPS = 1e-13

class BouncingBall(Fmi3Slave):
    def __init__(self, **kwargs):
        kwargs.update({'model_options_cs' : Fmi3ModelOptionsCS(canHandleVariableCommunicationStepSize = True,
                                                               mightReturnEarlyFromDoStep = True,
                                                               hasEventMode = True),
                       'model_options_me' : None,
                       })
        
        super().__init__(**kwargs)

        self.log(f"FMU Function instantiating: visible:{self.visible}, use events?{self.eventModeUsed}")
        self.author = "..."
        self.description = "Bouncing Ball as FMI3 component with event handling"

        self.time = 0.0
        self.h = 1.0
        self.v = 0.0
        self.derh = 0.0
        self.derv = 0.0
        self.g = -9.81
        self.e = 0.7
        self.v_min = 0.1
        self.next_bounce: float
        self.energy_min: float

        # define units
        unit1 = Unit(name="m", m=1)
        unit2 = Unit(name="m/s", m=1, s=-1)
        unit3 = Unit(name="m/s2", m=1, s=-2)
        self.register_units([unit1, unit2, unit3])

        self.register_variable(
            Float64("time", causality=Fmi3Causality.independent, variability=Fmi3Variability.continuous)
        )

        self.register_variable(
            Float64("h",
                    causality=Fmi3Causality.output,
                    variability=Fmi3Variability.continuous,
                    initial=Fmi3Initial.exact,
                    unit=unit1.name,
                    start=1,
            ))
        self.register_variable(
            Float64("derh",
                    causality=Fmi3Causality.local,
                    variability=Fmi3Variability.continuous,
                    derivative=1,
                    unit=unit2.name,
                   ))
        self.register_variable(
            Float64("v",
                    causality=Fmi3Causality.output,
                    start=0,
                    variability=Fmi3Variability.continuous,
                    initial=Fmi3Initial.exact,
                    unit=unit2.name,
                   ))
        self.register_variable(
            Float64("derv",
                    causality=Fmi3Causality.local,
                    variability=Fmi3Variability.continuous,
                    derivative=3,
                    unit=unit3.name,
                   ))

        self.register_variable(
            Float64("g",
                    causality=Fmi3Causality.parameter,
                    variability=Fmi3Variability.fixed,
                    unit=unit3.name,
                    start="-9.81"
                   ))
        self.register_variable(
            Float64("e",
                    causality=Fmi3Causality.parameter,
                    variability=Fmi3Variability.tunable,
                    start="0.7"
                   ))
        self.register_variable(
            Float64("v_min", causality=Fmi3Causality.parameter,
                    variability=Fmi3Variability.fixed,
                    start=0.1)
        )
    
    def calc_next_bounce(self):
        """Calculate the next bounce time as interval from current time."""
        if self.h == 0.0 and self.v == 0.0: # bouncing stopped
            return float('inf')
        return -self.v/self.g + np.sqrt((self.v/self.g)**2 - 2*self.h/self.g)
    
    def exit_initialization_mode(self):
        self.derv = self.g # constant
        self.next_bounce = self.time + self.calc_next_bounce()
        self.energy_min = 0.5* self.v_min* self.v_min

    def do_step(self, current_time:float, step_size:float, noSetFmuStatePriorToCurrentPoint:bool=True):
        self.time = current_time + step_size
        assert not self.eventModeUsed or self.time < self.next_bounce + EPS, (
            f"Time {self.time} > {self.next_bounce}"
        )
        self.derh = self.v
        self.h += (self.derh + 0.5*self.derv* step_size)*step_size
        self.v += self.derv * step_size
        
        event_handling_needed: bool = False
        if self.eventModeUsed and abs(self.time - self.next_bounce) < EPS:
            event_handling_needed = True # calculate the next bounce
            
        elif self.h <= 0 and self.v < 0: # when eventMode is not used
            self.h = 1e-12
            self.v = -self.v * self.e
            
        if not self.eventModeUsed and 0.5*self.v**2 - self.g*self.h < self.energy_min: # stop the bouncing
            self.v = 0
            self.derv = 0
        ret = Fmi3StepResult(eventHandlingNeeded = event_handling_needed,
                             lastSuccessfullTime = self.time)
        return ret

    def update_discrete_states(self):
        """Call by Orchestrator to update discrete states in super-dense time instant,
        returning info to the Orchestrator on e.g. nextEventTime

        Returns:
            discreteStatesNeedUpdate: True; the Orchestrator must stay in Event Mode for another event iteration,
               starting a new super-dense time instant.
            terminateSimulation: True; the FMU requests to stop the simulation.
            nominalsOfContinuousStatesChanged: True; use only for ME!
            valuesOfContinuousStatesChanged: False; use only for configuration changes
            nextEventTimeDefined: True; the next time event is known and nextEventTime has a valid value.
            nextEventTime: contains the absolute time of the next time event if nextEventTimeDefined = True.
               The importer must compute up to nextEventTime (or if needed slightly further)
               and then enter Event Mode using EnterEventMode.
               The FMU must handle this time event during the Event Mode that is entered
               by the first call to EnterEventMode, at or after nextEventTime.
               If another (e.g. state event) event happens before that nextEventTime,
               the previous definition of nextEventTime becomes obsolete.
        """
        if self.time > 0.0:
            self.h = 0.0 # avoid numerical issues. Bounce always at ground
            if abs(self.v) < self.v_min:
                self.v = 0.0
                self.derv = 0.0
            else:
                self.v = -self.v * self.e

        self.next_bounce = self.time + self.calc_next_bounce()
        return Fmi3UpdateDiscreteStatesResult(discreteStatesNeedUpdate=False,
                                              nextEventTimeDefined=True,
                                              nextEventTime=self.next_bounce)

if __name__ == "__main__":
    from pathlib import Path

    from fmpy import read_model_description

    from pythonfmu3.builder import FmuBuilder

    dest = FmuBuilder.build_FMU(
        script_file = Path(__file__),
        dest = Path(__file__).parent.resolve(),
        #project_files: Iterable[FilePath] = set(),
        #documentation_folder: Optional[FilePath] = None,
        #terminals : Optional[FilePath] = None,
    )
    read_model_description(dest, True, True, True)
    print(f"Generated {dest}. Validated modelDescription.")