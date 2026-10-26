from pythonfmu3 import Fmi3Causality, Fmi3Slave, Float64

class PIDController(Fmi3Slave):
    """PID Controller implementation"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.author = "PythonFMU3 Team"
        self.description = "PID Controller"

        # Inputs
        self.setpoint = 0.0
        self.measurement = 0.0

        # Outputs
        self.output = 0.0

        # Parameters
        self.kp = 1.0  # Proportional gain
        self.ki = 0.1  # Integral gain
        self.kd = 0.01 # Derivative gain

        # Internal states
        self.integral_error = 0.0
        self.previous_error = 0.0
        self.first_step = True

        # Register variables
        self.register_variable(Float64("time", causality=Fmi3Causality.independent))
        self.register_variable(Float64("setpoint", causality=Fmi3Causality.input, start=0.0))
        self.register_variable(Float64("measurement", causality=Fmi3Causality.input, start=0.0))
        self.register_variable(Float64("output", causality=Fmi3Causality.output))
        self.register_variable(Float64("kp", causality=Fmi3Causality.parameter, start=1.0))
        self.register_variable(Float64("ki", causality=Fmi3Causality.parameter, start=0.1))
        self.register_variable(Float64("kd", causality=Fmi3Causality.parameter, start=0.01))

    def do_step(self, current_time, step_size):
        # Calculate error
        error = self.setpoint - self.measurement

        # Proportional term
        p_term = self.kp * error

        # Integral term
        self.integral_error += error * step_size
        i_term = self.ki * self.integral_error

        # Derivative term
        if self.first_step:
            d_term = 0.0
            self.first_step = False
        else:
            d_term = self.kd * (error - self.previous_error) / step_size

        # PID output
        self.output = p_term + i_term + d_term

        # Store error for next iteration
        self.previous_error = error

        return True
    
if __name__ == "__main__":
    from pathlib import Path
    from pythonfmu3.builder import FmuBuilder
    from fmpy import read_model_description

    dest = FmuBuilder.build_FMU(
        script_file = Path(__file__),
        dest = Path(__file__).parent.resolve(),
        #project_files: Iterable[FilePath] = set(),
        #documentation_folder: Optional[FilePath] = None,
        #terminals : Optional[FilePath] = None,
    )
    read_model_description(dest, True, True, True)
    print(f"Generated {dest}. Validated modelDescription.")