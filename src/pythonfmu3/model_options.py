"""Contains modelOptions for both CoSimulation and ModelExchange, defined as dataclass.
These are included in several modules and should therefore be defined separately
"""

from dataclasses import dataclass, fields


# Note: all Bool options are false by default and the name expresses the option as True.
#      The cli uses therefore the original name to add the option as implicit True (non-default)
#      other options are added with their (non-default) numbers
@dataclass(kw_only=True, frozen=True, slots=True)
class Fmi3ModelOptionsCommon:
    """Model options common for Co-Simulation and Model Exchange."""

    needsExecutionTool: bool = False
    canBeInstantiatedOnlyOncePerProcess: bool = False
    canGetAndSetFMUState: bool = False
    canSerializeFMUState: bool = False
    providesDirectionalDerivatives: bool = False
    providesAdjointDerivatives: bool = False
    providesPerElementDependencies: bool = False
    providesEvaluateDiscreteStates: bool = False

    def to_dict(self, *, w_default: bool = True, w_none: bool = True):
        """A special version of 'asdict', which also allows for choice what to include.
        Note: self.do_dict() == asdict(self) if the default value is None.

        Args:
            w_defaults: include also the elements with default value
            w_none: include also elements with a 'None' value
        """
        dct: dict[str, bool | int | float] = {}
        for _f in fields(self):
            value = getattr(self, _f.name)
            if (
                (value is not None and value != _f.default)
                or (value is not None and value == _f.default and w_default)
                or (value is None and value == _f.default and w_default and w_none)
                or (value is None and value != _f.default and w_none)
            ):
                dct.update({_f.name: value})
        return dct

    def __getitem__(self, key:str):
        """Get one of the dataclass elements through a str key."""
        if not hasattr(self, key):
            raise KeyError(f"dataclass {self} has no element {key}") from None
        return getattr(self,key)

@dataclass(kw_only=True, frozen=True, slots=True)
class Fmi3ModelOptionsCS(Fmi3ModelOptionsCommon):
    """Model options for Co-Simulation.

    Note: This uses non-standard Python names, because they are transferred to the ModelDescription
          If users prefer, the options can be instantiated with a dict: Fmi3ModelOptionsCS(**{...})
          and can be used with the __getitem__ method - both as str.
    """

    canHandleVariableCommunicationStepSize: bool = False
    fixedInternalStepSize: float | None = None
    maxOutputDerivativeOrder: int = 0  # uInt
    recommendedIntermediateInputSmoothness: int = 0
    providesIntermediateUpdate: bool = False
    mightReturnEarlyFromDoStep: bool = False
    canReturnEarlyAfterIntermediateUpdate: bool = False
    hasEventMode: bool = False


@dataclass(kw_only=True, frozen=True, slots=True)
class Fmi3ModelOptionsME(Fmi3ModelOptionsCommon):
    """Model options for Model Exchange."""

    needsCompletedIntegratorStep: bool = False
