import m5
from m5.objects import *
from m5.util import addToPath
from optparse import OptionParser
import os
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

def compile_test_program():
    os.system("gcc -static -o qos_test qos_test.c")

def create_test_process(cmd, idx):
    process = Process()
    process.cmd = [cmd]
    process.pid = 100 + idx
    return process

def configureQoSPolicy(system, options):
    if options.dynamic_qos:
        system.mem_ctrl.qos_policy = DynamicQoSPolicy()
        system.mem_ctrl.qos_policy.monitoring_window = 100000  # 100k ticks
        system.mem_ctrl.qos_policy.high_bandwidth_threshold = 1000000  # 1MB/s
        system.mem_ctrl.qos_policy.low_bandwidth_threshold = 100000    # 100KB/s
    else:
        system.mem_ctrl.qos_policy = StaticQoSPolicy()
        # We'll set the priorities after instantiation

def createSystem(options):
    system = System()
    
    # Set up clock domain
    system.clk_domain = SrcClockDomain()
    system.clk_domain.clock = '2GHz'
    system.clk_domain.voltage_domain = VoltageDomain()
    
    # Create CPUs (using fewer CPUs for demonstration)
    system.cpu = [TimingSimpleCPU() for i in range(4)]
    
    # Create memory bus
    system.membus = SystemXBar()
    
    # Configure caches and connect them
    for i, cpu in enumerate(system.cpu):
        # Create L1 caches
        cpu.icache = L1ICache()
        cpu.dcache = L1DCache()
        
        # Connect cache ports
        cpu.icache_port = cpu.icache.cpu_side
        cpu.dcache_port = cpu.dcache.cpu_side
        
        # Connect caches to memory bus
        cpu.icache.mem_side = system.membus.cpu_side_ports
        cpu.dcache.mem_side = system.membus.cpu_side_ports
        
        # Create process for each CPU
        cpu.workload = create_test_process('./qos_test', i)
        cpu.createThreads()
    
    # Create memory controller
    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR4_2400_16x4()
    system.mem_ctrl.dram.range = AddrRange('2GB')
    
    # Configure QoS policy
    configureQoSPolicy(system, options)
    
    # Connect memory controller
    system.mem_ctrl.port = system.membus.mem_side_ports
    
    return system

def runSimulation(options):
    # Compile the test program
    compile_test_program()
    
    # Create and configure the system
    system = createSystem(options)
    root = Root(full_system=False, system=system)
    
    # Instantiate the simulation
    m5.instantiate()
    
    # Set static priorities after instantiation if using static QoS
    if not options.dynamic_qos:
        priorities = {
            0: 50,   # Low priority
            1: 100,  # Medium priority
            2: 150,  # High priority
            3: 200   # Very high priority
        }
        for cpu_id, priority in priorities.items():
            system.mem_ctrl.qos_policy.setPriority(f"cpu{cpu_id}", priority)
    
    print("\nStarting simulation...")
    print(f"QoS Policy: {'Dynamic' if options.dynamic_qos else 'Static'}")
    
    # Run simulation
    exit_event = m5.simulate(options.max_ticks)
    print('\nExited @ tick {} because {}'
          .format(m5.curTick(), exit_event.getCause()))

if __name__ == "__m5_main__":
    parser = OptionParser()
    parser.add_option("--dynamic-qos", action="store_true",
                     default=False, help="Use dynamic QoS policy")
    parser.add_option("--max-ticks", type="int", default=10000000,
                     help="Maximum number of ticks to simulate")
    
    (options, args) = parser.parse_args()
    runSimulation(options)