#include "Robot.h"

#include <frc2/command/CommandScheduler.h>

void Robot::RobotPeriodic() {
  frc2::CommandScheduler::GetInstance().Run();  // runs VoiceControl::Periodic()
}

#ifndef RUNNING_FRC_TESTS
int main() {
  return frc::StartRobot<Robot>();
}
#endif
