from pythonfmu3.fmi3slave import Float64, Fmi3Causality, Fmi3Slave, Fmi3Variability

try:
    from sympy import exp, symbols
except ImportError:  # Trick to be able to generate the FMU without sympy installed
    symbols, exp = None, None


class SympySlave(Fmi3Slave):
    """This class is an example to demonstrate installing new Python dependencies.

    The code is not efficient.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.realIn = 22.0
        self.realOut = 0.0
        self.tau = 2.0
        self.a = 5.0
        self.register_variable(Float64("realIn", causality=Fmi3Causality.input))
        self.register_variable(
            Float64(
                "a",
                causality=Fmi3Causality.parameter,
                variability=Fmi3Variability.tunable,
            )
        )
        self.register_variable(
            Float64(
                "tau",
                causality=Fmi3Causality.parameter,
                variability=Fmi3Variability.tunable,
            )
        )
        self.register_variable(Float64("realOut", causality=Fmi3Causality.output))

    def do_step(self, current_time, step_size):
        i, a, t, tau = symbols("i, a, t, tau")
        expr = i * a * (1 - exp(-1 * t / tau))
        self.realOut = expr.evalf(
            subs={i: self.realIn, a: self.a, t: current_time + step_size, tau: self.tau}
        )
        return True
