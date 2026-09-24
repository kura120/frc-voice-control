package frc.robot.subsystems;

import edu.wpi.first.networktables.BooleanSubscriber;
import edu.wpi.first.networktables.NetworkTable;
import edu.wpi.first.networktables.NetworkTableInstance;
import edu.wpi.first.networktables.StringSubscriber;
import edu.wpi.first.networktables.TimestampedString;
import edu.wpi.first.wpilibj.DriverStation;
import edu.wpi.first.wpilibj.RobotController;
import edu.wpi.first.wpilibj.smartdashboard.SmartDashboard;
import edu.wpi.first.wpilibj2.command.Command;
import edu.wpi.first.wpilibj2.command.CommandScheduler;
import edu.wpi.first.wpilibj2.command.SubsystemBase;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

/**
 * Voice command receiver. Reads "<seq>:<COMMAND>" from NetworkTables table "VoiceControl" and runs
 * whatever you bound to COMMAND. Construct one in RobotContainer and call bind()/bindCommand().
 */
public class VoiceControl extends SubsystemBase {
  private static final String TABLE_NAME = "VoiceControl";
  private static final double MAX_AGE_SECONDS = 1.0; // ignore stale/delayed commands
  private static final boolean ALLOW_ON_FMS = false; // ignore voice on a real field
  private static final Set<String> ALWAYS_ALLOWED = Set.of("STOP"); // works even when disabled

  /**
   * Console verbosity, printed as "[CMD] ...":
   *
   * <ul>
   *   <li>0 = silent
   *   <li>1 = one line per command outcome (executed / stale / unbound / blocked)
   *   <li>2 = also log every received value and every binding
   * </ul>
   */
  private static final int DEFAULT_VERBOSITY = 1;

  private record Parsed(long seq, String name) {}

  private final StringSubscriber commandSub;
  private final BooleanSubscriber armedSub;
  private final Map<String, Runnable> actions = new HashMap<>();
  private long lastSeq = Long.MIN_VALUE;
  private int verbosity = DEFAULT_VERBOSITY;

  public VoiceControl() {
    NetworkTable table = NetworkTableInstance.getDefault().getTable(TABLE_NAME);
    commandSub = table.getStringTopic("command").subscribe("");
    armedSub = table.getBooleanTopic("armed").subscribe(false);

    // Whatever is already on the topic at startup is old news: never run it.
    Parsed initial = parse(commandSub.get());
    if (initial != null) {
      lastSeq = initial.seq();
    }

    bind("STOP", () -> CommandScheduler.getInstance().cancelAll());
    log(2, "ready (verbosity " + verbosity + ")");
  }

  public void setVerbosity(int level) {
    verbosity = level;
  }

  /** Run {@code action} immediately when {@code name} is heard. */
  public void bind(String name, Runnable action) {
    actions.put(name.toUpperCase(), action);
    log(2, "bound " + name.toUpperCase());
  }

  /** Schedule {@code command} when {@code name} is heard. */
  public void bindCommand(String name, Command command) {
    bind(name, () -> CommandScheduler.getInstance().schedule(command));
  }

  private void log(int level, String message) {
    if (verbosity >= level) {
      System.out.println("[CMD] " + message);
    }
  }

  private void report(String name, String status) {
    SmartDashboard.putString("Voice/Last", name + ": " + status);
    log(1, name + " " + status);
  }

  private static Parsed parse(String raw) {
    int colon = raw.indexOf(':');
    if (colon < 0 || colon == raw.length() - 1) {
      return null;
    }
    try {
      return new Parsed(
          Long.parseLong(raw.substring(0, colon)), raw.substring(colon + 1).trim().toUpperCase());
    } catch (NumberFormatException e) {
      return null;
    }
  }

  private static boolean isAllowed(String name) {
    if (ALWAYS_ALLOWED.contains(name)) {
      return true;
    }
    if (DriverStation.isFMSAttached() && !ALLOW_ON_FMS) {
      return false;
    }
    return DriverStation.isEnabled();
  }

  @Override
  public void periodic() {
    SmartDashboard.putBoolean("Voice/Armed", armedSub.get());

    TimestampedString atomic = commandSub.getAtomic();
    Parsed parsed = parse(atomic.value);
    if (parsed == null || parsed.seq() == lastSeq) {
      return;
    }
    lastSeq = parsed.seq();

    // NT server time and FPGA time share a clock on the roboRIO.
    double ageSeconds = (RobotController.getFPGATime() - atomic.serverTime) / 1e6;
    log(2, String.format("rx seq=%d name=%s age=%.2fs", parsed.seq(), parsed.name(), ageSeconds));

    Runnable action = actions.get(parsed.name());
    if (ageSeconds > MAX_AGE_SECONDS) {
      report(parsed.name(), String.format("stale (%.1fs)", ageSeconds));
    } else if (action == null) {
      report(parsed.name(), "unbound");
    } else if (!isAllowed(parsed.name())) {
      report(parsed.name(), "blocked (disabled/FMS)");
    } else {
      action.run();
      report(parsed.name(), "executed");
    }
  }
}