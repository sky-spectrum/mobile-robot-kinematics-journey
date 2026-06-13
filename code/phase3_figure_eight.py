"""
Phase 3 — Ackermann figure-eight
==================================
Drives a figure-of-eight, the canonical Ackermann driving pattern.

Robot: Neobotix MPO-700 (using only Ackermann-compatible commands)
Run:
    ros2 launch phase3_pkg figure_eight.launch.py

Constraint discipline:
    linear.y is NEVER set. We pretend the robot cannot move sideways,
    even though internally it's swerve.

On startup the node also logs the steering angle that this command pair
would require IF the robot were truly Ackermann. The simulator does its
own thing, but the math is the learning goal.
"""
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class FigureEight(Node):

    def __init__(self):
        super().__init__('figure_eight')
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)

        # MPO-700 wheelbase (measured via tf2_echo)
        self.wheelbase = 0.480

        # Figure-eight parameters
        self.linear_speed = 0.3       # m/s
        self.angular_speed = 0.5      # rad/s
        self.half_loop_time = 4.0     # seconds per half-loop

        # State machine
        self.state = 'LEFT_TURN'
        self.state_start = self.get_clock().now()
        self.loop_count = 0

        # Kinematic prediction
        radius = self.linear_speed / self.angular_speed
        steering_predicted = math.atan(self.wheelbase / radius)

        self.get_logger().info('=== Figure 8 Drive ===')
        self.get_logger().info(f'Linear speed:  {self.linear_speed} m/s')
        self.get_logger().info(f'Angular speed: {self.angular_speed} rad/s')
        self.get_logger().info(f'Predicted radius:  R = v/ω = {radius:.3f} m')
        self.get_logger().info(
            f'Required steering: φ = arctan(l/R) = {math.degrees(steering_predicted):.1f}°'
        )
        self.get_logger().info('(Ackermann kinematics — the angle a real car would need)')

    def timer_callback(self):
        elapsed = (self.get_clock().now() - self.state_start).nanoseconds / 1e9
        msg = Twist()
        msg.linear.x = self.linear_speed
        # linear.y is NEVER set — Ackermann constraint!

        if self.state == 'LEFT_TURN':
            msg.angular.z = self.angular_speed
        elif self.state == 'RIGHT_TURN':
            msg.angular.z = -self.angular_speed
        elif self.state == 'DONE':
            msg.linear.x = 0.0
            msg.angular.z = 0.0

        self.pub.publish(msg)

        if self.state != 'DONE' and elapsed >= self.half_loop_time:
            self.loop_count += 1

            transitions = {
                'LEFT_TURN': 'RIGHT_TURN',
                'RIGHT_TURN': 'LEFT_TURN',
            }

            if self.loop_count >= 4:   # two full figure-eights
                self.state = 'DONE'
                self.get_logger().info('=== Figure 8 Completed ===')
            else:
                self.state = transitions[self.state]
                self.state_start = self.get_clock().now()


def main(args=None):
    rclpy.init(args=args)
    node = FigureEight()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
