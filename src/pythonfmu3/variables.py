"""Classes describing interface variables."""

from __future__ import annotations
import importlib
from abc import ABC
from collections import ChainMap
from collections.abc import Iterable
from enum import Enum
from functools import reduce
import numpy as np
from typing import Any, TypeAlias
import sys
from xml.etree.ElementTree import Element

from .enums import Fmi3Causality, Fmi3Initial, Fmi3IntervalVariability, Fmi3Variability

FMIScalar : TypeAlias = np.generic | bool | int | float | str

MAX_LENGTH = 1000


def flatten(lst):
    for item in lst:
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            yield from flatten(item)
        else:
            yield item


def check_numpy():
    try:
        importlib.import_module("numpy")
    except ModuleNotFoundError:
        raise ModuleNotFoundError("Numpy is not installed, it is required for Array support")

py_types: dict[str, type] = {
    "Real": float,
    "Integer": int,
    "Boolean": bool,
    "String": str,
    "Float32": np.float32,
    "Float64": np.float64,
    "Int8": np.int8,
    "UInt8": np.uint8,
    "Int16": np.int16,
    "Uint16": np.uint16,
    "Int32": np.int32,
    "UInt32": np.uint32,
    "Int64": np.int64,
    "UInt64": np.uint64,
    "Enumeration": int,
    "Clock": bool,
}

def fmi_type_version( fmi_type_name:str, fmi_version:int=3) -> bool:
    """Check whether the FMI type is valid in the given FMI version."""
    if fmi_type_name not in py_types:
        return False
    if fmi_version < 3 and fmi_type_name in ("Real", "Integer", "Boolean", "String", "Enumeration"):
        return True
    if  fmi_version == 3 and fmi_type_name not in ("Real", "Integer"):
        return True
    return False


def fmi_type( fmi_type_name:str):
    """Get the fmi type object from the fmi type str."""
    return getattr( sys.modules[__name__], fmi_type_name)

class ModelVariable(ABC):
    """Abstract FMI model variable definition.

    Args:
        name (str): Variable name
        causality (:obj:`Fmi3Causality`, optional): Variable causality
        description (str, optional): Variable description
        initial (:obj:`Fmi3Initial`, optional): Variable initial status
        variability (:obj:`Fmi3Variability`, optional): Variable variability
        declared_type: optional reference to a previously declared type (see VariableType)
        getter: optional explicit definition of a getter function
        setter: optional explicit definition of a setter function
        canHandleMultipleSetPerTimeInstant: boolean flag. See FMI spec.
    """

    def __init__(
        self,
        name: str,
        causality: Fmi3Causality | None = None,
        description: str | None = None,
        initial: Fmi3Initial | None = None,
        variability: Fmi3Variability | None = None,
        declared_type: str | None = None,
        getter: Any = None,
        setter: Any = None,
        can_handle_multiple_set_per_time_instant: bool = True,
    ):
        self.getter = getter
        self.setter = setter
        self._type = None
        self.local_name = name.rsplit(".", maxsplit=1)[-1]

        # demanagle names
        self.local_name = self.local_name.lstrip("_")

        self.__attrs = {
            "name": name,
            "valueReference": None,
            "description": description,
            "causality": causality,
            "variability": variability,
            "initial": initial,
            "declaredType": declared_type,
            "canHandleMultipleSetPerTimeInstant": can_handle_multiple_set_per_time_instant,
        }
        self._extras = {}

    @property
    def causality(self) -> Fmi3Causality | None:
        """:obj:`Fmi3Causality` or None: Variable causality - None if not set"""
        return self.__attrs["causality"]

    @property
    def description(self) -> str | None:
        """Str or None: Variable description - None if not set"""
        return self.__attrs["description"]

    @property
    def initial(self) -> Fmi3Initial | None:
        """:obj:`Fmi3Initial` or None: Variable initial status - None if not set"""
        return self.__attrs["initial"]

    @property
    def name(self) -> str:
        """str: Variable name"""
        return self.__attrs["name"]

    @property
    def value_reference(self) -> int:
        """int: Variable reference index"""
        return self.__attrs["valueReference"]

    @value_reference.setter
    def value_reference(self, value: int):
        if self.__attrs["valueReference"] is not None:
            raise RuntimeError("Value reference already set.")
        self.__attrs["valueReference"] = value

    @property
    def declared_type(self) -> str:
        """str: declared type"""
        return self.__attrs["declaredType"]

    @declared_type.setter
    def declared_type(self, value: str):
        if self.__attrs["declaredType"] is not None:
            raise RuntimeError("Declared type already set.")
        self.__attrs["declaredType"] = value

    @property
    def variability(self) -> Fmi3Variability | None:
        """:obj:`Fmi3Variability` or None: Variable variability - None if not set"""
        return self.__attrs["variability"]

    def requires_start(self) -> bool:
        """Test if a variable requires a start attribute

        Returns
        -------
            True if successful, False otherwise
        """
        return (
            self.initial == Fmi3Initial.exact
            or self.initial == Fmi3Initial.approx
            or self.causality == Fmi3Causality.input
            or self.causality == Fmi3Causality.parameter
            or self.variability == Fmi3Variability.constant
        )

    def to_xml(self) -> Element:
        """Convert the variable to XML node.

        Returns
        -------
            xml.etree.ElementTree.Element: XML node
        """
        attrib = dict()
        for key, value in ChainMap(self._extras, self.__attrs).items():
            if value is not None:
                attrib[key] = ModelVariable.to_str(value)
        return Element(self._type, attrib)

    @staticmethod
    def to_str(val: Any):
        """Helper method to translate python values to proper strings for use in xml."""
        if isinstance(val, bool):
            return str(val).lower()
        if isinstance(val, float):
            return f"{val:.16g}"
        if isinstance(val, Enum):
            return val.name
        return str(val)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name={self.name}, causality={self.causality}, variability={self.variability})"
        )


class Start:
    def __init__(self, startValue):
        self.value = startValue

    def to_xml(self) -> Element:
        attrib = dict()
        attrib["value"] = ModelVariable.to_str(self.value)
        return Element("Start", attrib)


class Dimension:
    def __init__(self, start: str = "", valueReference: str = ""):
        if start and valueReference and any((start, valueReference)):
            raise RuntimeError("start and valueReference attributes are mutally exclusive for Dimension element")

        self.start = start
        self.value_reference = valueReference

    def size(self, vars: list[ModelVariable]):
        if self.start:
            return self.start
        result = next(
            (value for vr, value in vars.items() if vr == int(self.value_reference)),
            None,
        )
        return result.getter()

    def to_xml(self) -> Element:
        attrib = dict()

        if self.start:
            attrib["start"] = str(self.start)
        else:
            attrib["valueReference"] = str(self.value_reference)
        ele = Element("Dimension", attrib)
        return ele


class Arrayable:
    def __init__(self, dimensions: list[Dimension] = [], **kwargs):
        if dimensions:
            check_numpy()
        self._dimensions = dimensions

    @property
    def dimensions(self) -> list[Dimension]:
        return self._dimensions

    def get_start_str(self, value, formatter=None):
        if formatter is None:
            formatter = ModelVariable.to_str
        if len(self.dimensions) > 0:
            output = " ".join([formatter(val) for val in flatten(value)])
            if len(output) > MAX_LENGTH:
                output = output[0]
            return output
        return formatter(value)

    def dimensions_xml(self) -> list[Element]:
        return [dim.to_xml() for dim in self._dimensions]

    def size(self, vars):
        return reduce(lambda x, dim: x * int(dim.size(vars)), self._dimensions, 1)


class Float64(ModelVariable, Arrayable):
    def __init__(
        self,
        name: str,
        start: Any | None = None,
        derivative: Any | None = None,
        dimensions: list[Dimension] = [],
        unit: str | None = None,
        **kwargs,
    ):
        ModelVariable.__init__(self, name, **kwargs)
        Arrayable.__init__(self, dimensions)
        self.__attrs = {"start": start, "derivative": derivative}
        self._type = "Float64"
        self._unit = unit

    @property
    def start(self) -> Any | None:
        return self.__attrs["start"]

    @start.setter
    def start(self, value: float):
        self.__attrs["start"] = value

    @property
    def unit(self) -> Any | None:
        return self._unit

    @unit.setter
    def unit(self, value: str):
        self._unit = value

    @property
    def derivative(self):
        return self.__attrs["derivative"]

    def to_xml(self) -> Element:
        attrib = dict()
        for key, value in self.__attrs.items():
            if value is not None:
                # In order to not loose precision, a number of this type should be
                # stored on an XML file with at least 16 significant digits
                output = self.get_start_str(value)
                attrib[key] = output

        if self.unit:
            attrib["unit"] = self.unit

        self._extras = attrib
        parent = super().to_xml()

        parent.extend(self.dimensions_xml())

        return parent

class Float32(Float64):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._type = "Float32"

class Int32(ModelVariable, Arrayable):
    def __init__(
        self,
        name: str,
        start: Any | None = None,
        dimensions: list[Dimension] = [],
        **kwargs,
    ):
        ModelVariable.__init__(self, name, **kwargs)
        Arrayable.__init__(self, dimensions, **kwargs)
        self.__attrs = {"start": start}
        self._type = "Int32"

    @property
    def start(self) -> Any | None:
        return self.__attrs["start"]

    @start.setter
    def start(self, value: int):
        self.__attrs["start"] = value

    def to_xml(self) -> Element:
        attrib = dict()
        for key, value in self.__attrs.items():
            if value is not None:
                attrib[key] = self.get_start_str(value)
        self._extras = attrib
        parent = super().to_xml()

        parent.extend(self.dimensions_xml())

        return parent


class Int64(ModelVariable, Arrayable):
    def __init__(
        self,
        name: str,
        start: Any | None = None,
        dimensions: list[Dimension] = [],
        **kwargs,
    ):
        ModelVariable.__init__(self, name, **kwargs)
        Arrayable.__init__(self, dimensions, **kwargs)
        self.__attrs = {"start": start}
        self._type = "Int64"

    @property
    def start(self) -> Any | None:
        return self.__attrs["start"]

    @start.setter
    def start(self, value: int):
        self.__attrs["start"] = value

    def to_xml(self) -> Element:
        attrib = dict()
        for key, value in self.__attrs.items():
            if value is not None:
                attrib[key] = self.get_start_str(value)
        self._extras = attrib
        parent = super().to_xml()

        parent.extend(self.dimensions_xml())

        return parent
#
class Int8(Int32):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._type = "Int8"

class Int16(Int32):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._type = "Int16"

# class Int64(Int32):
#     def __init__(self,**kwargs):
#         super().__init__(**kwargs)
#         self._type = "Int64"


class UInt64(ModelVariable, Arrayable):
    def __init__(
        self,
        name: str,
        start: Any | None = None,
        dimensions: list[Dimension] = [],
        **kwargs,
    ):
        ModelVariable.__init__(self, name, **kwargs)
        Arrayable.__init__(self, dimensions, **kwargs)
        self.__attrs = {"start": start}
        self._type = "UInt64"

    @property
    def start(self) -> Any | None:
        return self.__attrs["start"]

    @start.setter
    def start(self, value: int):
        self.__attrs["start"] = value

    def to_xml(self) -> Element:
        attrib = dict()
        for key, value in self.__attrs.items():
            if value is not None:
                attrib[key] = self.get_start_str(value)
        self._extras = attrib
        parent = super().to_xml()

        parent.extend(self.dimensions_xml())

        return parent

class UInt8(UInt64):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._type = "UInt8"

class UInt16(UInt64):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._type = "UInt16"
        
class UInt32(UInt64):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._type = "UInt32"


class Boolean(ModelVariable, Arrayable):
    def __init__(
        self,
        name: str,
        start: Any | None = None,
        dimensions: list[Dimension] = [],
        **kwargs,
    ):
        ModelVariable.__init__(self, name, **kwargs)
        Arrayable.__init__(self, dimensions, **kwargs)
        self.__attrs = {"start": start}
        self._type = "Boolean"

    @property
    def start(self) -> Any | None:
        return self.__attrs["start"]

    @start.setter
    def start(self, value: float):
        self.__attrs["start"] = value

    def to_xml(self) -> Element:
        attrib = dict()
        for key, value in self.__attrs.items():
            if value is not None:
                attrib[key] = self.get_start_str(value)
        self._extras = attrib
        parent = super().to_xml()

        parent.extend(self.dimensions_xml())

        return parent


class String(ModelVariable):
    def __init__(
        self,
        name: str,
        start: Any | None = None,
        dimensions: list[Dimension] = [],
        **kwargs,
    ):
        ModelVariable.__init__(self, name, **kwargs)
        self.__attrs = dict()
        self._type = "String"
        self._start = Start(start)

    @property
    def start(self) -> Any | None:
        return self._start.value

    @start.setter
    def start(self, value: float):
        self._start.value = value

    def to_xml(self) -> Element:
        attrib = dict()
        for key, value in self.__attrs.items():
            if value is not None:
                attrib[key] = str(value)
        self._extras = attrib
        parent = super().to_xml()

        if self.start is not None:
            parent.append(self._start.to_xml())
        return parent


class Clock(ModelVariable):
    """Clock variable definition. See also fmi3Variable.xsd and fmi3AttributeGroups.xsd/fmi3ClockAttributes

    Args:
        name: name of the clock unique within FMU
        can_be_deactivated: boolean flag
        priority: optional explicit priority as unsigned int
        interval_variability: required enumeration attribute, similar to variability
        interval_decimal: optional initial specification of decimal interval + field
        shift_decimal: optional delay of first clock activations. Default 0
        supports_fraction: optional possibility to provide shifts as integer fractions
        resolution: optional initial denominator of interval fraction
        interval_counter: optional initial nominator of interval fraction
        shift_counter: optional initial nominator of shift (first clock activation)
    """

    def __init__(
        self,
        name: str,
        can_be_deactivated: bool = False,
        priority: int | None = None,
        interval_variability: Fmi3IntervalVariability = Fmi3IntervalVariability.constant,
        interval_decimal: float | None = None,
        shift_decimal: float = 0.0,
        supports_fraction: bool = False,
        resolution: int | None = None,
        interval_counter: int | None = None,
        shift_counter: int = 0,
        **kwargs,
    ):
        ModelVariable.__init__(self, name, **kwargs)
        self.__attrs = {
            "canBeDeactivated": can_be_deactivated,
            "priority": priority,
            "intervalVariability": interval_variability,
            "intervalDecimal": interval_decimal,
            "shiftDecimal": shift_decimal,
            "supportsFraction": supports_fraction,
        }
        if supports_fraction:
            self.__attrs.update(
                {
                    "resolution": resolution,
                    "intervalCounter": interval_counter,
                    "shiftCounter": shift_counter,
                }
            )
        self._type = "Clock"

    def to_xml(self) -> Element:
        attrib = dict()
        for key, value in self.__attrs.items():
            if value is not None:
                attrib[key] = ModelVariable.to_str(value)
        self._extras = attrib
        parent = super().to_xml()

        return parent


class Enumeration(ModelVariable, Arrayable):
    def __init__(
        self,
        name: str,
        start: Any | None = None,
        declared_type: Any | None = None,
        dimensions: list[Dimension] = [],
        **kwargs,
    ):
        ModelVariable.__init__(self, name, **kwargs)
        Arrayable.__init__(self, dimensions, **kwargs)
        self.__attrs = {"start": start, "declaredType": declared_type}
        self._type = "Enumeration"

    @property
    def start(self) -> Any | None:
        return self.__attrs["start"]

    @start.setter
    def start(self, value: float) -> None:
        self.__attrs["start"] = value

    @property
    def declared_type(self) -> str | None:
        return self.__attrs["declaredType"]

    @declared_type.setter
    def declared_type(self, value: str) -> None:
        self.__attrs["declaredType"] = value

    def to_xml(self) -> Element:
        attrib : dict[str,str] = {}
        for key, value in self.__attrs.items():
            if value is not None:
                attrib[key] = str(value)
        self._extras = attrib
        parent = super().to_xml()

        return parent

# fmi_types: dict[type, Any] = {
#     #float : Real,
#     #int : Integer,
#     bool : Boolean,
#     str : String,
#     np.float32 : Float32,
#     np.float64 : Float64,
#     np.int8 : Int8,
#     np.uint8 : UInt8,
#     np.int16 : Int16,
#     np.uint16 : UInt16,
#     np.int32 : Int32,
#     np.uint32 : UInt32,
#     np.int64 :Int64,
#     np.uint64 : UInt64,
#     # int : Enumeration, ! not unique
#     # bool : Clock, ! not unique
# }

