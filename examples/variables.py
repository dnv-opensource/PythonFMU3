"""Defines various variable types and shapes and exports them."""
import numpy as np
import numpy.typing as npt
from pythonfmu3.fmi3slave import Fmi3Slave
from pythonfmu3.enums import (
    Fmi3IntervalVariability,
    Fmi3Causality,
    Fmi3Variability,
    Fmi3Initial,
    Fmi3Status)
from pythonfmu3.variables import Boolean, Dimension, Enumeration, String
from pythonfmu3.variables import Float64, Float32
from pythonfmu3.variables import Int64, Int32, Int16, Int8
from pythonfmu3.variables import UInt64, UInt32, UInt16, UInt8
from pythonfmu3.model_returns import Fmi3StepResult, Fmi3UpdateDiscreteStatesResult
from pythonfmu3.model_options import Fmi3ModelOptionsCS

EPS = 1e-14

class Variables3(Fmi3Slave):
    """Various variables and shapes, always defined as input-output pair."""

    def __init__(self,
                 model_options_cs = Fmi3ModelOptionsCS(**{'canHandleVariableCommunicationStepSize':True,
                                                          'hasEventMode':True}),
                 **kwargs
                ):
        kwargs.update({'model_options_cs' : model_options_cs})
        super().__init__(**kwargs)
        self.log(f"FMU instantiating: visible:{self.visible}, use events?{self.event_mode_used}")
        self.author = "Siegfried Eisinger"
        self.description = "Defines variaous variable types and shapes as input/output pairs, for testing purposes."

        # Parameters

        # Inputs
        self.bool_in: bool = True
        self.str_in: str = "Hello World"
        self.float32_in: np.float32 = 3.2
        self.float64_in: np.float64 = 6.4
        self.int8_in: np.int8 = -8
        self.uint8_in: np.uint8 = 8
        self.int16_in: np.int16 = -16
        self.uint16_in: np.uint16 = 16
        self.int32_in: np.int32 = -32
        self.uint32_in: np.uint32 = 32
        self.int64_in: np.int64 = -64
        self.uint64_in: np.uint64 = 64
        self.enumeration_in: np_int32 = 99
        self.arr_float64_in: npt.NDArray[np.float64] = np.array( (0,1,2,3,4,5,6,7,8,9), np.float64)
        self.arr_int32_in: npt.NDArray[np.int32] = np.array( (0,1,2,3,4,5,6,7,8,9), np.int32)
        # self.clock_in: bool
        
        # Outputs
        self.bool_out: bool
        self.str_out: str
        self.float32_out: np.float32
        self.float64_out: np.float64
        self.int8_out: np.int8
        self.uint8_out: np.uint8
        self.int16_out: np.int16
        self.uint16_out: np.uint16
        self.int32_out: np.int32
        self.uint32_out: np.uint32
        self.int64_out: np.int64
        self.uint64_out: np.uint64
        self.enumeration_out: int
        self.arr_float64_out: npt.NDArray[np.float64]
        self.arr_int32_out: npt.NDArray[np.int32]
        # self.clock_out: bool

        self.update_out()

        # Internal states
        self.time = 0.0

        # Register variables
        self.register_variable(Float64("time", causality=Fmi3Causality.independent))

        _discrete = Fmi3Variability.discrete
        _continuous = Fmi3Variability.continuous
        _input = Fmi3Causality.input
        _output = Fmi3Causality.output
        self.register_variable(Boolean("bool_in", variability=_discrete, causality=_input, start=True))
        self.register_variable(String("str_in", variability=_discrete, causality=_input, start="Hello World"))
        self.register_variable(Float64("float64_in", variability=_continuous, causality=_input, start="6.4"))
        self.register_variable(Float32("float32_in", variability=_continuous, causality=_input, start="3.2"))
        self.register_variable(Int64("int64_in", variability=_discrete, causality=_input, start="-64"))
        self.register_variable(Int32("int32_in", variability=_discrete, causality=_input, start="-32"))
        self.register_variable(Int16("int16_in", variability=_discrete, causality=_input, start="-16"))
        self.register_variable(Int8("int8_in", variability=_discrete, causality=_input, start="-8"))
        self.register_variable(UInt64("uint64_in", variability=_discrete, causality=_input, start="64"))
        self.register_variable(UInt32("uint32_in", variability=_discrete, causality=_input, start="32"))
        self.register_variable(UInt16("uint16_in", variability=_discrete, causality=_input, start="16"))
        self.register_variable(UInt8("uint8_in", variability=_discrete, causality=_input, start="8"))
        #??self.register_variable(Enumeration("enumeration_in", variability=_discrete, causality=_input, start="99"))
        self.register_variable(Float64("arr_float64_in", variability=_continuous, causality=_input,
                                       dimensions=[Dimension(start=10)], start="0 1 2 3 4 5 6 7 8 9"))
        self.register_variable(Int32("arr_int32_in", variability=_discrete, causality=_input,
                                     dimensions=[Dimension(start=5), Dimension(start=2)], start="0 1 2 3 4 5 6 7 8 9"))

        #self.register_variable(Boolean("bool_out", variability=_discrete, causality=_input))#, start=True))
        self.register_variable(String("str_out", variability=_discrete, causality=_input, start="Hello World"))
        self.register_variable(Float64("float64_out", variability=_continuous, causality=_input, start="6.4"))
        self.register_variable(Float32("float32_out", variability=_continuous, causality=_input, start="3.2"))
        self.register_variable(Int64("int64_out", variability=_discrete, causality=_input, start="-64"))
        self.register_variable(Int32("int32_out", variability=_discrete, causality=_input, start="-32"))
        self.register_variable(Int16("int16_out", variability=_discrete, causality=_input, start="-16"))
        self.register_variable(Int8("int8_out", variability=_discrete, causality=_input, start="-8"))
        self.register_variable(UInt64("uint64_out", variability=_discrete, causality=_input, start="64"))
        self.register_variable(UInt32("uint32_out", variability=_discrete, causality=_input, start="32"))
        self.register_variable(UInt16("uint16_out", variability=_discrete, causality=_input, start="16"))
        self.register_variable(UInt8("uint8_out", variability=_discrete, causality=_input, start="8"))
        self.register_variable(Float64("arr_float64_out", variability=_continuous, causality=_output,
                                       dimensions=[Dimension(start=10)]))
        self.register_variable(Int32("arr_int32_out", variability=_discrete, causality=_output,
                                     dimensions=[Dimension(start=5), Dimension(start=2)]))


    def update_out(self):
        self.bool_out = self.bool_in
        self.str_out = self.str_in
        self.float32_out = self.float32_in
        self.float64_out = self.float64_in
        self.int8_out = self.int8_in
        self.uint8_out = self.uint8_in
        self.int16_out = self.int16_in
        self.uint16_out = self.uint16_in
        self.int32_out = self.int32_in
        self.uint32_out = self.uint32_in
        self.int64_out = self.int64_in
        self.uint64_out = self.uint64_in
        self.enumeration_out = self.enumeration_in
        self.arr_float64_out = self.arr_float64_in
        self.arr_int32_out = self.arr_int32_in

        # self.clock_out = self.clock_in        

    def do_step(self,
                current_communication_point:float,
                communication_step_size:float,
                no_set_fmu_state_prior_to_current_point:bool):
        self.time = current_communication_point + communication_step_size
        self.update_out()
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
        self.update_out()
        return Fmi3UpdateDiscreteStatesResult()

if __name__ == "__main__":
    from pathlib import Path
    from pythonfmu3.builder import FmuBuilder
    from fmpy import read_model_description

    dest = FmuBuilder( Path(__file__), dest = Path(__file__).parent.resolve()).build()
    read_model_description(dest, True, True, True)
    print(f"Generated {dest}. Validated modelDescription.")