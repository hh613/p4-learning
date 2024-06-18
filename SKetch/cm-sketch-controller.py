import socket, struct, pickle, os
from p4utils.utils.helper import load_topo
from p4utils.utils.sswitch_thrift_API import *
from crc import Crc

crc32_polinomials = [0x04C11DB7, 0xEDB88320, 0xDB710641, 0x82608EDB, 0x741B8CD7, 0xEB31D82E,
                     0xD663B05, 0xBA0DC66B, 0x32583499, 0x992C1A4C, 0x32583499, 0x992C1A4C]


class CMSController(object):

    def __init__(self, sw_name, set_hash):

        self.topo = load_topo('topology.json')
        self.sw_name = sw_name
        self.set_hash = set_hash
        self.thrift_port = self.topo.get_thrift_port(sw_name)
        self.controller = SimpleSwitchThriftAPI(self.thrift_port)

        self.custom_calcs = self.controller.get_custom_crc_calcs()
        self.register_num =  len(self.custom_calcs)

        self.init()
        self.registers = []

    def init(self):
        if self.set_hash:
            self.set_crc_custom_hashes()
        self.create_hashes()

    def set_forwarding(self):
        self.controller.table_add("forwarding", "set_egress_port", ['1'], ['2'])
        self.controller.table_add("forwarding", "set_egress_port", ['2'], ['1'])

    def reset_registers(self):
        for i in range(self.register_num):
            self.controller.register_reset("sketch{}".format(i))

    def flow_to_bytestream(self, flow):
        return socket.inet_aton(flow[0]) + socket.inet_aton(flow[1]) + struct.pack(">HHB",flow[2], flow[3], 6)
    

    def set_crc_custom_hashes(self):
        i = 0
        for custom_crc32, width in sorted(self.custom_calcs.items()):
            self.controller.set_crc32_parameters(custom_crc32, crc32_polinomials[i], 0xffffffff, 0xffffffff, True, True)
            i+=1

    def create_hashes(self):
        self.hashes = []
        for i in range(self.register_num):
            self.hashes.append(Crc(32, crc32_polinomials[i], True, 0xffffffff, True, 0xffffffff))

    def read_registers(self):
        self.registers = []
        for i in range(self.register_num):
            self.registers.append(self.controller.register_read("sketch{}".format(i)))

    def get_cms(self, flow, mod):
        values = []
        min_value = float('inf')  # 初始化最小值为正无穷大
        min_register_index = -1
        min_counter_index = -1
        for i in range(self.register_num):
            index = self.hashes[i].bit_by_bit_fast(self.flow_to_bytestream(flow)) % mod
            #values.append(self.registers[i][index])
            value = self.registers[i][index]
            if value < min_value:
               min_value = value
               min_register_index = i
               min_counter_index = index
        #return min(values)
      
        return min_value, min_register_index,min_counter_index

    '''def decode_registers(self, eps, n, mod, ground_truth_file="sent_flows.pickle"):

        """In the decoding function you were free to compute whatever you wanted.
           This solution includes a very basic statistic, with the number of flows inside the confidence bound.
        """
        self.read_registers()
        confidence_count = 0
        flows = pickle.load(open(ground_truth_file, "rb"))
        for flow, n_packets in flows.items():
            #cms = self.get_cms(flow, mod)
            cms, register_index, counter_index = self.get_cms(flow, mod)  # 获取计数器值及对应的寄存器和计数器索引
            print("Flow: {}, Packets sent: {}, CMS value: {} (Register: {}, Counter: {})".format(flow, n_packets, cms, register_index, counter_index))

           # print("Packets sent and read by the cms: {}/{}".format(n_packets, cms))
            if not (cms <(n_packets + (eps*n))):
                confidence_count +=1

        print("Not hold for {}%".format(float(confidence_count)/len(flows)*100))
        '''
    def decode_registers(self, eps, n, mod, ground_truth_file="sent_flows.pickle"):
        self.read_registers()
        confidence_count = 0
        flows = pickle.load(open(ground_truth_file, "rb"))
        for flow, n_packets in flows.items():
        # 获取计数器值及对应的寄存器和计数器索引
           cms, register_index, counter_index = self.get_cms(flow, mod)
        
        # 解包五元组
           src_ip, dst_ip, src_port, dst_port, proto = flow
        
        # 协议名称
           proto_name = "TCP" if proto == 6 else "UDP" if proto == 17 else "Unknown"
        
        # 打印五元组信息
           print(f"Flow: (Src IP: {src_ip}, Src Port: {src_port}, Dst IP: {dst_ip}, Dst Port: {dst_port}, Protocol: {proto_name}), Packets sent: {n_packets}, CMS value: {cms} (Register: {register_index}, Counter: {counter_index})")
        
           if not (cms < (n_packets + (eps * n))):
            confidence_count += 1

        #print("Not hold for {}%".format(float(confidence_count) / len(flows) * 100))




if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--sw', help="switch name to configure" , type=str, required=False, default="s1")
    parser.add_argument('--eps', help="epsilon to use when checking bound", type=float, required=False, default=0.01)
    parser.add_argument('--n', help="number of packets sent by the send.py app", type=int, required=False, default=1000)
    parser.add_argument('--mod', help="number of cells in each register", type=int, required=False, default=4096)
    parser.add_argument('--flow-file', help="name of the file generated by send.py", type=str, required=False, default="sent_flows.pickle")
    parser.add_argument('--option', help="controller option can be either set_hashes, decode or reset registers", type=str, required=False, default="set_hashes")
    args = parser.parse_args()

    set_hashes = args.option == "set_hashes"
    controller = CMSController(args.sw, set_hashes)

    if args.option == "decode":
        controller.decode_registers(args.eps, args.n, args.mod, args.flow_file)

    elif args.option == "reset":
        controller.reset_registers()
