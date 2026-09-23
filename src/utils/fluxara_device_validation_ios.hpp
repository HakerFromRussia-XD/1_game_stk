#ifndef HEADER_FLUXARA_DEVICE_VALIDATION_IOS_HPP
#define HEADER_FLUXARA_DEVICE_VALIDATION_IOS_HPP

#include <string>

// Emits a compact memory sample from the running iPhone process.  It is used
// exclusively by the hidden one-process campaign soak route.
void fluxaraLogDeviceValidationMemory(const std::string& boundary,
                                      const std::string& event_id);

#endif
