from p4utils.utils.helper import load_topo
from p4utils.utils.sswitch_thrift_API import SimpleSwitchThriftAPI

def read_register():
    
    topo = load_topo('topology.json')
    sw_name = "s1"
    thrift_port = topo.get_thrift_port(sw_name)
    sswitch= SimpleSwitchThriftAPI(thrift_port)


    # 读取寄存器的值
    register_index = 1  # 假设key=1
    register_value = sswitch.register_read('box_register', register_index)
    print(f'value at box {register_index}: {register_value}')

if __name__ == "__main__":
    read_register()
