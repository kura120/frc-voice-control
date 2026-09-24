#pragma once

#include <frc/TimedRobot.h>

#include "RobotContainer.h"

/// Minimal command-based Robot. Keep your generated Robot; nothing here is voice-specific.
class Robot : public frc::TimedRobot {
 public:
  void RobotPeriodic() override;

 private:
  RobotContainer m_container;
};
