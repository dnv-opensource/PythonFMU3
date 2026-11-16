from pythonfmu3.fmi3slave import Fmi3Slave
from pythonfmu3.default_experiment import DefaultExperiment
from pythonfmu3.enums import Fmi3Causality, Fmi3Variability
from pythonfmu3.model_returns import Fmi3StepResult
from pythonfmu3.variables import Float64, String

class PythonSlaveReadFile(Fmi3Slave):
    default_experiment = DefaultExperiment(start_time=0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with open(f"{self.resources}/hello.txt") as file:
            data = file.read()

        self.time = 0

        self.register_variable(
            Float64(
                "time",
                causality=Fmi3Causality.independent,
                variability=Fmi3Variability.continuous,
            )
        )
        self.register_variable(
            String(
                "file_content",
                getter=lambda: data,
                causality=Fmi3Causality.output,
                variability=Fmi3Variability.constant,
            )
        )

    def do_step(self,
                currentCommunicationPoint: float,
                communicationStepSize: float,
                noSetFMUStatePriorToCurrentPoint: bool):
        return Fmi3StepResult()
