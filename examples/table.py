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
    Fmi3Initial,
    Fmi3Status)
from pythonfmu3.variables import Float64, UInt64, String, Dimension
from pythonfmu3.model_returns import Fmi3StepResult, Fmi3UpdateDiscreteStatesResult
from pythonfmu3.model_options import Fmi3ModelOptionsCS

EPS = 1e-14

class Table(Fmi3Slave):
    """Input table changing values with time."""

    def __init__(self, **kwargs):
        kwargs.update({'model_options_cs' : Fmi3ModelOptionsCS(canHandleVariableCommunicationStepSize = True,
                                                               hasEventMode = True),
                       'model_options_me' : None,
                       })
        super().__init__(**kwargs)
        self.log(f"FMU instantiating: visible:{self.visible}, use events?{self.event_mode_used}")

        self.author = "Siegfried Eisinger"
        self.description = "Table with time values in first column changing row with time."

        # Parameters
        self.times = np.array([t for t in np.arange(0,10, 0.9)], float)
        self.values = np.array([[t,t**2] for t in self.times], float)
        self.n_rows : int = len(self.times)
        self.n_cols : int = len(self.values[0])

        # Inputs
        # Outputs
        self.outputs: np.ndarray = np.array([0.0]*self.n_cols, float)

        # Internal states
        self.time = 0.0
        self.row: int = -1
        self.next_time = self.times[0]

        # Register variables
        self.register_variable(Float64("time", causality=Fmi3Causality.independent))
        self._n_rows = UInt64("n_rows",
                              variability=Fmi3Variability.fixed,
                              causality=Fmi3Causality.structuralParameter, 
                              initial=Fmi3Initial.exact,
                              start=self.n_rows)
        self.register_variable(self._n_rows)
        self._n_cols = UInt64("n_cols",
                              variability=Fmi3Variability.fixed,
                              causality=Fmi3Causality.structuralParameter, 
                              initial=Fmi3Initial.exact,
                              start=self.n_cols)
        self.register_variable(self._n_cols)
        self.register_variable(Float64("times",
                                       variability=Fmi3Variability.fixed,
                                       causality=Fmi3Causality.parameter, 
                                       initial=Fmi3Initial.exact,
                                       dimensions=[Dimension(valueReference=self._n_rows.value_reference)],
                                       #start = str(self.times.flatten()).strip('[').strip(']')
                               ))
        self.register_variable(Float64("values",
                                       variability=Fmi3Variability.fixed,
                                       causality=Fmi3Causality.parameter, 
                                       initial=Fmi3Initial.exact,
                                       dimensions=[Dimension(valueReference=self._n_rows.value_reference),
                                                   Dimension(valueReference=self._n_cols.value_reference)],
                                       start = str(self.values.flatten()).strip('[').strip(']')
                                ))
        self.register_variable(Float64("outputs",
                                       causality=Fmi3Causality.output,
                                       dimensions=[Dimension(valueReference=self._n_cols.value_reference)]))
                    
    def enter_event_mode(self):
        """Signal from orchestrator that an event has occured."""
        # print(f"EnterEventMode @{self.time}")
        pass
    
    def enter_step_mode(self):
        """Signal from orchestrator that events are dealt with and switching back to step mode."""
        # print(f"EnterStepMode @{self.time}")
        pass

    def exit_initialization_mode(self):
        self.row = -1
        # print(f"Initialization finished")
        pass

    def enter_configuration_mode(self):
        print(f"Start configuration mode")
        
    def exit_configuration_mode(self):
        print(f"Start configuration mode")

    def do_step(self, current_time:float, step_size:float, *, no_set_fmu_state_prior_to_current_point:bool=True):
        self.time = current_time + step_size
        if self.time >= self.next_time:
            if not self.event_mode_used:
                _ = self.update_discrete_states()
                ret = Fmi3StepResult(eventHandlingNeeded = False, lastSuccessfullTime = self.time)                
            else:
                return Fmi3StepResult(eventHandlingNeeded = True, lastSuccessfullTime = self.next_time)
        else:
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
        self.row += 1
        if self.row < len(self.values):
            if self.row+1 < len(self.values):
                self.next_time = self.times[self.row+1]
            else:
                self.next_time = float('inf')
            self.outputs = self.values[self.row]
            return Fmi3UpdateDiscreteStatesResult( discreteStatesNeedUpdate = True,
                                                   nextEventTimeDefined = (self.next_time is not None),
                                                   nextEventTime = self.next_time)
        else:
            return Fmi3UpdateDiscreteStatesResult()

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