from importlib.metadata import version
import logging
import pytest

from pythonfmu3 import Fmi3Slave, ModelExchange
from pythonfmu3.variables import py_types, fmi_type, fmi_type_version

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# TODO test xml

implemented = ("Boolean","String","Float64","Int64","Int32","UInt64") # implement the others in cpp and fmi3slave

def example( _type:str):
    """Provide an example value for the FMI _type as str."""
    if _type=='Enumeration' or 'int' in _type.lower():
        return py_types[_type](3)
    elif _type == "Real" or 'float' in _type.lower():
        return py_types[_type](9.9)
    elif _type in ("Boolean", "Clock"):
        return True
    elif _type=='String':
        return 'Hello World'
    else:
        raise KeyError(f"Unknown FMI type {_type}")

@pytest.mark.parametrize("model", ["theModelName", None])
def test_fmi3slave_constructor(model):

    class Slave(Fmi3Slave):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            if model is not None:
                self.modelName = model

        def do_step(self, t, dt):
            return True

    if model is None:
        slave = Slave(instanceName="slaveInstance")
        assert slave.modelName == "Slave"
        assert slave.instance_name == "slaveInstance"
    else:
        slave = Slave(instanceName="slaveInstance")
        assert slave.modelName == model
        assert slave.instance_name == "slaveInstance"


def test_fmi3slave_generation_tool():
    class Slave(Fmi3Slave):
        def do_step(self, t, dt):
            return True

    slave = Slave(instanceName="instance")
    xml = slave.to_xml()

    assert xml.attrib["generationTool"] == f"PythonFMU3 {version('PythonFMU3')}"


def test_fmi3slave_getters():

    class Slave(Fmi3Slave):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.var = value
            print("MAKE", fmi_typ)
            self.register_variable(fmi_typ(name = "var"))

        def do_step(self, t, dt):
            return True

    for fmi_type_name, py_type in py_types.items():
        if fmi_type_version(fmi_type_name, 3) and fmi_type_name not in implemented:
            LOGGER.error(f"FMI type {fmi_type_name} is not yet fully implemented. Skip.")
        elif fmi_type_version(fmi_type_name, 3):
            value = example(fmi_type_name)
            fmi_typ = fmi_type(fmi_type_name)
            slave = Slave(instanceName="slaveInstance")
            
            if type(value) is py_type:
                assert getattr(slave, f"get_{fmi_type_name.lower()}")([0]) == [value]
            else:
                with pytest.raises(TypeError):
                    getattr(slave, f"get_{fmi_type_name.lower()}")([0])


def test_fmi3slave_setters():

    class Slave(Fmi3Slave):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.var = None
            self.register_variable(fmi_typ(name="var"))

        def do_step(self, t, dt):
            return True

    for fmi_type_name, py_type in py_types.items():
        if fmi_type_version(fmi_type_name, 3) and fmi_type_name not in implemented:
            LOGGER.error(f"FMI type {fmi_type_name} is not yet fully implemented. Skip.")
        elif fmi_type_version(fmi_type_name, 3):
            value = example(fmi_type_name)
            fmi_typ = fmi_type(fmi_type_name)
            slave = Slave(instanceName="slaveInstance")

            if type(value) is py_type:
                set_method = getattr(slave, f"set_{fmi_type_name.lower()}")
                set_method([0], [value])
                assert getattr(slave, f"get_{fmi_type_name.lower()}")([0]) == [value]
            else:
                set_method = getattr(slave, f"set_{fmi_type_name.lower()}")
                with pytest.raises(TypeError):
                    set_method([0], [value])


def test_fmi3slave_log_categories():
    class Slave(Fmi3Slave):
        def do_step(self, t, dt):
            return True

    slave = Slave(instanceName="instance")
    xml = slave.to_xml()

    categories = xml.find("LogCategories")
    assert len(categories) == len(Slave.log_categories)
    for category, description in Slave.log_categories.items():
        assert categories.find(f"Category[@name='{category}'][@description='{description}']") is not None


@pytest.mark.parametrize(
    "new_categories",
    [
        {
            "logStatusWarning": "Log messages with fmi3Warning status.",
            "logStatusError": "Log messages with fmi3Error status.",
            "logStatusFatal": "Log messages with fmi3Fatal status.",
            "logAll": "Log all messages.",
        },
        {
            "logCustom1": "My first custom log category",
            "logCustom2": "My second custom log category",
        },
    ],
)
def test_fmi3slave_customized_log_categories(new_categories):
    class Slave(Fmi3Slave):
        log_categories = new_categories

        def do_step(self, t, dt):
            return True

    slave = Slave(instanceName="instance")
    xml = slave.to_xml()

    categories = xml.find("LogCategories")

    if len(new_categories) > 0:
        assert len(categories) == len(Slave.log_categories)
        for category, description in Slave.log_categories.items():
            assert categories.find(f"Category[@name='{category}'][@description='{description}']") is not None
    else:
        assert categories is None


def test_fmi3slave_model_exchange():
    class Slave(Fmi3Slave, ModelExchange):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.time = 0.0

        def get_continuous_state_derivatives(self, vals):
            return []

    slave = Slave(instanceName="instance")
    xml = slave.to_xml()

    categories = xml.find("ModelExchange")

    assert categories is not None, "ModelExchange category should be present in the XML"

if __name__ == "__main__":
    """Possibility to run single or all tests from the IDE."""
    retcode = 1
    if retcode == 0:
        retcode = pytest.main(["-rA", "-v", "--rootdir", "../", "--show", "False", __file__])
        assert retcode == 0, f"Non-zero return code {retcode}"
 
    # test_fmi3slave_constructor("theModelName")
    # test_fmi3slave_constructor(None)
    # test_fmi3slave_getters()
    # test_fmi3slave_setters()
    # test_fmi3slave_generation_tool()
    # test_fmi3slave_log_categories()
    # test_fmi3slave_customized_log_categories(
    #     {"logStatusWarning":"Log warning","logStatusError":"Log error","logStatusFatal":"Log fatal","logAll":"Log all"})
    #test_fmi3slave_customized_log_categories({"logCustom1": "Custom log 1", "logCustom2": "Custom log 2"})


