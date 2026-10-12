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

class Function(Fmi3Slave):
    """Discrete event Function implementation."""

    def __init__(self, **kwargs):
        kwargs.update({'model_options_cs' : Fmi3ModelOptionsCS(canHandleVariableCommunicationStepSize = True,
                                                               hasEventMode=True),
                       'model_options_me' : None,
                       })
        super().__init__(**kwargs)

        self.log(f"FMU Function instantiating: visible:{self.visible}, use events?{self.eventModeUsed}")
        self.author = "Siegfried Eisinger"
        self.description = "Function of its inputs, updating the output"
        
        # Parameters
        self.n_inputs : int = 2
        self.func_name : str = "sum"
        self.par : float = 1.0

        # Inputs
        self.inputs: np.ndarray = np.array([0.0]*self.n_inputs, float)
        # Outputs
        self.output: float = 0.0 

        # Internal states
        self.time = 0.0
        self.histogram : list[ tuple[float,int]] = []

        # Register variables
        self.register_variable(Float64("time", causality=Fmi3Causality.independent))
        self._n_inputs = UInt64("n_inputs",
                                variability=Fmi3Variability.fixed,
                                causality=Fmi3Causality.structuralParameter, 
                                initial=Fmi3Initial.exact,
                                start=2)
        self.register_variable(self._n_inputs)
        self.register_variable(String("func_name", causality=Fmi3Causality.parameter, start="sum"))
        self.register_variable(Float64("par", causality=Fmi3Causality.parameter, start=1.0))
        self.register_variable(Float64("inputs",
                                       variability=Fmi3Variability.continuous,
                                       causality=Fmi3Causality.input, 
                                       dimensions=[Dimension(valueReference=self._n_inputs.value_reference)],
                                       start=(1.0, 1.0) ))
        self.register_variable(Float64("output", causality=Fmi3Causality.output))
        

    def calc(self)-> float:
        """Re-calculate the function."""
        if self.func_name == "sum":
            if self.par == 1.0:
                return sum( x for x in self.inputs)
            else:
                return self.par* sum( x for x in self.inputs)
        elif self.func_name == "and":
            res = True
            for x in self.inputs:
                if not x:
                    return 0.0
            return 1.0
        elif self.func_name == "or":
            res = False
            for x in self.inputs:
                if x:
                    return 1.0
            return 0.0
        elif self.func_name == "min":
            return min(self.inputs)
        elif self.func_name == "max":
            return max(self.inputs)
        raise NotImplementedError(f"The function {self.func_name} is so far not included.") from None
            
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
        self.output = float('nan') # no inputs that, therefore output is initially undefined
        pass

    def do_step(self, current_time:float, step_size:float, noSetFmuStatePriorToCurrentPoint:bool=True):
        self.time = current_time + step_size
        if not self.eventModeUsed:
            self.histogram.append( (current_time, self.output))
            self.output = self.calc()
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
        before_update = self.output
        after_update = self.calc()
        #self.log(f"Update {self.instance_name}(Function): Inputs:{self.inputs}. {before_update} -> {after_update}")
        if before_update != after_update:
            self.output = after_update
            # make sure that all inputs are updated and loops are managed.
            return Fmi3UpdateDiscreteStatesResult( discreteStatesNeedUpdate=True) 
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