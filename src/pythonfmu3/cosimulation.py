from abc import ABC, abstractmethod
from pythonfmu3.model_returns import Fmi3StepResult

# co-simulation mixin
class CoSimulation(ABC):
    @abstractmethod
    def do_step(self,
                current_time: float,
                step_size: float,
                *,
                no_set_fmu_state_prior_to_current_point:bool = False) -> Fmi3StepResult:
        pass
