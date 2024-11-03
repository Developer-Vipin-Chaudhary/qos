#include "mem/qos/custom_policy.hh"
#include "base/trace.hh"
#include "debug/QOS.hh"

namespace gem5
{

namespace memory
{

namespace qos
{

StaticPolicy::StaticPolicy(const Params &p)
    : Policy(p)
{
}

void
StaticPolicy::regStats()
{
    Policy::regStats();
    
    stats.totalRequests
        .name(name() + ".total_requests")
        .desc("Total number of requests processed");
        
    stats.requestsPerPriority
        .init(256) // 8-bit priority values
        .name(name() + ".requests_per_priority")
        .desc("Number of requests per priority level");
        
    stats.latencyPerPriority
        .init(256)
        .name(name() + ".latency_per_priority")
        .desc("Average latency per priority level");
}

void
StaticPolicy::init()
{
    Policy::init();
}

void
StaticPolicy::setPriority(const RequestorID requestor_id, uint8_t priority)
{
    DPRINTF(QOS, "Setting priority %d for requestor %d\n", 
            priority, requestor_id);
    priorities[requestor_id] = priority;
}

uint8_t
StaticPolicy::schedule(const RequestorID requestor_id, const uint64_t data)
{
    uint8_t priority = 0;
    
    auto it = priorities.find(requestor_id);
    if (it != priorities.end()) {
        priority = it->second;
    }
    
    // Update statistics
    stats.totalRequests++;
    stats.requestsPerPriority[priority]++;
    
    DPRINTF(QOS, "Scheduling requestor %d with priority %d\n",
            requestor_id, priority);
            
    return priority;
}

DynamicPolicy::DynamicPolicy(const Params &p)
    : Policy(p),
      monitoringWindow(p.monitoring_window),
      lastUpdateTick(0),
      highBandwidthThreshold(p.high_bandwidth_threshold),
      lowBandwidthThreshold(p.low_bandwidth_threshold)
{
}

void
DynamicPolicy::regStats()
{
    Policy::regStats();
    
    stats.priorityUpdates
        .name(name() + ".priority_updates")
        .desc("Number of priority updates performed");
        
    stats.currentPriorities
        .init(256)
        .name(name() + ".current_priorities")
        .desc("Current priority levels for requestors");
        
    stats.bandwidthUtilization
        .init(256)
        .name(name() + ".bandwidth_utilization")
        .desc("Bandwidth utilization per requestor");
}

void
DynamicPolicy::init()
{
    Policy::init();
}

void
DynamicPolicy::updatePriorities()
{
    Tick currentTick = curTick();
    
    if ((currentTick - lastUpdateTick) < monitoringWindow) {
        return;
    }
    
    for (auto &pair : requestorStats) {
        RequestorID requestor_id = pair.first;
        RequestorStats &stats = pair.second;
        
        uint64_t bandwidth = stats.bandwidth;
        
        // Adjust priorities based on bandwidth usage
        if (bandwidth > highBandwidthThreshold) {
            // Decrease priority for high bandwidth consumers
            if (stats.currentPriority > 1) {
                stats.currentPriority--;
            }
        } else if (bandwidth < lowBandwidthThreshold) {
            // Increase priority for low bandwidth consumers
            if (stats.currentPriority < 255) {
                stats.currentPriority++;
            }
        }
        
        // Update statistics
        this->stats.currentPriorities[requestor_id] = stats.currentPriority;
        this->stats.bandwidthUtilization[requestor_id] = bandwidth;
        
        // Reset counters
        stats.bandwidth = 0;
        stats.requestCount = 0;
        stats.totalLatency = 0;
    }
    
    lastUpdateTick = currentTick;
    stats.priorityUpdates++;
}

uint8_t
DynamicPolicy::schedule(const RequestorID requestor_id, const uint64_t data)
{
    Tick currentTick = curTick();
    
    // Initialize stats if needed
    if (requestorStats.find(requestor_id) == requestorStats.end()) {
        requestorStats[requestor_id] = {0, 0, 0, currentTick, 128}; // Default priority 128
    }
    
    RequestorStats &stats = requestorStats[requestor_id];
    
    // Update statistics
    stats.requestCount++;
    stats.bandwidth += data;
    stats.lastAccessTick = currentTick;
    
    // Check if we need to update priorities
    updatePriorities();
    
    DPRINTF(QOS, "Scheduling requestor %d with dynamic priority %d\n",
            requestor_id, stats.currentPriority);
            
    return stats.currentPriority;
}

} // namespace qos
} // namespace memory
} // namespace gem5