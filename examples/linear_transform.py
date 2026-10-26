"""Implements a function component with n scalar inputs and one output.
   The function name can be specified.
   
   The function triggers only on input events and calculates its output,
   i.e. it triggers on update_discrete_states, updating the output, not setting new event times.
   do_step only keeps track of time.
"""
import numpy as np
from collections import namedtuple
from pythonfmu3 import Fmi3Slave
from pythonfmu3.enums import (
    Fmi3IntervalVariability,
    Fmi3Causality,
    Fmi3Variability,
    Fmi3Status)
from pythonfmu3.variables import Float64, UInt64, String, Dimension
from pythonfmu3.model_returns import Fmi3StepResult, Fmi3UpdateDiscreteStatesResult
from pythonfmu3.model_options import Fmi3ModelOptionsCS

EPS = 1e-14

class LinearTransform(Fmi3Slave):
    """Linear transformation of a scalar input value."""

    def __init__(self, **kwargs):
        kwargs.update({'model_options_cs' : Fmi3ModelOptionsCS(canHandleVariableCommunicationStepSize = True,
                                                               hasEventMode = True),
                       'model_options_me' : None,
                       })
        super().__init__(**kwargs)

        self.author = "Siegfried Eisinger"
        self.description = "Linear transformation of a scalar input value: y = a + b*x"

        # Internal states
        self.time = 0.0 # actually independent of time

        # Parameters
        self.a : float = 0.0 # intercept
        self.b : float = 1.0 # slope

        # Inputs
        self.x: float = 0.0
        # Outputs
        self.y: float = self.transform(self.x)

        # Register variables
        self.register_variable(Float64("time", causality=Fmi3Causality.independent))
        self.register_variable(Float64("a", causality=Fmi3Causality.parameter, start=0.0))
        self.register_variable(Float64("b", causality=Fmi3Causality.parameter, start=1.0))

        self.register_variable(Float64("x", causality=Fmi3Causality.input, start=0.0))
        self.register_variable(Float64("y", causality=Fmi3Causality.output))
                    
    def enter_event_mode(self):
        """Signal from orchestrator that an event has occured."""
        # print(f"EnterEventMode @{self.time}")
        pass
    
    def enter_step_mode(self):
        """Signal from orchestrator that events are dealt with and switching back to step mode."""
        # print(f"EnterStepMode @{self.time}")
        pass

    def exit_initialization_mode(self):
        # print(f"Initialization finished")
        pass

    def do_step(self, current_time:float, step_size:float, *, no_set_fmu_state_prior_to_current_point:bool=True):
        self.time = current_time + step_size
        self.y = self.transform(self.x)
        return Fmi3StepResult(eventHandlingNeeded = False, lastSuccessfullTime = self.time)
    
    def update_discrete_states(self):
        """Call by Orchestrator to update discrete states in super-dense time instant,
        returning info to the Orchestrator

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
        self.y = self.transform(self.x)
        return Fmi3UpdateDiscreteStatesResult(discreteStatesNeedUpdate = True)

    def transform(self, x:float):
        return self.a + self.b* x

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