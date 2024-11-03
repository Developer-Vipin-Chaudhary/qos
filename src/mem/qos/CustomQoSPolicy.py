from m5.params import *
from m5.proxy import *
from m5.objects.QoSPolicy import QoSPolicy

class StaticQoSPolicy(QoSPolicy):
    type = 'StaticPolicy'
    cxx_header = 'mem/qos/custom_policy.hh'
    cxx_class = 'gem5::memory::qos::StaticPolicy'

class DynamicQoSPolicy(QoSPolicy):
    type = 'DynamicPolicy'
    cxx_header = 'mem/qos/custom_policy.hh'
    cxx_class = 'gem5::memory::qos::DynamicPolicy'
    
    monitoring_window = Param.Tick(1000000, "Window size for monitoring in ticks")
    high_bandwidth_threshold = Param.UInt64(1000000, "High bandwidth threshold in bytes")
    low_bandwidth_threshold = Param.UInt64(100000, "Low bandwidth threshold in bytes")