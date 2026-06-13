"""
Phase 1 — Differential Drive square pattern
=============================================
Drives a 4-sided square: GO_STRAIGHT → TURN → repeat × 4.

Robot: Turtlebot3 Waffle Pi (or any differential drive)
Run:
    ros2 launch phase1_pkg square_drive.launch.py

Notes:
    The square is intentionally open-loop time-based. Errors accumulate.
    To make it closed-loop, subscribe to /odom and use yaw feedback to
    detect when each 90-degree rotation is complete.
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class SquareDrive(Node):

    def __init__(self):
        super().__init__('square_drive')
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)

        # State machine
        self.state = 'GO_STRAIGHT'
        self.state_start = self.get_clock().now()
        self.side_count = 0

        # Parameters
        self.linear_speed = 0.2       # m/s
        self.angular_speed = 0.5      # rad/s
        self.straight_duration = 3.0  # seconds per side
        # 90 degrees at angular_speed
        self.turn_duration = 3.14159 / 2 / self.angular_speed

        self.get_logger().info(
            f'Square: side={self.linear_speed * self.straight_duration:.2f}m, '
            f'turn={self.turn_duration:.2f}s'
        )

    def timer_callback(self):
        elapsed = (self.get_clock().now() - self.state_start).nanoseconds / 1e9
        msg = Twist()

        if self.state == 'GO_STRAIGHT':
            msg.linear.x = self.linear_speed
            if elapsed >= self.straight_duration:
                self.get_logger().info(f'Side {self.side_count + 1}/4 done. Turning...')
                self.state = 'TURN'
                self.state_start = self.get_clock().now()

        elif self.state == 'TURN':
            msg.angular.z = self.angular_speed
            if elapsed >= self.turn_duration:
                self.side_count += 1
                if self.side_count >= 4:
                    self.state = 'DONE'
                    self.get_logger().info('Square completed! Stopping.')
                else:
                    self.state = 'GO_STRAIGHT'
                self.state_start = self.get_clock().now()

        elif self.state == 'DONE':
            pass

        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SquareDrive()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
