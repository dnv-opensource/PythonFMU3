"""Implements a two-state discrete event component with states `working=1` and 'failed=0`
    The MTTF and MTTR are fixed parameters and the actual TTF is exponentially distributed, 
    while TTR is modelled as constant time interval.

   When `update_discrete_states` is called, the state changes and a new time interval is calculated,
   which is transmitted to the orchestrator as one of its return values.
   Clocks are not used in this version.
"""
import logging
import numpy as np
from pythonfmu3 import Fmi3Slave
from pythonfmu3.cosimulation import Fmi3StepResult
from pythonfmu3.enums import Fmi3IntervalVariability, Fmi3Causality, Fmi3Status
from pythonfmu3.variables import Boolean, Float64, Int32, Clock
from pythonfmu3.model_returns import Fmi3UpdateDiscreteStatesResult
from pythonfmu3.model_options import Fmi3ModelOptionsCS

LOGGER = logging.getLogger(__name__)

EPS = 1e-14

class TwoState(Fmi3Slave):
    """Two-state discrete event implementation"""

    def __init__(self, **kwargs):
        kwargs.update({'model_options_cs' : Fmi3ModelOptionsCS(canHandleVariableCommunicationStepSize = True,
                                                               mightReturnEarlyFromDoStep = True,
                                                               hasEventMode = True),
                       'model_options_me' : None,
                       })
        super().__init__(**kwargs)
        self.log(f"FMU instantiating: visible:{self.visible}, use events?{self.eventModeUsed}")
        self.author = "Siegfried Eisinger"
        self.description = "Two-state discrete event system."
        
        # Parameters
        self.mttf = 0.1  # Mean time to failure (ttf exponentially distributed)
        self.mttr = 0.01 # Mean time to repair (ttr constant)
        self.seed = 1
        self.rng = np.random.default_rng(self.seed)
        self.deterministic = False

        # Inputs

        # Outputs
        self.state = 1

        # Internal states
        self.next_interval = self.get_next_interval()
        self.time = 0.0
        self.next_time = 0.0
        self.histogram : list[ tuple[float,int]] = []

        # Register variables
        self.register_variable(Float64("time", causality=Fmi3Causality.independent))
        self.register_variable(Float64("mttf", causality=Fmi3Causality.parameter, start=1.0))
        self.register_variable(Float64("mttr", causality=Fmi3Causality.parameter, start=0.01))
        self.register_variable(Int32("seed", causality=Fmi3Causality.parameter, start=1))
        self.register_variable(Boolean("deterministic", causality=Fmi3Causality.parameter, start=False))
        self.register_variable(Int32("state", causality=Fmi3Causality.output))
        self.register_variable(Clock("next_interval",
                                     interval_variability=Fmi3IntervalVariability.triggered,
                                     interval_decimal=self.next_interval,
                                     ))

    def get_next_interval(self):
        if self.state==0:
            return self.mttr
        elif self.state==1:
            if self.deterministic:
                return self.mttf
            else:
                return self.rng.exponential(self.mttf)
        else:
            raise ValueError(f"Unallowed state {self.state}") from None

    def enter_event_mode(self):
        """Signal from orchestrator that an event has occured."""
        # print(f"EnterEventMode @{self.time}")
        pass
    
    def enter_step_mode(self):
        """Signal from orchestrator that events are dealt with and switching back to step mode."""
        # print(f"EnterStepMode @{self.time}")
        pass

    def exit_initialization_mode(self):
        self.log(f"Initialization finished. hasEventMode:{self.model_options_cs.hasEventMode}. UseEvents? {getattr(self, 'eventModeUsed', False)}")
        self.rng = np.random.default_rng(self.seed)


    def do_step(self, current_time:float, step_size:float, noSetFmuStatePriorToCurrentPoint:bool=True):
        self.time = current_time + step_size
        self.histogram.append( (current_time, self.state))
        if self.time >= self.next_time-EPS:
            if not self.eventModeUsed:
                _ = self.update_discrete_states()
                ret = Fmi3StepResult(eventHandlingNeeded = False,
                                     lastSuccessfullTime = self.time)                
            else:
                ret = Fmi3StepResult(eventHandlingNeeded = True,
                                     lastSuccessfullTime = self.next_time)
            #print(f"DoStep@{current_time}: {ret}")
        else:
            ret = Fmi3StepResult(eventHandlingNeeded = False,
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
        self.state = 1 if self.time == 0.0 else 1 - self.state
        self.next_interval = self.get_next_interval()
        self.next_time = self.time + self.next_interval
        # self.log(f"Update {self.instance_name}(TwoState) @{self.time} => {self.state}. NextT:{self.next_time}")            
        return Fmi3UpdateDiscreteStatesResult(discreteStatesNeedUpdate=True,
                                              nextEventTimeDefined=True,
                                              nextEventTime=self.next_time)


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