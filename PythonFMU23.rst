########################
PythonFMU for FMI2 and 3
########################
Notes on how to make PythonFMU3 work for both FMI2 and FMI3.

* Folder `src/pythonfmu3` should be renamed to `src/pythonfmu`
* Folder `src/pythonfmu3/pythonfmu-export` should be renamed to src/pythonfmu/pythonfmu3-export`
* Folder `src/pythonfmu/pythonfmu2-export` should be added with content from the `PythonFMU` repository. 

Files in src/pythonfmu3/
========================

builder.py
----------
* `get_model_description()`: should work, but should probably be replaced by the more flexible version from PythonFMU. Requires also that the related c-code (adapted) is replaced.
* **FmuBuilder.build_FMU()** should be simplified in any case and needs adaptation. 
  Add also a parameter telling the builder which FMI version to use - or make automatic??
  Change also _FMU to _fmu.
* `create_command_parser`: needs to be changed in relation to changes in build_FMU

cosimulation.py
---------------
* **CoSimulation(ABC)**: need to decide how to handle the method `do_step()` and `enter_initialization_mode()`, 
  which have a different signature in FMI2 and FMI3.

modelexchange.py
----------------
* **ModelExchange(ABC,...)**: some of the methods do not exist in FMI2

default_experiment.py
---------------------
* keep as is. Note that this is used differently in FMI2 (`setup_experiment()`) and FMI3 (`enter_initialization_mode()`)

deploy.py
---------
* keep as is

enums.py
--------
* all enums are defined as **Fmi3...**. Need to decide whether to make equivalent fmi2 enums or make the classes neutral with respect to FMI version. Note that a few minor changes between FMI2 and FMI3 must be handled and the Fmi3Type enum seems both wrong and unused.

fmi3slave.py
------------
* **Fmi3Slave** and **Fmi3SlaveBase** are made for FMI3. Make a similar fmi2slave.py for FMI2.

logmsg.py
---------
* keep as is. Check whether the logging strategy is aligned with the FMI standard.

model_options.py
----------------
* all class names are **Fmi3...**. Need to decide whether to make equivalent fmi2 classes or make the classes neutral with respect to FMI version. Some properties do not exist in FMI2, which would need to be managed, so that they are not listed in modelDescription.xml

model_returns.py
----------------
* only relevant for FMI3, since FMI2 does not use these more comåplex returns.

osutil.py
---------
* keep as is. The file should probably be **moved to a utils/ folder**.

unit.py
-------
* keep as is. **Check** whether there are no changes in the handling of units between FMI2 and FMI3

variables.py
------------
* `py_types`: FMI2 types `Real`and `Integer`are included. Can use `fmi_type_version()` to check whether type is allowed in FMI version used.
* `fmi_type_version()`: useful to whether type is allowed in FMI version used.
* `fmi_type`: ok
* `ModelVariable`: name of the class changed from ScalarVariable to ModelVariable. The signature is still compatible with both FMI2 and FMI3. Can probably live with the FMI3 name, making sure that **ScalarVariable** is used when generating the modelDescription in FMI2. See `to_xml()` and `to_str()` methods.
* `Start`: ok
* `Dimension`: does not exist in FMI2. Either make sure that it is **not used in FMI2** or **automatically translate** to a set of ScalarVariable, using the structured variableNamingConvention. 
* `Arrayable`. See `Dimension`.
* `Float64 ...`: do not exist in FMI2. **Add** `Real` and `Integer` classes. We could choose to **automatically translate** `Float64` and `Int32` into `Real`and `Integer` classes when building FMI2.
* Clock: does not exist in FMI2. **Check** that it is not used when building FMI2.

variable_types.py
-----------------
* the defined classes should be ok under FMI2 also. **Float64Type** shall not be used under FMI2.







