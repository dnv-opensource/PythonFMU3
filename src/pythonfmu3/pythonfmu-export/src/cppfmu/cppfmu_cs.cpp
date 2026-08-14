/* Copyright 2016-2019, SINTEF Ocean.
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */
#include "cppfmu/cppfmu_cs.hpp"

#include <stdexcept>


namespace cppfmu
{

// =============================================================================
// SlaveInstance
// =============================================================================


void SlaveInstance::SetupExperiment(
    FMIBoolean /*toleranceDefined*/,
    FMIFloat64 /*tolerance*/,
    FMIFloat64 /*tStart*/,
    FMIBoolean /*stopTimeDefined*/,
    FMIFloat64 /*tStop*/)
{
    // Do nothing
}


void SlaveInstance::EnterInitializationMode()
{
    // Do nothing
}


void SlaveInstance::ExitInitializationMode()
{
    // Do nothing
}


void SlaveInstance::Terminate()
{
    // Do nothing
}


void SlaveInstance::Reset()
{
    // Do nothing
}

void SlaveInstance::SetFloat64(
    const FMIValueReference /*vr*/[],
    std::size_t nvr,
    const FMIFloat64 /*value*/[],
    std::size_t nValues)
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}

void SlaveInstance::SetInt32(
    const FMIValueReference /*vr*/[],
    std::size_t nvr,
    const FMIInt32 /*value*/[],
    std::size_t nValues)
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}

void SlaveInstance::SetInt64(
    const FMIValueReference /*vr*/[],
    std::size_t nvr,
    const FMIInt64 /*value*/[],
    std::size_t nValues)
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}

void SlaveInstance::SetUInt64(
    const FMIValueReference /*vr*/[],
    std::size_t nvr,
    const FMIUInt64 /*value*/[],
    std::size_t nValues)
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}

void SlaveInstance::SetBoolean(
    const FMIValueReference /*vr*/[],
    std::size_t nvr,
    const FMIBoolean /*value*/[],
    std::size_t nValues)
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}

void SlaveInstance::SetString(
    const FMIValueReference /*vr*/[],
    std::size_t nvr,
    const FMIString /*value*/[],
    std::size_t nValues)
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}


void SlaveInstance::GetFloat64(
    const FMIValueReference /*vr*/[],
    std::size_t nvr,
    FMIFloat64 /*value*/[],
    std::size_t nValues) const
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to get nonexistent variable");
    }
}


void SlaveInstance::GetInt32(
    const FMIValueReference /*vr*/[],
    std::size_t nvr,
    FMIInt32 /*value*/[],
    std::size_t nValues) const
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to get nonexistent variable");
    }
}


void SlaveInstance::GetInt64(
    const FMIValueReference /*vr*/[],
    std::size_t nvr,
    FMIInt64 /*value*/[],
    std::size_t nValues) const
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to get nonexistent variable");
    }
}


void SlaveInstance::GetUInt64(
    const FMIValueReference /*vr*/[],
    std::size_t nvr,
    FMIUInt64 /*value*/[],
    std::size_t nValues) const
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to get nonexistent variable");
    }
}


void SlaveInstance::GetBoolean(
    const FMIValueReference /*vr*/[],
    std::size_t nvr,
    FMIBoolean /*value*/[],
    std::size_t nValues) const
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}


void SlaveInstance::GetString(
    const FMIValueReference /*vr*/[],
    std::size_t nvr,
    FMIString /*value*/[],
    std::size_t nValues) const
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}

// Event- and Clock-related functions
void SlaveInstance::EnterEventMode()
{
    // Do nothing
}
void SlaveInstance::EnterStepMode()
{
    // Do nothing
}
void SlaveInstance::UpdateDiscreteStates(
        cppfmu::FMIBoolean* discreteStatesNeedUpdate,
        cppfmu::FMIBoolean* terminateSimulation,
        cppfmu::FMIBoolean* nominalContinuousStatesChanged,
        cppfmu::FMIBoolean* valuesOfContinuousStatesChanged,
        cppfmu::FMIBoolean* nextEventTimeDefined,
        cppfmu::FMIFloat64* nextEventTime)
{
    // Do nothing
}

void SlaveInstance::GetClock(  const FMIValueReference /*vr*/[], std::size_t nvr, FMIClock /*values*/[]) const
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}
void SlaveInstance::SetClock(  const FMIValueReference /*vr*/[], std::size_t nvr, const FMIClock /*values*/[])
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}
void SlaveInstance::GetIntervalDecimal(
        const FMIValueReference /*vr*/[],
        std::size_t nvr,
        FMIFloat64 /*intervals*/[],
        FMIIntervalQualifier /*qualifiers*/[]) const
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}
void SlaveInstance::SetIntervalDecimal(const FMIValueReference /*vr*/[], std::size_t nvr, const FMIFloat64 /*intervals*/[])
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}
void SlaveInstance::GetShiftDecimal( const FMIValueReference /*vr*/[], std::size_t nvr, FMIFloat64 /*shifts*/[]) const
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}
void SlaveInstance::SetShiftDecimal( const FMIValueReference /*vr*/[], std::size_t nvr, const FMIFloat64 /*shifts*/[])
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}
void SlaveInstance::GetIntervalFraction(
        const FMIValueReference /*vr*/[],
        std::size_t nvr,
        FMIUInt64 /*intervalCounters*/[],
        FMIUInt64 /*resolutions*/[],
        FMIIntervalQualifier /*qualifiers*/[]) const
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}
void SlaveInstance::SetIntervalFraction(
        const FMIValueReference /*vr*/[],
        std::size_t nvr,
        const FMIUInt64 /*intervalCounters*/[],
        const FMIUInt64 /*resolutions*/[])
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}
void SlaveInstance::GetShiftFraction(
        const FMIValueReference /*vr*/[],
        std::size_t nvr,
        FMIUInt64 /*shiftCounters*/[],
        FMIUInt64 /*resolutions*/[]) const
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}
void SlaveInstance::SetShiftFraction(
        const FMIValueReference /*vr*/[],
        std::size_t nvr,
        const FMIUInt64 /*shiftCounters*/[],
        const FMIUInt64 /*resolutions*/[])
{
    if (nvr != 0) {
        throw std::logic_error("Attempted to set nonexistent variable");
    }
}



SlaveInstance::~SlaveInstance() CPPFMU_NOEXCEPT
{
    // Do nothing
}


} // namespace cppfmu
