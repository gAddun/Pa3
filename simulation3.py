'''
Giovany Addun
Steven Thompson

Changes:
-Modified objects to reflect structure of network
-Created rt, a routing table. Represented as a python dictionary where the keys are tuples of (src_addr, dst_addr)
    rt is passed to routers at instantiation
-Modified messages so that host_1 send traffic to host_3 and host_2 send traffic to host_4
-Incerased simulation time
'''
import network3
import link3
import threading
from time import sleep

##configuration parameters
router_queue_size = 0  # 0 means unlimited
simulation_time = 3  # give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = []  # keeps track of objects, so we can kill their threads
    # routing tables represented as python dictionary
    # keys are tuples of (src_addr, dst_addr) and values are out_interfaces
    rt = {(1,3): 0, (1,4): 1, (2,3) : 0, (2, 4): 1}

    # create network nodes
    host_1 = network3.Host(1)
    object_L.append(host_1)
    host_2 = network3.Host(2)
    object_L.append(host_2)
    host_3 = network3.Host(3)
    object_L.append(host_3)
    host_4 = network3.Host(4)
    object_L.append(host_4)

    router_a = network3.Router(name='A', intf_count=2, max_queue_size=router_queue_size, routing_table=rt)
    object_L.append(router_a)
    router_b = network3.Router(name='B', intf_count=1, max_queue_size=router_queue_size, routing_table=rt)
    object_L.append(router_b)
    router_c = network3.Router(name='C', intf_count=1, max_queue_size=router_queue_size, routing_table=rt)
    object_L.append(router_c)
    router_d = network3.Router(name='D', intf_count=2, max_queue_size=router_queue_size, routing_table=rt)
    object_L.append(router_d)


    # create a Link Layer to keep track of links between network nodes
    link_layer = link3.LinkLayer()
    object_L.append(link_layer)

    # add all the links
    link_layer.add_link(link3.Link(host_1, 0, router_a, 0, 50))
    link_layer.add_link(link3.Link(host_2, 0, router_a, 1, 50))
    link_layer.add_link(link3.Link(router_a, 0, router_b, 0, 50))
    link_layer.add_link(link3.Link(router_a, 1, router_c, 0, 50))
    link_layer.add_link(link3.Link(router_b, 0, router_d, 0, 50))
    link_layer.add_link(link3.Link(router_c, 0, router_d, 1, 50))
    link_layer.add_link(link3.Link(router_d, 0, host_3, 0, 50))
    link_layer.add_link(link3.Link(router_d, 1, host_4, 0, 50))

    # start all the objects
    thread_L = []
    thread_L.append(threading.Thread(name=host_1.__str__(), target=host_1.run))
    thread_L.append(threading.Thread(name=host_2.__str__(), target=host_2.run))
    thread_L.append(threading.Thread(name=host_3.__str__(), target=host_3.run))
    thread_L.append(threading.Thread(name=host_4.__str__(), target=host_4.run))

    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))
    thread_L.append(threading.Thread(name=router_b.__str__(), target=router_b.run))
    thread_L.append(threading.Thread(name=router_c.__str__(), target=router_c.run))
    thread_L.append(threading.Thread(name=router_d.__str__(), target=router_d.run))

    thread_L.append(threading.Thread(name="Network", target=link_layer.run))

    for t in thread_L:
        t.start()

    # create some send events

    #send from host_1 to host_3
    mtu_into_network = link_layer.link_L[0].mtu
    host_1.udt_send(3, "In the time of chimpanzees I was a monkey\nButane in my veins so I'm out to cut the junkie", mtu_into_network)
    #send from host_2 to host_4
    sleep(simulation_time)
    host_2.udt_send(4, "'Twas brillig, and the slithy toves. Did gyre and gimble in the wabe", mtu_into_network)
    # give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)

    # join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()

    print("All simulation threads joined")



    # writes to host periodically