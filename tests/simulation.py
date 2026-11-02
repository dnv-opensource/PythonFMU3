from math import isclose
from time import time as current_communication_point

from fmpy.fmi1 import *
from fmpy.fmi2 import *
from fmpy.simulation import (
    Input,
    Recorder,
    apply_start_values,
    settable_in_initialization_mode,
    settable_in_instantiated,
)
from fmpy.util import auto_interval


def _simulateCS(
    model_description,
    fmu,
    start_time,
    stop_time,
    relative_tolerance,
    start_values,
    apply_default_start_values,
    input_signals,
    output,
    output_interval,
    timeout,
    step_finished,
    set_input_derivatives,
    use_event_mode,
    early_return_allowed,
    validate,
    initialize,
    terminate,
    set_stop_time,
):
    """Copy of fmpy.simulation.simulateCS() function,
    where we put in hooks to test the implemented event functions.
    """
    print(f"RUNNING ADAPTED SIMULATE. events?{use_event_mode}")
    nextEventTime: float | None = None
    if set_input_derivatives and not model_description.coSimulation.canInterpolateInputs:
        raise Exception("Parameter set_input_derivatives is True but the FMU cannot interpolate inputs.")

    if output_interval is None:
        output_interval = auto_interval(stop_time - start_time)

    sim_start = current_communication_point()

    is_fmi1 = model_description.fmiVersion == "1.0"
    is_fmi2 = model_description.fmiVersion == "2.0"

    can_handle_variable_step_size = model_description.coSimulation.canHandleVariableCommunicationStepSize

    input = Input(
        fmu=fmu, modelDescription=model_description, signals=input_signals, set_input_derivatives=set_input_derivatives
    )

    time = start_time

    if initialize:
        # initialize the model
        if is_fmi1:
            start_values = apply_start_values(fmu, model_description, start_values, settable=has_start_value)
            input.apply(time)
            fmu.initialize(tStart=time, stop_time=stop_time if set_stop_time else None)
        elif is_fmi2:
            fmu.setupExperiment(
                tolerance=relative_tolerance, start_time=time, stop_time=stop_time if set_stop_time else None
            )
            start_values = apply_start_values(fmu, model_description, start_values, settable=settable_in_instantiated)
            fmu.enterInitializationMode()
            start_values = apply_start_values(
                fmu, model_description, start_values, settable=settable_in_initialization_mode
            )
            input.apply(time)
            fmu.exitInitializationMode()
        else:
            start_values = apply_start_values(fmu, model_description, start_values, settable=settable_in_instantiated)
            fmu.enterInitializationMode(
                tolerance=relative_tolerance, startTime=time, stopTime=stop_time if set_stop_time else None
            )
#            fmu.enterInitializationMode(relative_tolerance, time, stop_time)
            start_values = apply_start_values(
                fmu, model_description, start_values, settable=settable_in_initialization_mode
            )
            input.apply(time)
            fmu.exitInitializationMode()

            if use_event_mode:
                update_discrete_states = True

                while update_discrete_states:
                    (update_discrete_states, terminateSimulation, _, _, _nETD, _nET) = fmu.updateDiscreteStates()

                if terminateSimulation:
                    raise Exception("The FMU requested to terminate the simulation during initialization.")
                if _nETD:
                    nextEventTime = time + _nET
                fmu.enterStepMode()

    if validate and len(start_values) > 0:
        raise Exception(
            "The start values for the following variables could not be set: " + ", ".join(start_values.keys())
        )

    recorder = Recorder(fmu=fmu, modelDescription=model_description, variableNames=output, interval=output_interval)

    recorder.sample(time, force=True)

    n_steps = 0

    input_applied = False

    # simulation loop
    while True:
        if timeout is not None and (current_communication_point() - sim_start) > timeout:
            break

        if time > stop_time or isclose(time, stop_time):
            break

        next_regular_point = start_time + (n_steps + 1) * output_interval

        next_communication_point = next_regular_point

        next_input_event_time = input.nextEvent(time)

        if (
            can_handle_variable_step_size
            and next_communication_point > next_input_event_time
            and not isclose(next_communication_point, next_input_event_time)
        ):
            next_communication_point = next_input_event_time

        if next_communication_point > stop_time and not isclose(next_communication_point, stop_time):
            if can_handle_variable_step_size:
                next_communication_point = stop_time
            else:
                break

        input_event = isclose(next_communication_point, next_input_event_time)

        communication_step_size = next_communication_point - time

        if is_fmi1:
            input.apply(time, continuous=True, discrete=True, after_event=True)

            fmu.doStep(current_communication_point=time, communication_step_size=communication_step_size)

            time = next_communication_point

            recorder.sample(time)

        elif is_fmi2:
            input.apply(time, continuous=True, discrete=True, after_event=True)

            try:
                fmu.doStep(current_communication_point=time, communication_step_size=communication_step_size)

                time = next_communication_point

            except FMICallException as exception:
                if exception.status == fmi2Discard:
                    terminateSimulation = fmu.getBooleanStatus(fmi2Terminated)

                    if terminateSimulation:
                        time = fmu.getRealStatus(fmi2LastSuccessfulTime)
                        recorder.sample(time, force=True)
                        break
                else:
                    raise exception

            recorder.sample(time)

        else:
            input.apply(time, continuous=not input_applied, discrete=not input_applied, after_event=not use_event_mode)

            (event_encountered, terminateSimulation, earlyReturn, last_successful_time) = fmu.doStep(
                currentCommunicationPoint=time,
                communicationStepSize=communication_step_size,
                noSetFMUStatePriorToCurrentPoint=False
            )

            if earlyReturn and not early_return_allowed:
                raise Exception("FMU returned early from doStep() but Early Return is not allowed.")

            if earlyReturn and last_successful_time < next_communication_point:
                time = last_successful_time
            else:
                time = next_communication_point

            recorder.sample(time)

            if terminateSimulation:
                break

            if use_event_mode and (input_event or event_encountered):
                fmu.enterEventMode()

                input.apply(time, after_event=True)

                update_discrete_states = True

                while update_discrete_states:
                    update_discrete_states, terminateSimulation, _, _, _, _ = fmu.updateDiscreteStates()

                    if terminateSimulation:
                        break

                fmu.enterStepMode()

                recorder.sample(time)

                input_applied = True
            else:
                input_applied = False

        if isclose(time, next_regular_point):
            n_steps += 1

        if step_finished is not None and not step_finished(time, recorder):
            break

    if terminate:
        fmu.terminate()

    return recorder.result()
