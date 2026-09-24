#include "subsystems/VoiceControl.h"

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <iostream>
#include <memory>
#include <set>
#include <utility>

#include <frc/DriverStation.h>
#include <frc/RobotController.h>
#include <frc/smartdashboard/SmartDashboard.h>
#include <frc2/command/CommandScheduler.h>
#include <networktables/NetworkTableInstance.h>

namespace {
constexpr double kMaxAgeSeconds = 1.0;  // ignore stale/delayed commands
constexpr bool kAllowOnFms = false;     // ignore voice on a real field
const std::set<std::string> kAlwaysAllowed{"STOP"};  // works even when disabled

std::string Upper(std::string s) {
  std::transform(s.begin(), s.end(), s.begin(),
                 [](unsigned char c) { return std::toupper(c); });
  return s;
}
}  // namespace

VoiceControl::VoiceControl() {
  auto table = nt::NetworkTableInstance::GetDefault().GetTable("VoiceControl");
  m_commandSub = table->GetStringTopic("command").Subscribe("");
  m_armedSub = table->GetBooleanTopic("armed").Subscribe(false);

  // Whatever is already on the topic at startup is old news: never run it.
  if (auto initial = Parse(m_commandSub.Get())) {
    m_lastSeq = initial->seq;
  }

  Bind("STOP", [] { frc2::CommandScheduler::GetInstance().CancelAll(); });
  Log(2, "ready (verbosity " + std::to_string(m_verbosity) + ")");
}

void VoiceControl::Bind(std::string name, std::function<void()> action) {
  name = Upper(std::move(name));
  Log(2, "bound " + name);
  m_actions[name] = std::move(action);
}

void VoiceControl::BindCommand(std::string name, frc2::CommandPtr command) {
  auto owned = std::make_shared<frc2::CommandPtr>(std::move(command));
  Bind(std::move(name),
       [owned] { frc2::CommandScheduler::GetInstance().Schedule(*owned); });
}

void VoiceControl::Log(int level, const std::string& message) const {
  if (m_verbosity >= level) {
    std::cout << "[CMD] " << message << std::endl;
  }
}

void VoiceControl::Report(const std::string& name,
                          const std::string& status) const {
  frc::SmartDashboard::PutString("Voice/Last", name + ": " + status);
  Log(1, name + " " + status);
}

std::optional<VoiceControl::Parsed> VoiceControl::Parse(const std::string& raw) {
  const auto colon = raw.find(':');
  if (colon == std::string::npos || colon + 1 >= raw.size()) {
    return std::nullopt;
  }
  try {
    return Parsed{std::stoll(raw.substr(0, colon)), Upper(raw.substr(colon + 1))};
  } catch (const std::exception&) {
    return std::nullopt;
  }
}

bool VoiceControl::IsAllowed(const std::string& name) {
  if (kAlwaysAllowed.count(name) > 0) {
    return true;
  }
  if (frc::DriverStation::IsFMSAttached() && !kAllowOnFms) {
    return false;
  }
  return frc::DriverStation::IsEnabled();
}

void VoiceControl::Periodic() {
  frc::SmartDashboard::PutBoolean("Voice/Armed", m_armedSub.Get());

  auto atomic = m_commandSub.GetAtomic();
  auto parsed = Parse(atomic.value);
  if (!parsed || parsed->seq == m_lastSeq) {
    return;
  }
  m_lastSeq = parsed->seq;

  // NT server time and FPGA time share a clock on the roboRIO.
  const double ageSeconds =
      static_cast<double>(
          static_cast<int64_t>(frc::RobotController::GetFPGATime()) -
          atomic.serverTime) /
      1e6;

  char buf[96];
  std::snprintf(buf, sizeof buf, "rx seq=%lld name=%s age=%.2fs",
                static_cast<long long>(parsed->seq), parsed->name.c_str(),
                ageSeconds);
  Log(2, buf);

  auto it = m_actions.find(parsed->name);
  if (ageSeconds > kMaxAgeSeconds) {
    std::snprintf(buf, sizeof buf, "stale (%.1fs)", ageSeconds);
    Report(parsed->name, buf);
  } else if (it == m_actions.end()) {
    Report(parsed->name, "unbound");
  } else if (!IsAllowed(parsed->name)) {
    Report(parsed->name, "blocked (disabled/FMS)");
  } else {
    it->second();
    Report(parsed->name, "executed");
  }
}