from pythonfmu3.fmi3slave import Float64, Fmi3Causality, Fmi3Slave, Fmi3Variability


class PythonSlaveWithException(Fmi3Slave):
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

    def do_step(self, current_time, step_size):
        raise RuntimeError()
