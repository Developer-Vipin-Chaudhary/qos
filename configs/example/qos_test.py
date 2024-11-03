import m5
from m5.objects import *
from optparse import OptionParser
import os

# SE Mode process factory
def create_process(cmd, index):
    process = Process()
    process.cmd = [cmd, str(index)]
    return process

# Cache configurations
class L1Cache(Cache):
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20
    size = '32kB'

class L1ICache(L1Cache):
    pass

class L1DCache(L1Cache):
    pass

def createCPU(cpu_id, workload):
    # Create CPU
    cpu = TimingSimpleCPU()
    
    # Create L1 caches
    cpu.icache = L1ICache()
    cpu.dcache = L1DCache()
    
    # Connect cache ports
    cpu.icache_port = cpu.icache.cpu_side
    cpu.dcache_port = cpu.dcache.cpu_side
    
    # Set workload
    cpu.workload = workload
    
    return cpu

def createSystem(options):
    system = System()

    # Set up clock domain
    system.clk_domain = SrcClockDomain()
    system.clk_domain.clock = '2GHz'
    system.clk_domain.voltage_domain = VoltageDomain()

    # Create memory bus
    system.membus = SystemXBar()

    # Create CPUs and their caches
    system.cpu = [createCPU(i, create_process('tests/test-progs/qos-test/qos_test', i)) for i in range(4)]

    # Connect CPU caches to membus
    for cpu in system.cpu:
        cpu.icache.mem_side = system.membus.cpu_side_ports
        cpu.dcache.mem_side = system.membus.cpu_side_ports
        cpu.createThreads()

    # Create and configure memory controller
    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR4_2400_16x4()
    system.mem_ctrl.dram.range = AddrRange('2GB')
    system.mem_ctrl.port = system.membus.mem_side_ports

    # Connect system components
    system.system_port = system.membus.cpu_side_ports

    # Configure QoS policy
    if options.dynamic_qos:
        system.mem_ctrl.qos_policy = DynamicQoSPolicy()
        system.mem_ctrl.qos_policy.monitoring_window = 100000
        system.mem_ctrl.qos_policy.high_bandwidth_threshold = 1000000
        system.mem_ctrl.qos_policy.low_bandwidth_threshold = 100000
    else:
        system.mem_ctrl.qos_policy = StaticQoSPolicy()

    return system

def runSimulation(options):
    system = createSystem(options)
    root = Root(full_system=False, system=system)
    
    # Instantiate simulation
    m5.instantiate()
    
    # Set static priorities if using static QoS
    if not options.dynamic_qos:
        priorities = {
            0: 50,   # Low priority
            1: 100,  # Medium priority
            2: 150,  # High priority
            3: 200   # Very high priority
        }
        for cpu_id, priority in priorities.items():
            system.mem_ctrl.qos_policy.setPriority(f"cpu{cpu_id}", priority)
    
    print(f"\nStarting simulation with {'Dynamic' if options.dynamic_qos else 'Static'} QoS...")
    
    # Run simulation
    exit_event = m5.simulate(options.max_ticks)
    print(f'\nExited @ tick {m5.curTick()} because {exit_event.getCause()}')

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--dynamic-qos", action="store_true",
                      default=False, help="Use dynamic QoS policy")
    parser.add_option("--max-ticks", type="int", default=10000000,
                      help="Maximum number of ticks to simulate")
    
    (options, args) = parser.parse_args()
    runSimulation(options)
