import math

from localmodule import get_amplitude, get_time_constant

from pythonfmu3.enums import Fmi3Causality, Fmi3Variability
from pythonfmu3.fmi3slave import Fmi3Slave
from pythonfmu3.model_returns import Fmi3StepResult
from pythonfmu3.variables import Float64


class PythonSlaveWithDep(Fmi3Slave):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.realIn = 22.0
        self.realOut = 0.0
        self.time = 0

        self.register_variable(
            Float64(
                "time",
                causality=Fmi3Causality.independent,
                variability=Fmi3Variability.continuous,
            )
        )
        self.register_variable(Float64("realIn", causality=Fmi3Causality.input))
        self.register_variable(Float64("realOut", causality=Fmi3Causality.output))

    def do_step(self,
                currentCommunicationPoint: float,
                communicationStepSize: float,
                noSetFMUStatePriorToCurrentPoint: bool):
        self.realOut = self.realIn * get_amplitude() * math.exp((currentCommunicationPoint + communicationStepSize) / get_time_constant())
        return Fmi3StepResult()
