#include "utils/fluxara_device_validation_ios.hpp"

#include "utils/log.hpp"

#include <mach/mach.h>

void fluxaraLogDeviceValidationMemory(const std::string& boundary,
                                      const std::string& event_id)
{
    task_vm_info_data_t vm = {};
    mach_msg_type_number_t vm_count = TASK_VM_INFO_COUNT;
    const kern_return_t vm_result = task_info(mach_task_self(), TASK_VM_INFO,
        reinterpret_cast<task_info_t>(&vm), &vm_count);

    mach_task_basic_info_data_t basic = {};
    mach_msg_type_number_t basic_count = MACH_TASK_BASIC_INFO_COUNT;
    const kern_return_t basic_result = task_info(mach_task_self(),
        MACH_TASK_BASIC_INFO, reinterpret_cast<task_info_t>(&basic),
        &basic_count);

    thread_act_array_t threads = nullptr;
    mach_msg_type_number_t thread_count = 0;
    const kern_return_t threads_result = task_threads(mach_task_self(),
        &threads, &thread_count);
    if (threads_result == KERN_SUCCESS && threads)
        vm_deallocate(mach_task_self(), reinterpret_cast<vm_address_t>(threads),
            vm_size_t(thread_count) * sizeof(thread_t));

    const unsigned long long resident = basic_result == KERN_SUCCESS
        ? static_cast<unsigned long long>(basic.resident_size) : 0ULL;
    const unsigned long long footprint = vm_result == KERN_SUCCESS
        ? static_cast<unsigned long long>(vm.phys_footprint) : 0ULL;
    const unsigned long long virtual_size = vm_result == KERN_SUCCESS
        ? static_cast<unsigned long long>(vm.virtual_size) : 0ULL;
    Log::info("FluxaraDeviceSoak",
        "memory boundary=%s event=%s resident_bytes=%llu footprint_bytes=%llu virtual_bytes=%llu threads=%u task_vm=%d basic=%d threads_result=%d",
        boundary.c_str(), event_id.c_str(), resident, footprint, virtual_size,
        threads_result == KERN_SUCCESS ? unsigned(thread_count) : 0u,
        int(vm_result), int(basic_result), int(threads_result));
}
