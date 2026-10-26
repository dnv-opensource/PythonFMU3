# Changelog

All notable changes to the [PythonFMU3s] project from version 0.4.0 will be documented in this file.<br>
The changelog format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

* -/-



## [0.4.0] - 2026-11
The main goal was the inclusion of event-related functions in the package.
In addition also other functions have been implemented, but there are still some pending FMI3 functions.
All changes where implemented in the branch *eis*

* Re-structured project to the standard src/pythonfmu3/ structure and moving tests/ out. Ran ruff check --fix and ruff format on project
* Fixed tests so that ============================= test session starts ==============================
* Added the PID-controller example to /examples. Needed fixes. Changed therefore docs/usage.md and adapted the documentation build process (adding conf.py, /_static and /_templates)
* Added the implementation of EnterEventMode fmi3 function to the Cpp code. Successfull compilation. Added a basic discrete event example.
* Updated the documentation of ModelVariables class and added since this is not only in use for ME, but also for CS in event mode. It is set to True per default as per FMI spec
* Added a variable type 'Clock' to ModelVariables. Added some documentation also to other variable types and added ModelVariables.to_str as formatter for python types to xml strings
* Implemented all event-related functions in cppfmu/ and pythonfmu/. Code compiles, but is so far not yet tested.
* Added the function EnterStepMode, which was completely missing, such that no switch back to step mode was possible. Compilation ok.
* In order to receive results from UpdateDiscreteStates() a dedicated NamedTuple needs to be defined and used.
* Ensure all FMI3 model options, so that the system can work with FMI3 features. Options are now implemented as dataclass and it is possible to provide options directly to the Slave (not only through cli). Tested features.
* Change in builder.py to include model options properly
* Corrected errors in fmi3slave.py and variables.py leading to errors in FMU building and FMU usage with respect to variables with dimensions
* Added an FMI3 FMU 'function' as an example for a *pass-through* event-based FMU. Tested basic usage.
* Adapted function signatures to be as close as possible to FMI3 standard. SetupExperiment deprecated, EnterInitializationMode updated, EnterContinuousTimeMode and CompletedIntegratorStep added. Recompiled and basic tests.
* Added the arguments 'eventModeUsed' and 'earlyReturnAllowed' in InstantiateCosimulation, which where so far not included. Related changes in fmi3slave are also implemented. Compiles and test works. IntermediateUpdate management is still not included.
* Some last changes as part of moving back to windows. Windows compilation not yet included.
* Added windows support to the package. The dynamic libraries and the generated FMUs have been added to the git package (.gitignore changed).
* Minor updates within the example FMUs to support discrete_event mode
* Added a CHANGELOG.md file to the package and included this point list from the git commit messages.
* 




