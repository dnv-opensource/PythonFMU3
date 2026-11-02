"""Define the abstract facade class."""

import ctypes
import datetime as dt
from functools import partialmethod
import importlib.metadata
import json
from typing import TypeVar, TYPE_CHECKING, Any, ClassVar
from uuid import uuid1
from xml.etree.ElementTree import Element, SubElement

import numpy as np

from pythonfmu3.cosimulation import CoSimulation
from pythonfmu3.enums import Fmi3Causality, Fmi3Initial, Fmi3Status, Fmi3Variability
from pythonfmu3.logmsg import LogMsg
from pythonfmu3.model_options import Fmi3ModelOptionsCS, Fmi3ModelOptionsME
from pythonfmu3.modelexchange import ModelExchange
from pythonfmu3.model_returns import Fmi3StepResult, Fmi3UpdateDiscreteStatesResult
from pythonfmu3.model_returns import StepResult, UpdateDiscreteStatesResult
from pythonfmu3.unit import Unit
from pythonfmu3.variable_types import VariableType
from pythonfmu3.variables import (
    Boolean,
    Enumeration,
    Float32,
    Float64,
    Int8,
    Int16,
    Int32,
    Int64,
    ModelVariable,
    String,
    UInt8,
    UInt16,
    UInt32,
    UInt64,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pythonfmu3.default_experiment import DefaultExperiment
    from pythonfmu3.variables import FmiScalar

TUInt = TypeVar("TUInt")

class Fmi3SlaveBase:
    """Abstract facade class to execute Python through FMI standard.

    Note that argument names use non-python style camelCase, as defined and expected in FMI standard.
    Args:
        instanceName: the name of the instantiated component model (FMU)
        resources: optional relative path to additional resources
        logger: logger callable
        visible: determine whether visible features in simulation shall be active or not
        eventModeUsed: Orchestrator can tell the FMU whether event mode is used
        earlyReturnAllowed: Orchestrator can tell the FMU whether early return from step is allowed
        model_options_cs: non-default settings of Co-Simulation model options. Transferred to modelDescription
        model_options_me: non-default settings of Co-Simulation model options. Transferred to modelDescription
    """

    def __init__(self,
                 instanceName : str,
                 *,
                 resources : str|None = None,
                 logger =None, #: Callable|None = None,
                 visible : bool = False,
                 eventModeUsed : bool = False,
                 earlyReturnAllowed : bool = False,
                 model_options_cs : Fmi3ModelOptionsCS | None = None,
                 model_options_me : Fmi3ModelOptionsME | None = None,
                 # required_intermediate_variables : list[int]|None = None,
                 # n_required_intermediate_variables : int = 0,
                 # instance_environment : Callable|None = None,
                 # logger_msg : Callable|None = None,
                 # intermediate_update : Callable|None = None,
                 ) -> None:
        print("INSTANTIATING...", instanceName)
        self.model_options_cs = model_options_cs or Fmi3ModelOptionsCS()
        self.model_options_me = model_options_me or Fmi3ModelOptionsME()
        self.vars : dict[int,ModelVariable] = {}
        self.event_indicators: list[int] = []
        self.instance_name = instanceName
        self.resources = resources
        self.visible = visible
        #self.logger = logger
        self.event_mode_used = eventModeUsed
        self.early_return_allowed = earlyReturnAllowed
        #self.model_options_cs = model_options_cs or Fmi3ModelOptionsCS()
        #self.model_options_me = model_options_me or Fmi3ModelOptionsME()
        self.log_queue : list[LogMsg] = []

        self.guid = uuid1()
        self.author: str | None = None
        self.license: str | None = None
        self.version: str | None = None
        self.copyright: str | None = None
        self.modelName: str | None = self.__class__.__name__
        self.description: str | None = None
        self.default_experiment: DefaultExperiment | None = None

        self.type_definitions: dict[str, VariableType] = {}
        self.units: dict[str, Unit] = {}

    log_categories: ClassVar[dict[str, str]] = {
        "logStatusWarning": "Log messages with fmi3Warning status.",
        "logStatusDiscard": "Log messages with fmi3Discard status.",
        "logStatusError": "Log messages with fmi3Error status.",
        "logStatusFatal": "Log messages with fmi3Fatal status.",
        "logAll": "Log all messages.",
    }

    def to_xml(self, model_options: dict[str, str] | None = None) -> Element: # noqa: PLR0915, PLR0912, C901
        """Build the XML representation of the model.

        Args:
            model_options: FMU model options

        Returns
        -------
            xml Element description of the FMU
        """
        t = dt.datetime.now(dt.UTC)
        date_str = t.isoformat(timespec="seconds")
        assert self.modelName is not None, "Need a modelName at this stage."

        attrib : dict[str, str] = {
            'fmiVersion' : "3.0",
            'modelName' : self.modelName,
            'instantiationToken' : f"{self.guid!s}",
            'generationTool' : f"PythonFMU3 {importlib.metadata.version('PythonFMU3')}",
            'generationDateAndTime' : date_str,
            'variableNamingConvention' : "structured",
        }
        if self.description is not None:
            attrib["description"] = self.description
        if self.author is not None:
            attrib["author"] = self.author
        if self.license is not None:
            attrib["license"] = self.license
        if self.version is not None:
            attrib["version"] = self.version
        if self.copyright is not None:
            attrib["copyright"] = self.copyright

        root = Element("fmiModelDescription", attrib=attrib)

        options_cs = {"modelIdentifier": self.modelName}
        model_options_cs = Fmi3ModelOptionsCS().to_dict() if model_options is None else model_options
        for name, default in Fmi3ModelOptionsCS().to_dict().items():
            if name in model_options_cs:
                value = model_options_cs.get(name, default)
                if value is not None:
                    options_cs[name] = str(value).lower()

        options_me = {"modelIdentifier": self.modelName}
        model_options_me = Fmi3ModelOptionsME().to_dict() if model_options is None else model_options
        for name, default in Fmi3ModelOptionsME().to_dict().items():
            if name in model_options_me:
                value = model_options_me.get(name, default)
                if value is not None:
                    options_me[name] = str(value).lower()

        # check if we have cosim mixin or model exchange mixin
        if isinstance(self, ModelExchange):
            SubElement(root, "ModelExchange", attrib=options_me)

        if isinstance(self, CoSimulation):
            SubElement(root, "CoSimulation", attrib=options_cs)

        if self.units:
            unit_defs = SubElement(root, "UnitDefinitions")
            for unit in self.units.values():
                unit_defs.append(unit.to_xml())

        if self.type_definitions:
            type_defs = SubElement(root, "TypeDefinitions")
            for val in self.type_definitions.values():
                type_defs.append(val.to_xml())

        if len(Fmi3SlaveBase.log_categories) > 0:
            categories = SubElement(root, "LogCategories")
            for category, description in self.log_categories.items():
                categories.append(
                    Element(
                        "Category",
                        attrib={"name": category, "description": description},
                    )
                )

        if self.default_experiment is not None:
            if self.default_experiment.start_time is not None:
                attrib["startTime"] = str(self.default_experiment.start_time)
            if self.default_experiment.stop_time is not None:
                attrib["stopTime"] = str(self.default_experiment.stop_time)
            if self.default_experiment.communicationStepSize is not None:
                attrib["stepSize"] = str(self.default_experiment.communicationStepSize)
            if self.default_experiment.tolerance is not None:
                attrib["tolerance"] = str(self.default_experiment.tolerance)
            SubElement(root, "DefaultExperiment", attrib)

        variables = SubElement(root, "ModelVariables")
        for mv in self.vars.values():
            if mv.requires_start():
                self.__apply_start_value(mv)
            variables.append(mv.to_xml())

        structure = SubElement(root, "ModelStructure")
        outputs = list(filter(lambda v: v.causality == Fmi3Causality.output, self.vars.values()))

        continuous_state_derivatives = list(
            filter(
                lambda v: (
                    v.variability == Fmi3Variability.continuous
                    and (isinstance(v, Float64) and v.derivative is not None)
                ),
                self.vars.values(),
            )
        )

        allowed_variability = [None, Fmi3Initial.approx, Fmi3Initial.calculated]
        initial_unknown = list(
            filter(
                lambda v: (
                    (v.causality == Fmi3Causality.output and (v.initial in allowed_variability))
                    or v.causality == Fmi3Causality.calculatedParameter
                    or (v in continuous_state_derivatives
                    and v.initial in allowed_variability)
                ),
                self.vars.values(),
            )
        )

        for v in outputs:
            SubElement(structure, "Output", attrib = {'valueReference' : str(v.value_reference)})

        for v in continuous_state_derivatives:
            SubElement(structure, "ContinuousStateDerivative", attrib={'valueReference' : str(v.value_reference)})

        for v in initial_unknown:
            SubElement(structure, "InitialUnknown", attrib={'valueReference' : str(v.value_reference)})

        for v in self.event_indicators:
            SubElement(structure, "EventIndicator", attrib={'valueReference' : str(v)})

        return root

    def __apply_start_value(self, mv: ModelVariable) -> None:
        vrs = [mv.value_reference]
        refs : FmiScalar | list[FmiScalar]
        if isinstance(mv, Int32):
            refs = self.get_int32(vrs)
        elif isinstance(mv, (Enumeration, Int64)):
            refs = self.get_int64(vrs)
        elif isinstance(mv, UInt64):
            refs = [val.value for val in self.get_uint64(vrs)]
        elif isinstance(mv, Float64):
            refs = self.get_float64(vrs)
        elif isinstance(mv, Boolean):
            refs = self.get_boolean(vrs)
        elif isinstance(mv, String):
            refs = self.get_string(vrs)
        else:
            raise KeyError(f"Unsupported type {type(mv)}!")
        mv.start = refs if len(getattr(mv, "dimensions", [])) else refs[0]

    def register_variable(
        self,
        var: ModelVariable,
        *,
        nested: bool = True,
        var_type : VariableType | None = None,
        has_event_indicator: bool = False,
    ) -> None:
        """Register a variable as FMU interface.

        Args:
            var: The variable to be registered
            nested: Optional, does the "." in the variable name reflect an object hierarchy to access it? Default True
            var_type:
            has_event_indicator:
        """
        variable_reference = len(self.vars)
        self.vars[variable_reference] = var
        # Set the unique value reference
        var.value_reference = variable_reference
        owner = self
        if var.getter is None and nested and "." in var.name:
            split = var.name.split(".")
            split.pop(-1)
            for s in split:
                owner = getattr(owner, s)
        if var.getter is None:
            if hasattr(var, "dimensions") and len(var.dimensions) > 0:
                var.getter = lambda: getattr(owner, var.local_name).flatten().tolist()
            else:
                var.getter = lambda: getattr(owner, var.local_name)
        if var.setter is None and hasattr(owner, var.local_name) and var.variability != Fmi3Variability.constant:
            if hasattr(var, "dimensions") and len(var.dimensions) > 0:
                var.setter = lambda v: setattr(
                    owner,
                    var.local_name,
                    np.reshape(v, shape=getattr(owner, var.local_name).shape),
                )
            else:
                var.setter = lambda v: setattr(owner, var.local_name, v)

        if var_type is not None:
            self.type_definitions[var_type.name] = var_type
            var.declared_type = var_type.name

        if has_event_indicator:
            self.register_event_indicator(var.value_reference)

    def register_event_indicator(self, vr:int) -> None:
        self.event_indicators.append(vr)

    def setup_experiment(self, start_time: float) -> None:
        self.log(f"setup_experiment({start_time}) not defined within FMI3. Use enter_initialization_mode()")

    def register_units(self, units: list[Unit]) -> None:
        for unit in units:
            self.units[unit.name] = unit

    def enterInitializationMode(self,
                                toleranceDefined:bool,
                                tolerance:float,
                                startTime:float,
                                stopTimeDefined:bool,
                                stopTime:float):
        """Translate the FMI3 call to the python-adapted call."""
        return self.enter_initialization_mode(
            tolerance = tolerance if toleranceDefined else None,
            start_time = startTime,
            stop_time = stopTime if stopTimeDefined else None
            )
    
    def enter_initialization_mode(
        self, tolerance: float | None = None, start_time: float = 0.0, stop_time: float | None = None
    ) -> None:
        """Run initialization mode in Python-adapted style."""
        assert not all(x is None for x in (tolerance, stop_time)), "One out of tolerance and stop_time shall be defined" 

    def exit_initialization_mode(self) -> None:
        pass

    def doStep(self,
               currentCommunicationPoint: float,
               communicationStepSize: float,
               noSetFMUStatePriorToCurrentPoint: bool
               ) -> Fmi3StepResult:
        """Translate the FMI3 call to the python-adapted call."""
        return self.do_step(currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint)
    
    def do_step(self,
                current_communication_point: float,
                communication_step_size: float,
                no_set_fmu_state_prior_to_current_point: bool = False,
    ) -> Fmi3StepResult:
        """Run doStep in Python-adapted style."""
        return Fmi3StepResult(False, False, False, current_communication_point+communication_step_size)

    
    def update_discrete_states(self) -> Fmi3UpdateDiscreteStatesResult:
        return Fmi3UpdateDiscreteStatesResult() # default. Should be overridden.

    def terminate(self) -> None:
        pass

    def get_int32(self, vrs: list[int]) -> list[int]:
        refs : list[int] = []
        for vr in vrs:
            var = self.vars[vr]
            if isinstance(var, (Int32,Int8,Int16,Int64)):
                if len(var.dimensions) == 0:
                    refs.append(int(var.getter()))
                else:
                    refs.extend(map(int, var.getter()))
            else:
                raise TypeError(f"Variable with valueReference={vr} is not of type Int32!")
        return refs
    
    def get_int8(self, vrs: list[int]) -> list[int]:
        return self.get_int32( vrs)

    def get_int16(self, vrs: list[int]) -> list[int]:
        return self.get_int32( vrs)

    def get_int64(self, vrs: list[int]) -> list[int]:
        return self.get_int32( vrs)

#     def get_uint64(self, vrs: list[int]) -> list[ctypes.c_uint64]:
#         refs : list[ctypes.c_uint64] = []
#         for vr in vrs:
#             var = self.vars[vr]
#             if isinstance(var, (UInt64,UInt32,UInt16,UInt8)):
#                 if len(var.dimensions) == 0:
#                     val = var.getter()
#                     refs.append(ctypes.c_uint64(val) if not isinstance(val, ctypes.c_uint64) else val)
#                 else:
#                     refs.extend(map(ctypes.c_uint64, var.getter()))
#             else:
#                 raise TypeError(f"Variable with valueReference={vr} is not of type Uint64!")
#         return refs
#

    def get_uint(self, vrs: list[int], fmi_type:TUInt, c_type:TUInt=ctypes.c_uint64) -> list[TUInt]:
        refs : list[T] = []
        for vr in vrs:
            var = self.vars[vr]
            if isinstance(var, fmi_type):
                if len(var.dimensions) == 0:
                    val = var.getter()
                    refs.append(c_type(val) if not isinstance(val, c_type) else val)
                else:
                    refs.extend(map(c_type, var.getter()))
            else:
                raise TypeError(f"Variable with valueReference={vr} is not of type {fmi_type}, but {var._type}!")
        return refs
    
    def get_uint8(self, vrs: list[int]) -> list[ctypes.c_uint8]:
        return self.get_uint( vrs, fmi_type=UInt8, c_type=ctypes.c_uint8) 
                   
    def get_uint16(self, vrs: list[int]) -> list[ctypes.c_uint16]:
        return self.get_uint( vrs, fmi_type=UInt16, c_type=ctypes.c_uint16) 

    def get_uint32(self, vrs: list[int]) -> list[ctypes.c_uint32]:
        return self.get_uint( vrs, fmi_type=UInt32, c_type=ctypes.c_uint32) 

    def get_uint64(self, vrs: list[int]) -> list[ctypes.c_uint64]:
        return self.get_uint( vrs, fmi_type=UInt64, c_type=ctypes.c_uint64) 

    def get_float64(self, vrs: list[int]) -> list[float]:
        refs : list[float] = []
        for vr in vrs:
            var = self.vars[vr]
            if isinstance(var, (Float64, Float32)):
                if len(var.dimensions) == 0:
                    refs.append(float(var.getter()))
                else:
                    refs.extend(var.getter())
            else:
                raise TypeError(f"Variable with valueReference={vr} is not of type Float64!")
        return refs
    
    def get_float32(self, vrs: list[int]) -> list[float]:
        return self.get_float64( vrs)

    def get_boolean(self, vrs: list[int]) -> list[bool]:
        refs : list[bool] = []
        for vr in vrs:
            var = self.vars[vr]
            if isinstance(var, Boolean):
                if len(var.dimensions) == 0:
                    refs.append(bool(var.getter()))
                else:
                    refs.extend(var.getter())

            else:
                raise TypeError(f"Variable with valueReference={vr} is not of type Boolean!")
        return refs

    def get_string(self, vrs: list[int]) -> list[str]:
        refs : list[str] = []
        for vr in vrs:
            var = self.vars[vr]
            if isinstance(var, String):
                refs.append(str(var.getter()))
            else:
                raise TypeError(f"Variable with valueReference={vr} is not of type String!")
        return refs

    def set_int32(self, vrs: list[int], values: list[int]) -> None:
        offset = 0
        for vr in vrs:
            var = self.vars[vr]
            if isinstance(var, Int32):
                size = var.size(self.vars)
                if size > 1:
                    var.setter(values[offset : offset + size])
                else:
                    var.setter(values[offset])
                offset += size
            else:
                raise TypeError(f"Variable with valueReference={vr} is not of type Int32!")

    def set_int64(self, vrs: list[int], values: list[int]) -> None:
        offset = 0
        for vr in vrs:
            var = self.vars[vr]
            if isinstance(var, (Enumeration, Int64)):
                size = var.size(self.vars)
                if size > 1:
                    var.setter(values[offset : offset + size])
                else:
                    var.setter(values[offset])
                offset += size
            else:
                raise TypeError(f"Variable with valueReference={vr} is not of type Int64!")

    def set_uint64(self, vrs: list[int], values: list[int]) -> None:
        offset = 0
        for vr in vrs:
            var = self.vars[vr]
            if isinstance(var, UInt64):
                size = var.size(self.vars)
                if size > 1:
                    var.setter(values[offset : offset + size])
                else:
                    var.setter(values[offset])
                offset += size
            else:
                raise TypeError(f"Variable with valueReference={vr} is not of type UInt64!")

    def set_float64(self, vrs: list[int], values: list[float]) -> None:
        offset = 0
        for vr in vrs:
            var = self.vars[vr]
            if isinstance(var, Float64):
                size = var.size(self.vars)
                if size > 1:
                    var.setter(values[offset : offset + size])
                else:
                    var.setter(values[offset])
                offset += size
            else:
                raise TypeError(f"Variable with valueReference={vr} is not of type Float64!")

    def set_boolean(self, vrs: list[int], values: list[bool]) -> None:
        offset = 0
        for vr in vrs:
            var = self.vars[vr]
            if isinstance(var, Boolean):
                size = var.size(self.vars)
                if size > 1:
                    var.setter(values[offset : offset + size])
                else:
                    var.setter(values[offset])
                offset += size
            else:
                raise TypeError(f"Variable with valueReference={vr} is not of type Boolean!")

    def set_string(self, vrs: list[int], values: list[str]) -> None:
        for vr, value in zip(vrs, values, strict=True):
            var = self.vars[vr]
            if isinstance(var, String):
                var.setter(value)
            else:
                raise TypeError(f"Variable with valueReference={vr} is not of type String!")

    def _get_fmu_state(self) -> dict[str, Any]:
        return {var.name : var.getter() for var in self.vars.values()}

    def _set_fmu_state(self, state: dict[str, Any]) -> None:
        vars_by_name = {v.name : v for v in self.vars.values()}
        for name, value in state.items():
            if name not in vars_by_name:
                setattr(self, name, value)
            else:
                v = vars_by_name[name]
                if v.setter is not None:
                    v.setter(value)

    def get_number_of_event_indicators(self) -> int:
        return len(self.event_indicators)

    def set_continuous_states(self, values: list[float]) -> None:
        offset = 0
        continuous_state_derivatives = list(
            filter(
                lambda v: (
                    v.variability == Fmi3Variability.continuous
                    and (isinstance(v, Float64) and v.derivative is not None)
                ),
                self.vars.values(),
            )
        )

        vrs = [v.derivative for v in continuous_state_derivatives]

        for vr in vrs:
            var = self.vars[vr]
            size = var.size(self.vars)
            if size > 1:
                var.setter(values[offset : offset + size])
            else:
                var.setter(values[offset])
            offset += size

    def get_continuous_states(self) -> list[float]:
        continuous_state_derivatives = list(
            filter(
                lambda v: (
                    v.variability == Fmi3Variability.continuous
                    and (isinstance(v, Float64) and v.derivative is not None)
                ),
                self.vars.values(),
            )
        )

        vrs = [v.derivative for v in continuous_state_derivatives]

        refs : list[Any] = []
        for vr in vrs:
            var = self.vars[vr]
            if len(var.dimensions) == 0:
                refs.append(float(var.getter()))
            else:
                refs.extend(var.getter())

        return refs

    def get_number_of_continuous_states(self) -> int:
        continuous_state_derivatives = list(
            filter(
                lambda v: (
                    v.variability == Fmi3Variability.continuous
                    and (isinstance(v, Float64) and v.derivative is not None)
                ),
                self.vars.values(),
            )
        )
        return len(continuous_state_derivatives)

    def set_time(self, time: float)->None:
        self.time = time

    @staticmethod
    def _fmu_state_to_bytes(state: dict[str, Any]) -> bytes:
        return json.dumps(state).encode("utf-8")

    @staticmethod
    def _fmu_state_from_bytes(state: bytes) -> dict[str, Any]:
        return json.loads(state.decode("utf-8"))

    def _get_log_queue(self) -> list[LogMsg]:
        return self.log_queue

    def log(
        self,
        msg: str,
        status: Fmi3Status = Fmi3Status.ok,
        category: str | None = None,
        *,
        debug: bool = False,
    )->None:
        """Log a message to the FMU logger.

        Args:
            msg (str) : Log message
            status (Fmi3Status) : Optional, message status (default ok)
            category (str or None) : Optional, message category (default derived from status)
            debug (bool) : Optional, is this a debug message (default False)
        """
        if category is None:
            category = f"logStatus{status.name.capitalize()}"
            if category not in Fmi3SlaveBase.log_categories:
                category = "logAll"
        log_msg = LogMsg(status, category, msg, debug)
        self.log_queue.append(log_msg)


class Fmi3Slave(Fmi3SlaveBase, CoSimulation):
    pass
