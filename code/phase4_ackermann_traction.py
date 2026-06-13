"""
Phase 4 — Ackermann + Traction (4WD with front steering) kinematics calculator
================================================================================
For every cmd_vel sent, compute the 4 wheel speeds and 2 steering angles that
an actual Ackermann + Traction robot would need.

Robot: Neobotix MPO-700 (internally swerve, but we issue Ackermann-compatible cmds)
Run:
    ros2 launch phase4_pkg ackermann_traction.launch.py

Output:
    Real-time kinematic calculation logged per cmd_vel.

Equations:
    R_b = l / tan(φ)                              (turning radius)
    φ_left   = arctan(l / (R - w_f/2))            (inner front steer)
    φ_right  = arctan(l / (R + w_f/2))            (outer front steer)
    v_rear_left  = v · (R - w_r/2) / R            (inner rear speed)
    v_rear_right = v · (R + w_r/2) / R            (outer rear speed)
"""
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class AckermannTraction(Node):

    def __init__(self):
        super().__init__('ackermann_traction')

        # MPO-700 measured dimensions
        self.l = 0.480
        self.w_f = 0.450
        self.w_r = 0.450

        # Publisher for cmd_vel and subscriber to own messages
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.sub = self.create_subscription(
            Twist, 'cmd_vel', self.cmd_callback, 10)

        # Driving sequence
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.state = 'STRAIGHT'
        self.state_start = self.get_clock().now()
        self.last_logged = None

        self.get_logger().info('=== Phase 4 — Ackermann + Traction Calculator ===')
        self.get_logger().info(
            f'MPO-700: l={self.l}m, w_f={self.w_f}m, w_r={self.w_r}m')

    def calculate_ackermann_traction(self, v_x, w_z):
        """Compute 4-wheel speeds and 2 steering angles for an Ackermann+Traction robot."""
        if abs(w_z) < 1e-6:
            return dict(mode='STRAIGHT', R=float('inf'),
                        phi_L=0.0, phi_R=0.0,
                        v_FL=v_x, v_FR=v_x, v_RL=v_x, v_RR=v_x)
        if abs(v_x) < 1e-6:
            return dict(mode='IMPOSSIBLE')

        R = v_x / w_z
        phi_L = math.atan(self.l / (R - self.w_f / 2))
        phi_R = math.atan(self.l / (R + self.w_f / 2))
        v_RL = v_x * (R - self.w_r / 2) / R
        v_RR = v_x * (R + self.w_r / 2) / R
        # Front wheel speeds via arc-length approximation
        v_FL = v_x * math.sqrt(self.l**2 + (R - self.w_f / 2)**2) / R
        v_FR = v_x * math.sqrt(self.l**2 + (R + self.w_f / 2)**2) / R

        return dict(mode='TURNING', R=R,
                    phi_L=phi_L, phi_R=phi_R,
                    v_FL=v_FL, v_FR=v_FR, v_RL=v_RL, v_RR=v_RR)

    def cmd_callback(self, msg):
        # Throttle: only log when the cmd changes meaningfully
        key = (round(msg.linear.x, 2), round(msg.angular.z, 2))
        if key == self.last_logged:
            return
        self.last_logged = key

        r = self.calculate_ackermann_traction(msg.linear.x, msg.angular.z)

        if r['mode'] == 'STRAIGHT':
            self.get_logger().info(
                f'\n[STRAIGHT] cmd_vel: v_x={msg.linear.x:.2f}, ω_z=0.0'
                f'\n  All wheels equal speed = {r["v_FL"]:.3f} m/s, no steering'
            )
        elif r['mode'] == 'IMPOSSIBLE':
            self.get_logger().warn(
                f'\n[IMPOSSIBLE] cmd_vel: v_x=0, ω_z={msg.angular.z:.2f}'
                f'\n  Ackermann CANNOT do in-place rotation (would need φ=90°).'
            )
        else:
            self.get_logger().info(
                f'\n[TURNING] cmd_vel: v_x={msg.linear.x:+.2f}, ω_z={msg.angular.z:+.2f}'
                f'\n  Turning radius R = {r["R"]:+.3f} m'
                f'\n  Front Steer   L={math.degrees(r["phi_L"]):+6.1f}° | R={math.degrees(r["phi_R"]):+6.1f}°'
                f'\n  Front Wheel v L={r["v_FL"]:+.3f}    | R={r["v_FR"]:+.3f}  m/s'
                f'\n  Rear  Wheel v L={r["v_RL"]:+.3f}    | R={r["v_RR"]:+.3f}  m/s'
                f'\n  → rear left/right speed diff: {abs(r["v_RR"] - r["v_RL"]):.3f} m/s'
            )

    def timer_callback(self):
        """Drive a sequence: STRAIGHT → LEFT_TURN → RIGHT_TURN → repeat."""
        elapsed = (self.get_clock().now() - self.state_start).nanoseconds / 1e9
        msg = Twist()
        msg.linear.x = 0.3

        if self.state == 'STRAIGHT':
            msg.angular.z = 0.0
            if elapsed >= 3.0:
                self.state = 'LEFT_TURN'
                self.state_start = self.get_clock().now()
        elif self.state == 'LEFT_TURN':
            msg.angular.z = 0.3
            if elapsed >= 4.0:
                self.state = 'RIGHT_TURN'
                self.state_start = self.get_clock().now()
        elif self.state == 'RIGHT_TURN':
            msg.angular.z = -0.3
            if elapsed >= 4.0:
                self.state = 'STRAIGHT'
                self.state_start = self.get_clock().now()

        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = AckermannTraction()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
