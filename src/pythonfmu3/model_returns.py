"""Contains model return classes for both CoSimulation and ModelExchange,
i.e. FMI3 function returns as NamedTuple
Defined selarately, so that they can be imported where needed.
"""

from typing import NamedTuple


class Fmi3StepResult(NamedTuple):
    eventHandlingNeeded: bool = False
    terminateSimulation: bool = False
    earlyReturn: bool = False
    lastSuccessfullTime: "Float64" = 0.0

class StepResult(NamedTuple):
    event_handling_needed: bool = False
    terminate_simulation: bool = False
    early_return: bool = False
    last_successfull_time: "Float64" = 0.0


class Fmi3UpdateDiscreteStatesResult(NamedTuple):
    discreteStatesNeedUpdate: bool = False
    terminateSimulation: bool = False
    nominalContinuousStatesChanged: bool = False  # (only ME)
    valuesOfContinuousStatesChanged: bool = False
    nextEventTimeDefined: bool = False
    nextEventTime: float = 0.0
        
class UpdateDiscreteStatesResult(NamedTuple):
    discrete_states_need_update: bool = False
    terminate_simulation: bool = False
    nominal_continuous_states_changed: bool = False  # (only ME)
    values_of_continuous_states_changed: bool = False
    next_event_time_defined: bool = False
    next_event_time: float = 0.0
