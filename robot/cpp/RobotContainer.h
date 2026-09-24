#pragma once

#include "subsystems/VoiceControl.h"

/// Example container. Keep yours; you only need the VoiceControl lines.
class RobotContainer {
 public:
  RobotContainer();

 private:
  void ConfigureVoiceCommands();

  VoiceControl m_voice;
};
