'''
Giovany Addun
Steven Thompson

Changes:
changed MTU for second link to 30
'''
import network2
import link2
import threading
from time import sleep

##configuration parameters
router_queue_size = 0  # 0 means unlimited
simulation_time = 1.5  # give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = []  # keeps track of objects, so we can kill their threads

    # create network nodes
    client = network2.Host(1)
    object_L.append(client)
    server = network2.Host(2)
    object_L.append(server)
    router_a = network2.Router(name='A', intf_count=1, max_queue_size=router_queue_size)
    object_L.append(router_a)

    # create a Link Layer to keep track of links between network nodes
    link_layer = link2.LinkLayer()
    object_L.append(link_layer)

    # add all the links
    link_layer.add_link(link2.Link(client, 0, router_a, 0, 50))
    link_layer.add_link(link2.Link(router_a, 0, server, 0, 30))

    # start all the objects
    thread_L = []
    thread_L.append(threading.Thread(name=client.__str__(), target=client.run))
    thread_L.append(threading.Thread(name=server.__str__(), target=server.run))
    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))

    thread_L.append(threading.Thread(name="Network", target=link_layer.run))

    for t in thread_L:
        t.start()

    # create some send events
    mtu_into_network = link_layer.link_L[0].mtu
    client.udt_send(2, "In the time of chimpanzees I was a monkey\nButane in my veins so I'm out to cut the junkie", mtu_into_network)

    # give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)

    # join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()

    print("All simulation threads joined")



    # writes to host periodically