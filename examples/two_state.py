"""Implements a two-state discrete event system with states `working=1` and 'failed=0`
    The MTTF and MTTR are fixed parameters and the actual TTF is exponentially distributed, 
    while TTR is modelled as constant time interval.

   When `enterEventMode` is called, the state changes and a new time interval is calculated,
   which is transmitted to the orchestrator with a `getIntervalDecimal` call.
"""
import numpy as np
from collections import namedtuple
from pythonfmu3 import Fmi3Slave
from pythonfmu3.enums import Fmi3IntervalVariability, Fmi3Causality, Fmi3Status
from pythonfmu3.variables import Float64, Int32, Clock
from pythonfmu3.fmi3slave import Fmi3StepResult, Fmi3UpdateDiscreteStatesResult

EPS = 1e-14

class TwoState(Fmi3Slave):
    """Two-state discrete event implementation"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.author = "Siegfried Eisinger"
        self.description = "Two-state discrete event system."
        
        # Parameters
        self.mttf = 1.0  # Mean time to failure (ttf exponentially distributed)
        self.mttr = 0.01 # Mean time to repair (ttr constant)
        self.seed = 1

        # Inputs

        # Outputs
        self.state = 1

        # Internal states
        self.rng = np.random.default_rng(self.seed)
        self.next_interval = self.get_next_interval()
        self.time = 0.0
        self.histogram : list[ tuple[float,int]] = []

        # Register variables
        self.register_variable(Float64("time", causality=Fmi3Causality.independent))
        self.register_variable(Float64("mttf", causality=Fmi3Causality.parameter, start=1.0))
        self.register_variable(Float64("mttr", causality=Fmi3Causality.parameter, start=0.01))
        self.register_variable(Int32("seed", causality=Fmi3Causality.parameter, start=1))
        self.register_variable(Int32("state", causality=Fmi3Causality.output))
        self.register_variable(Clock("next_interval",
                                     interval_variability=Fmi3IntervalVariability.triggered,
                                     interval_decimal=self.next_interval,
                                     ))

    def get_next_interval(self):
        if self.state==0:
            return self.mttr
        elif self.state==1:
            return self.rng.exponential(self.mttf)
        else:
            raise ValueError(f"Unallowed state {self.state}") from None
            
    def enter_event_mode(self):
        """Signal from orchestrator that an event has occured."""
        print(f"EnterEventMode @{self.time}")
    
    def enter_step_mode(self):
        """Signal from orchestrator that events are dealt with and switching back to step mode."""
        print(f"EnterStepMode @{self.time}")

    def exit_initialization_mode(self):
        print(f"Initialization finished")

    def do_step(self, current_time, step_size):
        self.time = current_time + step_size
        self.histogram.append( (current_time, self.state))

        return Fmi3StepResult(status=Fmi3Status.ok,
                              eventHandlingNeeded=(self.time>self.next_time-EPS))
    
    def update_discrete_states(self):
        """Call by Orchestrator to update discrete states in super-dense time instant,
        returning info to the Orchestrator on e.g. nextEventTime

        Returns:
            discreteStatesNeedUpdate: True; the Orchestrator must stay in Event Mode for another event iteration,
               starting a new super-dense time instant.
            terminateSimulation: True; the FMU requests to stop the simulation.
            nominalsOfContinuousStatesChanged: True; use only for ME!
            valuesOfContinuousStatesChanged: True; use only for ME!
            nextEventTimeDefined: True; the next time event is known and nextEventTime has a valid value.
            nextEventTime: contains the absolute time of the next time event if nextEventTimeDefined = True.
               The importer must compute up to nextEventTime (or if needed slightly further)
               and then enter Event Mode using EnterEventMode.
               The FMU must handle this time event during the Event Mode that is entered
               by the first call to EnterEventMode, at or after nextEventTime.
               If another (e.g. state event) event happens before that nextEventTime,
               the previous definition of nextEventTime becomes obsolete.
        """
        self.state = 1 if self.time == 0.0 else 1 - self.state
        self.next_interval = self.get_next_interval()
        self.next_time = self.time + self.next_interval
        print(f"UpdateDiscreteStates @ {self.time} => {self.state}, {self.next_time}")
            
# dict does not work
#         return ( False, # discreteStatesNeedUpdate
#                  False, # terminateSimulation
#                  False, # nominalContinuousStatesChanged (only ME)
#                  False, # valuesOfContinuousStatesChanged
#                  True, # nextEventTimeDefined,
#                  self.next_interval, #nextEventTime
#                  )
        return Fmi3UpdateDiscreteStatesResult( nextEventTimeDefined=True, nextEventTime=self.next_interval)


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