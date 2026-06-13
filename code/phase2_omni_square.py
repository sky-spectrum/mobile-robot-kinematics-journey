"""
Phase 2 — Mecanum omnidirectional rotation-less square
========================================================
Drives a square WITHOUT rotating. Robot heading stays the same throughout.

Robot: Neobotix MPO-500 (mecanum)
Run:
    ros2 launch phase2_pkg omni_square.launch.py

Key trick:
    angular.z is NEVER set. Direction is changed by switching which of
    linear.x and linear.y is used (and its sign).
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class OmniSquare(Node):

    def __init__(self):
        super().__init__('omni_square')
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)

        # Direction state — 4 sides, no rotation between them
        self.state = 'FORWARD'
        self.state_start = self.get_clock().now()
        self.side_count = 0

        self.speed = 0.2
        self.side_duration = 3.0

        self.get_logger().info('=== Omni Square Started ===')
        self.get_logger().info('Robot moves in a square WITHOUT rotating!')

    def timer_callback(self):
        elapsed = (self.get_clock().now() - self.state_start).nanoseconds / 1e9
        msg = Twist()

        # Note: msg.angular.z is NEVER set. Heading is preserved.
        if self.state == 'FORWARD':
            msg.linear.x = self.speed
        elif self.state == 'LEFT':
            msg.linear.y = self.speed
        elif self.state == 'BACKWARD':
            msg.linear.x = -self.speed
        elif self.state == 'RIGHT':
            msg.linear.y = -self.speed

        self.pub.publish(msg)

        if self.state != 'DONE' and elapsed >= self.side_duration:
            self.side_count += 1
            self.get_logger().info(f'Side {self.side_count}/4 ({self.state}) done')

            transitions = {
                'FORWARD': 'LEFT',
                'LEFT': 'BACKWARD',
                'BACKWARD': 'RIGHT',
                'RIGHT': 'FORWARD',
            }

            if self.side_count >= 4:
                self.state = 'DONE'
                self.get_logger().info(
                    '=== Omni Square completed! Robot still facing original direction ===')
            else:
                self.state = transitions[self.state]
                self.state_start = self.get_clock().now()


def main(args=None):
    rclpy.init(args=args)
    node = OmniSquare()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
