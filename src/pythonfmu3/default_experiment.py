class DefaultExperiment:
    def __init__(
        self,
        start_time: float = None,
        stop_time: float = None,
        communication_step_size: float = None,
        tolerance: float = None,
    ):
        self.start_time = start_time
        self.stop_time = stop_time
        self.communication_step_size = communication_step_size
        self.tolerance = tolerance
