package frc.robot;

import edu.wpi.first.wpilibj2.command.Commands;
import frc.robot.subsystems.VoiceControl;

/** Example container. Keep yours; you only need the VoiceControl lines. */
public class RobotContainer {
  private final VoiceControl voice = new VoiceControl();

  public RobotContainer() {
    configureVoiceCommands();
  }

  private void configureVoiceCommands() {
    // Replace these with your real commands.
    voice.bindCommand("INTAKE", Commands.print("INTAKE"));
    voice.bindCommand("SHOOT", Commands.print("SHOOT"));
    voice.bindCommand("CLIMB", Commands.print("CLIMB"));
    // "STOP" is pre-bound to cancelAll(); override with voice.bind("STOP", ...) if needed.
  }
}
