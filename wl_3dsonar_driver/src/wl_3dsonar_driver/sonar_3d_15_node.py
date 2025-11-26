#!/usr/bin/env python3
import threading
import socket
import struct
import os
import sys
import numpy as np
import netifaces

# sys.path.append(os.path.join(os.path.dirname(__file__)))
# from wl_api.sonar_3d_15_protocol_pb2 import RangeImage, BitmapImageGreyscale8
from wl_api.interface_sonar_api import set_speed, set_acoustics
from wl_api.inspect_sonar_data import handle_packet

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2, PointField
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header

try:
    from rcl_interfaces.msg import SetParametersResult
except ImportError:
    # Fallback for environments where rcl_interfaces is not available
    class SetParametersResult:
        def __init__(self, successful=True):
            self.successful = successful

# # Helper to parse RIP1 framing and extract RangeImage protobuf
# def parse_rip1_range_image(data):
#     if len(data) < 12:
#         raise ValueError("Packet too short for RIP1 framing")
#     magic, length, msg_type = struct.unpack('<4sII', data[:12])
#     if magic != b'RIP1':
#         raise ValueError("Invalid RIP1 magic")
#     if msg_type != 1:  # 1 = RangeImage
#         raise ValueError("Not a RangeImage message")
#     pb_data = data[12:12+length]
#     range_image = RangeImage()
#     range_image.ParseFromString(pb_data)
#     return range_image

class Sonar3D15Node(Node):
    def __init__(self):
        super().__init__('sonar_3d_15_node')
        self.declare_parameters(
            namespace='',
            parameters=[
                ('sonar_ip', '192.168.2.190'),#192.168.194.96#192.168.2.190
                ('speed_of_sound', 1480),
                ('acoustics_enabled', True),
                ('multicast_group', '224.0.0.96'),
                ('multicast_port', 4747),
                ('filter_ip', '192.168.2.190'),
            ]
        )
        self.get_logger().info('Sonar 3D-15 ROS2 node started.')
        self.sonar_ip = self.get_parameter('sonar_ip').get_parameter_value().string_value
        self.speed_of_sound = self.get_parameter('speed_of_sound').get_parameter_value().integer_value
        self.acoustics_enabled = self.get_parameter('acoustics_enabled').get_parameter_value().bool_value
        self.multicast_group = self.get_parameter('multicast_group').get_parameter_value().string_value
        self.multicast_port = self.get_parameter('multicast_port').get_parameter_value().integer_value
        self.filter_ip = self.get_parameter('filter_ip').get_parameter_value().string_value

        # MULTICAST_GROUP = '224.0.0.5' # Used when everything is in brovnet
        MULTICAST_GROUP = '224.0.0.96'  # Used when the sonar is connected to supernet and the laptop as well over wifi 
        
        # Register parameter change callback
        self.add_on_set_parameters_callback(self.parameter_callback)

        # Initial configuration
        self.configure_sonar()
        #Current settings is for unicast. Need some cleaning and also add a flag to do multicast. Coming sooon.
        interface_ip = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
        multicast_group = self.multicast_group
        port = self.multicast_port
        #self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)#multicast
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)#unicast
        #self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)#multicast
        #self.sock.bind(('', port))#multicast
        self.sock.bind((interface_ip, 6666))
        #group = socket.inet_aton(multicast_group)#multicast
        #If connected via ethernet
        #interface_ip = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']

        #If connected via wifi
        
        
        #mreq = struct.pack('4s4s', group, socket.inet_aton(interface_ip))#multicast
        #mreq = struct.pack('4sL', group, socket.INADDR_ANY) 
        #print(socket.INADDR_ANY)
        # mreq = struct.pack('4s4s', group, socket.inet_aton('192.168.32.33'))
        #self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)#multicast
        self.get_logger().info(f"Listening for Sonar 3D-15 UDP packets on {multicast_group}:{port}...")

        if self.filter_ip:
            self.get_logger().info(f"Filtering packets from IP: {self.filter_ip}")

        # Start UDP listening thread
        sample_time = 0.001          # sample time in seconds
        self.create_timer(sample_time, self.udp_listener)
        # self.udp_thread = threading.Thread(target=self.udp_listener, daemon=True)
        # self.udp_thread.start()

        self.image_pub = self.create_publisher(Image, 'sonar/depth_image', 10)
        self.intensity_pub = self.create_publisher(Image, 'sonar/intensity_image', 10)
        self.pointcloud_pub = self.create_publisher(PointCloud2, 'sonar/point_cloud', 10)

    def configure_sonar(self):
        if self.sonar_ip:
            try:
                # Use the imported API functions
                resp_speed = set_speed(self.sonar_ip, self.speed_of_sound)
                self.get_logger().info(f"Set speed_of_sound: {resp_speed.status_code}")
                resp_acoustics = set_acoustics(self.sonar_ip, self.acoustics_enabled)
                self.get_logger().info(f"Set acoustics_enabled: {resp_acoustics.status_code}")
            except Exception as e:
                self.get_logger().error(f"Failed to configure sonar: {e}")

    def parameter_callback(self, params):
        success = True
        for param in params:
            if param.name == 'speed_of_sound':
                self.speed_of_sound = param.value
                try:
                    resp = set_speed(self.sonar_ip, self.speed_of_sound)
                    self.get_logger().info(f"Updated speed_of_sound: {resp.status_code}")
                except Exception as e:
                    self.get_logger().error(f"Failed to update speed_of_sound: {e}")
                    success = False
            elif param.name == 'acoustics_enabled':
                self.acoustics_enabled = param.value
                try:
                    resp = set_acoustics(self.sonar_ip, self.acoustics_enabled)
                    self.get_logger().info(f"Updated acoustics_enabled: {resp.status_code}")
                except Exception as e:
                    self.get_logger().error(f"Failed to update acoustics_enabled: {e}")
                    success = False
            elif param.name == 'sonar_ip':
                self.sonar_ip = param.value
                self.configure_sonar()
            elif param.name == 'multicast_group':
                self.multicast_group = param.value
            elif param.name == 'multicast_port':
                self.multicast_port = param.value
            elif param.name == 'filter_ip':
                self.filter_ip = param.value
        return SetParametersResult(successful=success)

    def pack_cloud(self, frame, voxels):
        voxels_list = []
        for voxel in voxels:
            voxels_list.append([voxel["x"],voxel["y"],voxel["z"]])

        cloud = np.array(voxels_list).reshape(-1, 3)  
        sonar_cloud = PointCloud2()
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = frame
        fields = [PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
                PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
                PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1)]

        sonar_cloud = point_cloud2.create_cloud(header, fields, cloud)

        return sonar_cloud

    def udp_listener(self):
        buffer_size = 65535
        try:     
            # while rclpy.ok():
            data, addr = self.sock.recvfrom(buffer_size)
            if self.filter_ip and addr[0] != self.filter_ip:
                return
            self.get_logger().debug(f"Received {len(data)} bytes from {addr}")
            try:
                print("000000000000000")
                result = handle_packet(data)
                if result is None:
                    return
                msg_type, msg_obj, voxels = result
                if msg_type == "RangeImage":
                    print(msg_type)
                    # Convert to numpy array (float32)
                    img_np = np.array(msg_obj.image_pixel_data, dtype=np.float32).reshape((msg_obj.height, msg_obj.width))
                    img = np.flip(img_np, 0)

                    msg = Image()
                    msg.header.stamp = self.get_clock().now().to_msg()
                    msg.header.frame_id = "3d_link"
                    msg.height = msg_obj.height
                    msg.width = msg_obj.width
                    msg.encoding = "32FC1"
                    msg.is_bigendian = False
                    msg.step = img.strides[1]
                    msg.data = img.tobytes()
                    self.image_pub.publish(msg)

                    # Publish point cloud
                    sonar_cloud = self.pack_cloud("3d_link", voxels)
                    self.pointcloud_pub.publish(sonar_cloud)

                elif msg_type == "BitmapImageGreyscale8":
                    print(msg_type)
                    # Intensity image as 8UC1
                    img_list = [] 
                    for y in range(msg_obj.height-1, -1, -1): 
                        for x in range(msg_obj.width):
                            pixel_value = msg_obj.image_pixel_data[y * msg_obj.width + x]
                            # f.write(f"{pixel_value} ".encode())
                            img_list.append(pixel_value)
                    img_np = np.array(img_list, dtype=np.uint8).reshape((msg_obj.height, msg_obj.width))
                    
                    msg = Image()
                    msg.header.stamp = self.get_clock().now().to_msg()
                    msg.header.frame_id = "saabmarine/sonarlink"
                    msg.height = msg_obj.height
                    msg.width = msg_obj.width
                    msg.encoding = "8UC1"
                    msg.is_bigendian = False
                    msg.step = img_np.strides[0]
                    msg.data = img_np.tobytes()
                    self.intensity_pub.publish(msg)
            except Exception as e:
                self.get_logger().error(f"Failed to parse/publish sonar data: {e}")
        except Exception as e:
            self.get_logger().error(f"UDP listener error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = Sonar3D15Node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        #rclpy.shutdown()

if __name__ == '__main__':
    main()
