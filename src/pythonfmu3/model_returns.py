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

class Fmi3UpdateDiscreteStatesResult(NamedTuple):
    discreteStatesNeedUpdate: bool = False
    terminateSimulation: bool = False
    nominalContinuousStatesChanged: bool = False # (only ME)
    valuesOfContinuousStatesChanged: bool = False
    nextEventTimeDefined: bool = False
    nextEventTime: float = 0.0


class Fmi3StepResult(NamedTuple):
    eventHandlingNeeded: bool = False
    terminateSimulation: bool = False
    earlyReturn: bool = False
    lastSuccessfullTime: "Float64" = 0.0
