package frc.robot;

import edu.wpi.first.wpilibj.TimedRobot;
import edu.wpi.first.wpilibj2.command.CommandScheduler;

/** Minimal command-based Robot. Keep your generated Robot.java; nothing here is voice-specific. */
public class Robot extends TimedRobot {
  private final RobotContainer container = new RobotContainer();

  @Override
  public void robotPeriodic() {
    CommandScheduler.getInstance().run(); // runs VoiceControl.periodic()
  }
}
