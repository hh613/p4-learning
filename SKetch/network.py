from p4utils.mininetlib.network_API import NetworkAPI

net = NetworkAPI()

# Network general options
net.setLogLevel('info')

# Network definition
net.addP4Switch('s1', cli_input='s1-commands.txt')
net.setP4SourceAll('p4src/cm-sketch.p4')

net.addHost('h1')
net.addHost('h2')
net.addHost("h3")
net.addHost("h4")

net.addLink("h1", "s1")
net.addLink("h2", "s1")
net.addLink("h3", "s1")
net.addLink("h4", "s1")

# Assignment strategy
net.mixed()

# Nodes general options
net.disablePcapDumpAll()
net.disableLogAll()
net.enableCli()
net.startNetwork()