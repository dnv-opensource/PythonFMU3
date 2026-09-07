from abc import ABC, abstractmethod
from pythonfmu3.model_returns import Fmi3StepResult

# co-simulation mixin
class CoSimulation(ABC):
    @abstractmethod
    def do_step(self,
                current_time: float,
                step_size: float,
                *,
                noSetFmuStatePriorToCurrentPoint:bool = False) -> Fmi3StepResult:
        pass
