'''
Created on Oct 12, 2016

@author: mwitt_000
'''
import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.mtu = None

    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None

    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)


## Implements a network layer packet (different from the RDT packet
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths
    dst_addr_S_length = 5
    src_addr_S_length = 5
    flag_length = 1
    offset_length = 2
    header_length = src_addr_S_length + dst_addr_S_length + flag_length + offset_length

    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    def __init__(self, src_addr, dst_addr, data_S, flag=0, offset=0):
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.flag = flag
        self.offset = offset

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.src_addr).zfill(self.src_addr_S_length)
        byte_S += str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += self.data_S
        return byte_S

    #convert a fragmented packet into a byte string
    def to_byte_S_frag(self):
        byte_S = str(self.src_addr).zfill(self.src_addr_S_length)
        byte_S += str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += str(self.flag).zfill(self.flag_length)
        byte_S += str(self.offset).zfill(self.offset_length)
        byte_S += self.data_S
        return byte_S

    #determine if a packet is a fragment
    @classmethod
    def is_fragment(self, byte_S):
        if byte_S[self.dst_addr_S_length] is '1':
            return True
        return False

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S, mtu):
        fragments = []
        src_addr = int(byte_S[0:NetworkPacket.src_addr_S_length])
        dst_addr = ((byte_S[5:10]))
        dst_addr = int(dst_addr)
        data_S = byte_S[NetworkPacket.dst_addr_S_length:]
        offset_size = 0
        while True:
            if((self.header_length+len(data_S[offset_size])>mtu)):
                frag_flag=1
            else:
                frag_flag=0
            fragments.append(self(src_addr, dst_addr, data_S[offset_size:offset_size + mtu - self.header_length], frag_flag, offset_size))
            offset_size = offset_size + mtu - self.header_length
            if(len(data_S[offset_size:])==0):
                break
        return fragments


## Implements a network host for receiving and transmitting data
class Host:
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False  # for thread termination
        self.frag_buffer = []

    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)

    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S, mtu):
        length = len(data_S)
        if(length<=mtu):
            pkt = NetworkPacket(self.addr, dst_addr, data_S)
            self.out_intf_L[0].put(pkt.to_byte_S())  # send packets always enqueued successfully
            print('{}: sending packet {}:'.format(self, pkt))
        else:
            #scale is the number of smaller packets that need to be made
            scale = (length // mtu)
            scale += 1
            for i in range(0, scale):
                #if this packet is the last segment
                if(i==scale-1):
                    pkt_segment = data_S[(i*mtu)-6:length]
                    pkt = NetworkPacket(self.addr, dst_addr, pkt_segment)
                    # send the packet segment
                    self.out_intf_L[0].put(pkt.to_byte_S())
                    print('{}: sending packet {}'.format(self, pkt))
                elif(i==0):
                    # segment the transmission into chunks the size of the mtu
                    print(i)
                    pkt_segment = data_S[(i * mtu):((i + 1) * mtu) - 6]
                    pkt = NetworkPacket(self.addr, dst_addr, pkt_segment)
                    # send the packet segment
                    self.out_intf_L[0].put(pkt.to_byte_S())
                    print('{}: sending packet {}'.format(self, pkt))
                else:
                    #segment the transmission into chunks the size of the mtu
                    print(i)
                    pkt_segment = data_S[(i*mtu)-6:((i+1)*mtu)-6]
                    pkt = NetworkPacket(dst_addr, pkt_segment)
                    #send the packet segment
                    self.out_intf_L[0].put(pkt.to_byte_S())
                    print('{}: sending packet {}'.format(self, pkt))


    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            self.frag_buffer.append(pkt_S[NetworkPacket.header_length:])
            if not NetworkPacket.is_fragment(pkt_S):
                print('{}: received packet "{}"'.format(self, ''.join(self.frag_buffer)))
                self.frag_buffer.clear()

    ## thread target for the host to keep receiving data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            # receive data arriving to the in interface
            self.udt_receive()
            # terminate
            if (self.stop):
                print(threading.currentThread().getName() + ': Ending')
                return


## Implements a multi-interface router described in class
class Router:
    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_count, max_queue_size, routing_table):
        self.intf_count = intf_count
        self.routing_table = routing_table
        self.stop = False  # for thread termination
        self.name = name
        # create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):

        for i in range(0, len(self.in_intf_L)):
            pkt_S = None
            try:
                # get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                # if packet exists make a forwarding decision
                if pkt_S is not None:
                    if (self.intf_count > 1):
                        out_intf = self.route(pkt_S)
                        mtu = self.out_intf_L[out_intf].mtu
                    else:
                        out_intf = 0
                        mtu = self.out_intf_L[out_intf].mtu
                    packets = NetworkPacket.from_byte_S(pkt_S, mtu)  # parse a packet out
                    # HERE you will need to implement a lookup into the
                    # forwarding table to find the appropriate outgoing interface
                    # for now we assume the outgoing interface is also i
                    for p in packets:
                        self.out_intf_L[out_intf].put(p.to_byte_S_frag(), True)
                        print('%s: forwarding packet "%s" from interface %d to %d with mtu %d' \
                              % (self, p, i, i, self.out_intf_L[out_intf].mtu))
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, i))
                pass

    ## thread target for the host to keep forwarding data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print(threading.currentThread().getName() + ': Ending')
                return

    #added route() method to determine how to forward packets.
    #examine's a packet's src_addr and dst_addr  to lookup the out_intf from a router's forwarding table
    def route(self, pkt_S):
        src_addr = int(pkt_S[0:5])
        dst_addr = pkt_S[5:10]
        dst_addr = int(dst_addr)
        lookup_tuple = (src_addr, dst_addr)
        out_intf = self.routing_table.get(lookup_tuple)
        return out_intf