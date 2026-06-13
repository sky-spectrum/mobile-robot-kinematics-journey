"""
Phase 5 — Swerve Drive kinematics + 6-step capability demo
============================================================
For every cmd_vel sent, compute the speed and steering angle for each of 4
swerve modules. Then automatically run a 6-step sequence showing all the
things swerve can do that simpler kinematics cannot.

Robot: Neobotix MPO-700 (true swerve)
Run:
    ros2 launch phase5_pkg swerve_kinematics.launch.py

Equations per module at body-frame position (l_x, l_y):
    v_i_x = v_b_x - ω_b_z · l_y
    v_i_y = v_b_y + ω_b_z · l_x
    v_i   = √(v_i_x² + v_i_y²)
    φ_i   = arctan2(v_i_y, v_i_x)

Sequence:
    1. STRAIGHT             (Phase 1 baseline)
    2. SIDEWAYS             (Phase 2 capability)
    3. DIAGONAL
    4. SIDEWAYS + ROTATE    (genuinely new)
    5. IN-PLACE ROTATION    (impossible in P3, P4)
    6. ALL 3 AXES           (full swerve)
"""
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class SwerveKinematics(Node):

    def __init__(self):
        super().__init__('swerve_kinematics')

        # MPO-700 module positions in base_link frame
        # (x: forward, y: left)
        self.modules = {
            'FL': (+0.240, +0.225),
            'FR': (+0.240, -0.225),
            'BL': (-0.240, +0.225),
            'BR': (-0.240, -0.225),
        }

        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.sub = self.create_subscription(
            Twist, 'cmd_vel', self.cmd_callback, 10)

        # 6-step capability demo sequence
        # (name, duration_s, linear.x, linear.y, angular.z)
        self.sequence = [
            ('1. STRAIGHT',           3.0, 0.3, 0.0, 0.0),
            ('2. SIDEWAYS',           3.0, 0.0, 0.3, 0.0),
            ('3. DIAGONAL',           3.0, 0.3, 0.3, 0.0),
            ('4. SIDEWAYS + ROTATE',  4.0, 0.0, 0.3, 0.3),
            ('5. IN-PLACE ROTATION',  3.0, 0.0, 0.0, 0.5),
            ('6. ALL 3 AXES',         4.0, 0.3, 0.2, 0.2),
            ('STOP',                  2.0, 0.0, 0.0, 0.0),
        ]
        self.seq_idx = 0
        self.state_start = self.get_clock().now()
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.last_logged = None

        self.get_logger().info('=== Phase 5 — Swerve Kinematics ===')
        for name, pos in self.modules.items():
            self.get_logger().info(
                f'  Module {name}: position ({pos[0]:+.3f}, {pos[1]:+.3f})')

    def calculate_swerve(self, v_x, v_y, w_z):
        results = {}
        for name, (lx, ly) in self.modules.items():
            v_ix = v_x - w_z * ly
            v_iy = v_y + w_z * lx
            v_i = math.sqrt(v_ix**2 + v_iy**2)
            phi_i = math.atan2(v_iy, v_ix) if v_i > 1e-6 else 0.0
            results[name] = (v_i, phi_i)
        return results

    def cmd_callback(self, msg):
        key = (round(msg.linear.x, 2), round(msg.linear.y, 2),
               round(msg.angular.z, 2))
        if key == self.last_logged:
            return
        self.last_logged = key

        results = self.calculate_swerve(
            msg.linear.x, msg.linear.y, msg.angular.z)

        log = (f'\n--- cmd_vel: v_x={msg.linear.x:+.2f}, '
               f'v_y={msg.linear.y:+.2f}, ω_z={msg.angular.z:+.2f} ---')
        for name in ['FL', 'FR', 'BL', 'BR']:
            v_i, phi_i = results[name]
            log += (f'\n  {name}: speed={v_i:.3f} m/s, '
                    f'steering={math.degrees(phi_i):+7.1f}°')
        self.get_logger().info(log)

    def timer_callback(self):
        if self.seq_idx >= len(self.sequence):
            return

        name, duration, vx, vy, wz = self.sequence[self.seq_idx]
        elapsed = (self.get_clock().now() - self.state_start).nanoseconds / 1e9

        if elapsed < 0.1:
            self.get_logger().info(f'\n>>> {name} for {duration}s <<<')

        msg = Twist()
        msg.linear.x = vx
        msg.linear.y = vy
        msg.angular.z = wz
        self.pub.publish(msg)

        if elapsed >= duration:
            self.seq_idx += 1
            self.state_start = self.get_clock().now()
            if self.seq_idx >= len(self.sequence):
                self.get_logger().info('=== All Swerve sequences completed ===')


def main(args=None):
    rclpy.init(args=args)
    node = SwerveKinematics()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
