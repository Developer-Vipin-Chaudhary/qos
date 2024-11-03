#ifndef __MEM_QOS_CUSTOM_POLICY_HH__
#define __MEM_QOS_CUSTOM_POLICY_HH__

#include "mem/qos/policy.hh"
#include "params/StaticQoSPolicy.hh"
#include "params/DynamicQoSPolicy.hh"
#include "base/statistics.hh"
#include <map>
#include <queue>

namespace gem5 {

namespace memory {

namespace qos {

/**
 * Static QoS Policy implementation
 */
class StaticPolicy : public Policy {
  private:
    // Map to store static priorities for each requestor
    std::map<RequestorID, uint8_t> priorities;
    
    // Statistics
    struct StaticPolicyStats {
        statistics::Scalar totalRequests;
        statistics::Vector requestsPerPriority;
        statistics::Vector latencyPerPriority;
    } stats;

  public:
    using Params = StaticQoSPolicyParams;
    StaticPolicy(const Params &p);
    
    void regStats() override;
    
    void init() override;
    
    /**
     * Set priority for a specific requestor
     * @param requestor_id RequestorID to set priority for
     * @param priority Priority value (0-255, higher is more important)
     */
    void setPriority(const RequestorID requestor_id, uint8_t priority);
    
    /**
     * Schedule implementation for static policy
     */
    uint8_t schedule(const RequestorID requestor_id,
                    const uint64_t data) override;
};

/**
 * Dynamic QoS Policy implementation
 */
class DynamicPolicy : public Policy {
  private:
    // Structure to track requestor statistics
    struct RequestorStats {
        uint64_t requestCount;
        uint64_t totalLatency;
        uint64_t bandwidth;
        Tick lastAccessTick;
        uint8_t currentPriority;
    };
    
    // Map to store dynamic statistics for each requestor
    std::map<RequestorID, RequestorStats> requestorStats;
    
    // Monitoring window size in ticks
    const Tick monitoringWindow;
    
    // Last update tick
    Tick lastUpdateTick;
    
    // Bandwidth thresholds for priority adjustment
    const uint64_t highBandwidthThreshold;
    const uint64_t lowBandwidthThreshold;
    
    // Statistics
    struct DynamicPolicyStats {
        statistics::Scalar priorityUpdates;
        statistics::Vector currentPriorities;
        statistics::Vector bandwidthUtilization;
    } stats;
    
    /**
     * Update priorities based on monitored metrics
     */
    void updatePriorities();

  public:
    using Params = DynamicQoSPolicyParams;
    DynamicPolicy(const Params &p);
    
    void regStats() override;
    
    void init() override;
    
    /**
     * Schedule implementation for dynamic policy
     */
    uint8_t schedule(const RequestorID requestor_id,
                    const uint64_t data) override;
};

} // namespace qos
} // namespace memory
} // namespace gem5

#endif // __MEM_QOS_CUSTOM_POLICY_HH__