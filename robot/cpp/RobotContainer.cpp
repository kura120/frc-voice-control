#include "RobotContainer.h"

#include <frc2/command/Commands.h>

RobotContainer::RobotContainer() {
  ConfigureVoiceCommands();
}

void RobotContainer::ConfigureVoiceCommands() {
  // Replace these with your real commands.
  m_voice.BindCommand("INTAKE", frc2::cmd::Print("INTAKE"));
  m_voice.BindCommand("SHOOT", frc2::cmd::Print("SHOOT"));
  m_voice.BindCommand("CLIMB", frc2::cmd::Print("CLIMB"));
  // "STOP" is pre-bound to CancelAll(); override with m_voice.Bind("STOP", ...) if needed.
}
