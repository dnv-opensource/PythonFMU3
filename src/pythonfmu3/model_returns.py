"""Contains model return classes for both CoSimulation and ModelExchange,
i.e. FMI3 function returns as NamedTuple
Defined selarately, so that they can be imported where needed.
"""

from typing import NamedTuple


class Fmi3StepResult(NamedTuple):
    """Signal the results from do_step to the orchestrator.

    Returns
        eventHandingNeeded: True; the orchestrator must swithc to event mode.
        terminateSimulation: True; the FMU requests to stop the simulation.
        earlyReturn: True; the FMU singals that it returned early (step not fully done)
        lastSuccessfullTime: If earlyReturn=True, provide the time until which the step was performed.
    """
    eventHandlingNeeded: bool = False
    terminateSimulation: bool = False
    earlyReturn: bool = False
    lastSuccessfullTime: "Float64" = 0.0

class Fmi3UpdateDiscreteStatesResult(NamedTuple):
    """Signal the results from update_discrete_events to the orchestrator.

    Returns:
        discreteStatesNeedUpdate: True; the Orchestrator must stay in Event Mode for another event iteration,
           starting a new super-dense time instant. Never only return 'True' since it leads to an infinite loop!
        terminateSimulation: True; the FMU requests to stop the simulation.
        nominalsOfContinuousStatesChanged: True; use only for ME!
        valuesOfContinuousStatesChanged: False; use only for configuration changes
        nextEventTimeDefined: True; the next time event is known and nextEventTime has a valid value.
        nextEventTime: contains the absolute time of the next time event if nextEventTimeDefined = True.
    """
    discreteStatesNeedUpdate: bool = False 
    terminateSimulation: bool = False 
    nominalContinuousStatesChanged: bool = False  # (only ME)
    valuesOfContinuousStatesChanged: bool = False 
    nextEventTimeDefined: bool = False
    nextEventTime: float = 0.0
