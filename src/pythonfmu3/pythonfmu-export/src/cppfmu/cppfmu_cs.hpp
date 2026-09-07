/* Copyright 2016-2019, SINTEF Ocean.
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */
#ifndef CPPFMU_CS_HPP
#define CPPFMU_CS_HPP

#include "cppfmu_common.hpp"

#include <vector>
#include <memory>

namespace cppfmu
{

/* ============================================================================
 * CO-SIMULATION INTERFACE
 * ============================================================================
 */

/* A base class for co-simulation slave instances.
 *
 * To implement a co-simulation slave, create a class which publicly derives
 * from this one and override its virtual methods as required.  DoStep() is
 * the only function which it is mandatory to override.
 *
 * The methods map directly to the C functions defined by FMI 2.0 (and, with
 * some adaptations, FMI 1.0), so the documentation here is intentionally
 * sparse.  We refer to the FMI specifications for detailed information.
 */
class SlaveInstance
{
public:
    /* Called from fmi3SetupExperiment() (FMI 2.0) or fmiInitializeSlave()
     * (FMI 1.0).
     * Does nothing by default.
     */
    /* not in FMI3:
    virtual void SetupExperiment(
        FMIBoolean toleranceDefined,
        FMIFloat64 tolerance,
        FMIFloat64 tStart,
        FMIBoolean stopTimeDefined,
        FMIFloat64 tStop);

     * Called from fmi3EnterInitializationMode() (FMI 2.0) or
     * fmiInitializeSlave() (FMI 1.0).
     * Does nothing by default.
     */
    virtual void EnterInitializationMode(
        FMIBoolean toleranceDefined,
        FMIFloat64 tolerance,
        FMIFloat64 tStart,
        FMIBoolean stopTimeDefined,
        FMIFloat64 stopTime);

    /* Changed signature in FMI3!
     * Does nothing by default.
     */
    virtual void ExitInitializationMode();

    /* Called from fmi3Terminate()/fmiTerminateSlave().
     * Does nothing by default.
     */
    virtual void Terminate();

    /* Called from fmi3Reset()/fmiResetSlave().
     * Does nothing by default.
     */
    virtual void Reset();

    /* Called from fmi3SetXxx()/fmiSetXxx().
     * Throws std::logic_error by default.
     */
    virtual void SetFloat64(
        const FMIValueReference vr[],
        std::size_t nvr,
        const FMIFloat64 value[],
        std::size_t nValues);
    virtual void SetInt32(
        const FMIValueReference vr[],
        std::size_t nvr,
        const FMIInt32 value[],
        std::size_t nValues);
    virtual void SetInt64(
        const FMIValueReference vr[],
        std::size_t nvr,
        const FMIInt64 value[],
        std::size_t nValues);
    virtual void SetUInt64(
        const FMIValueReference vr[],
        std::size_t nvr,
        const FMIUInt64 value[],
        std::size_t nValues);
    virtual void SetBoolean(
        const FMIValueReference vr[],
        std::size_t nvr,
        const FMIBoolean value[],
        std::size_t nValues);
    virtual void SetString(
        const FMIValueReference vr[],
        std::size_t nvr,
        const FMIString value[],
        std::size_t nValues);

    /* Called from fmi3GetXxx()/fmiGetXxx().
     * Throws std::logic_error by default.
     */
    virtual void GetFloat64(
        const FMIValueReference vr[],
        std::size_t nvr,
        FMIFloat64 value[],
        std::size_t nValues) const;
    virtual void GetInt32(
        const FMIValueReference vr[],
        std::size_t nvr,
        FMIInt32 value[],
        std::size_t nValues) const;
    virtual void GetInt64(
        const FMIValueReference vr[],
        std::size_t nvr,
        FMIInt64 value[],
        std::size_t nValues) const;
    virtual void GetUInt64(
        const FMIValueReference vr[],
        std::size_t nvr,
        FMIUInt64 value[],
        std::size_t nValues) const;
    virtual void GetBoolean(
        const FMIValueReference vr[],
        std::size_t nvr,
        FMIBoolean value[],
        std::size_t nValues) const;
    virtual void GetString(
        const FMIValueReference vr[],
        std::size_t nvr,
        FMIString value[],
        std::size_t nValues) const;

    // Called from fmi3DoStep()/fmiDoStep(). Must be implemented in model code.
    virtual void DoStep(
        FMIFloat64 currentCommunicationPoint,
        FMIFloat64 communicationStepSize,
        FMIBoolean noSetFMUStatePriorToCurrentPoint,
        FMIBoolean* eventHandlingNeeded,
        FMIBoolean* terminateSimulation,
        FMIBoolean* earlyReturn,
        FMIFloat64* lastSuccessfullTime);

    // Event- and Clock-related functions
    virtual void EnterEventMode();
    virtual void EnterContinuousTimeMode();
    virtual void CompletedIntegratorStep(
        fmi3Boolean noSetFMUStatePriorToCurrentPoint,
        fmi3Boolean* enterEventMode,
        fmi3Boolean* terminateSimulation);
    virtual void EnterStepMode();
    virtual void GetClock(  const FMIValueReference vr[], std::size_t nvr, FMIClock values[]) const;
    virtual void SetClock(  const FMIValueReference vr[], std::size_t nvr, const FMIClock values[]);
    virtual void GetIntervalDecimal(
        const FMIValueReference vr[],
        std::size_t nvr,
        FMIFloat64 intervals[],
        FMIIntervalQualifier qualifiers[]) const;
    virtual void SetIntervalDecimal(const FMIValueReference vr[], std::size_t nvr, const FMIFloat64 intervals[]);
    virtual void GetShiftDecimal( const FMIValueReference vr[], std::size_t nvr, FMIFloat64 shifts[]) const;
    virtual void SetShiftDecimal( const FMIValueReference vr[], std::size_t nvr, const FMIFloat64 shifts[]);
    virtual void GetIntervalFraction(
        const FMIValueReference vr[],
        std::size_t nvr,
        FMIUInt64 intervalCounters[],
        FMIUInt64 resolutions[],
        FMIIntervalQualifier qualifiers[]) const;
    virtual void SetIntervalFraction(
        const FMIValueReference vr[],
        std::size_t nvr,
        const FMIUInt64 intervalCounters[],
        const FMIUInt64 resolutions[]);
    virtual void GetShiftFraction(
        const FMIValueReference vr[],
        std::size_t nvr,
        FMIUInt64 shiftCounters[],
        FMIUInt64 resolutions[]) const;
    virtual void SetShiftFraction(
        const FMIValueReference vr[],
        std::size_t nvr,
        const FMIUInt64 shiftCounters[],
        const FMIUInt64 resolutions[]);

    // Model Exchange methods
    virtual void GetContinuousStates(cppfmu::FMIFloat64* continuousStates, std::size_t nStates) const = 0;
    virtual void GetContinuousStateDerivatives(cppfmu::FMIFloat64* derivatives, std::size_t nStates) const = 0;
    virtual void GetNominalsOfContinuousStates(cppfmu::FMIFloat64* nominalContinuousStates, std::size_t nStates) const = 0;
    virtual void SetContinuousStates(const cppfmu::FMIFloat64* continuousStates, std::size_t nStates) = 0;
    virtual void SetTime(cppfmu::FMIFloat64 time) = 0;
    virtual void GetNumberOfContinuousStates(std::size_t& nStates) const = 0;
    virtual void GetNumberOfEventIndicators(std::size_t& nEventIndicators) const = 0;
    virtual void GetEventIndicators(cppfmu::FMIFloat64* eventIndicators, std::size_t nEventIndicators) const = 0;
    virtual void UpdateDiscreteStates(
        cppfmu::FMIBoolean* discreteStatesNeedUpdate,
        cppfmu::FMIBoolean* terminateSimulation,
        cppfmu::FMIBoolean* nominalContinuousStatesChanged,
        cppfmu::FMIBoolean* valuesOfContinuousStatesChanged,
        cppfmu::FMIBoolean* nextEventTimeDefined,
        cppfmu::FMIFloat64* nextEventTime) = 0;


    virtual void GetFMUstate(fmi3FMUState& state) = 0;
    virtual void SetFMUstate(const fmi3FMUState& state) = 0;
    virtual void FreeFMUstate(fmi3FMUState& state) = 0;

    virtual size_t SerializedFMUstateSize(const fmi3FMUState& state) = 0;
    virtual void SerializeFMUstate(const fmi3FMUState& state, fmi3Byte bytes[], size_t size) = 0;
    virtual void DeSerializeFMUstate(const fmi3Byte bytes[], size_t size, fmi3FMUState& state) = 0;

    // The instance is destroyed in fmi3FreeInstance()/fmiFreeSlaveInstance().
    virtual ~SlaveInstance() CPPFMU_NOEXCEPT;
};

} // namespace cppfmu


/* A function which must be defined by model code, and which should create
 * and return a new slave instance.
 *
 * The returned instance must be managed by a std::unique_ptr with a deleter
 * of type std::function<void(void*)> that takes care of freeing the memory.
 * The simplest way to set this up is to use cppfmu::AllocateUnique() to
 * create the slave instance.
 *
 * Most of its parameters correspond to those of fmi3Instantiate() and
 * fmiInstantiateSlave(), except that 'functions' and 'loggingOn' have been
 * replaced with more convenient types:
 *
 *     memory = An object which the model code can use for memory management,
 *              typically in conjunction with cppfmu::Allocator,
 *              cppfmu::AllocateUnique(), etc.  Allocation and deallocation
 *              requests get forwarded to the simulation environment.
 *
 *     logger = An object which the model code can use to log messages (e.g.
 *              warnings or debug info).  The messages are forwarded to the
 *              simulation environment's logging facilities.
 *
 * Note that this function is declared in the global namespace.
 */
std::unique_ptr<cppfmu::SlaveInstance> CppfmuInstantiateSlave(
    cppfmu::FMIString instanceName,
    cppfmu::FMIString fmuGUID,
    cppfmu::FMIString fmuResourceLocation,
    cppfmu::FMIString mimeType,
    cppfmu::FMIFloat64 timeout,
    cppfmu::FMIBoolean visible,
    cppfmu::FMIBoolean interactive,
    const cppfmu::Logger& logger,
    cppfmu::FMIBoolean eventModeUsed,
    cppfmu::FMIBoolean earlyReturnAllowed
    );

#endif // header guard
