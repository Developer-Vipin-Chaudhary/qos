import m5
from m5.objects import *
from m5.util import addToPath
from optparse import OptionParser
import sys

# Cache configurations
class L1ICache(Cache):
    size = '32kB'
    assoc = 8
    tag_latency = 1
    data_latency = 1
    response_latency = 1
    mshrs = 16
    tgts_per_mshr = 20

class L1DCache(Cache):
    size = '32kB'
    assoc = 8
    tag_latency = 1
    data_latency = 1
    response_latency = 1
    mshrs = 16
    tgts_per_mshr = 20

class L2Cache(Cache):
    size = '256kB'
    assoc = 8
    tag_latency = 10
    data_latency = 10
    response_latency = 1
    mshrs = 20
    tgts_per_mshr = 12

def createQoSPolicy(options):
    if options.dynamic_qos:
        return DynamicQoSPolicy(
            monitoring_window = 100000,  # 100k ticks
            high_bandwidth_threshold = 1000000,  # 1MB/s
            low_bandwidth_threshold = 100000     # 100KB/s
        )
    else:
        policy = StaticQoSPolicy()
        policy.priorities = {
            'cpu0': 50,   # Low priority
            'cpu1': 100,  # Medium priority
            'cpu2': 150,  # Medium-high priority
            'cpu5': 200   # High priority
        }
        return policy

def createSystem(options):
    system = System()
    
    # Set up clock domain
    system.clk_domain = SrcClockDomain()
    system.clk_domain.clock = '2GHz'
    system.clk_domain.voltage_domain = VoltageDomain()
    
    # Create CPUs
    system.cpu = [TimingSimpleCPU() for i in range(8)]
    
    # Create memory bus
    system.membus = SystemXBar()
    
    # Configure caches and connect them
    for i, cpu in enumerate(system.cpu):
        # Create L1 caches
        cpu.icache = L1ICache()
        cpu.dcache = L1DCache()
        
        # Create cache ports
        cpu.icache_port = cpu.icache.cpu_side
        cpu.dcache_port = cpu.dcache.cpu_side
        
        # Connect caches to memory bus
        cpu.icache.mem_side = system.membus.cpu_side_ports
        cpu.dcache.mem_side = system.membus.cpu_side_ports
    
    # Create memory controller
    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR4_2400_16x4()
    system.mem_ctrl.dram.range = AddrRange('512MB')
    
    # Configure QoS policy
    system.mem_ctrl.qos_policy = createQoSPolicy(options)
    
    # Connect memory controller
    system.mem_ctrl.port = system.membus.mem_side_ports
    
    # Add a workload
    process = Process()
    process.cmd = ['hello']  # Replace with your actual workload
    for cpu in system.cpu:
        cpu.workload = process
        cpu.createThreads()
    
    return system

def runSimulation(options):
    system = createSystem(options)
    root = Root(full_system=False, system=system)
    
    # Instantiate the simulation
    m5.instantiate()
    
    # Now set the priorities after instantiation
    if not options.dynamic_qos:
        for cpu_name, priority in system.mem_ctrl.qos_policy.priorities.items():
            system.mem_ctrl.qos_policy.setPriority(cpu_name, priority)
    
    print("Starting simulation...")
    exit_event = m5.simulate(options.max_ticks)
    print('Exited @ tick {} because {}'
          .format(m5.curTick(), exit_event.getCause()))

if __name__ == "__m5_main__":
    parser = OptionParser()
    parser.add_option("--dynamic-qos", action="store_true",
                     default=False, help="Use dynamic QoS policy")
    parser.add_option("--max-ticks", type="int", default=1000000,
                     help="Maximum number of ticks to simulate")
    
    (options, args) = parser.parse_args()
    runSimulation(options)