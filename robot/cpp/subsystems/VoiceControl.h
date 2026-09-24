#pragma once

#include <cstdint>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>

#include <frc2/command/CommandPtr.h>
#include <frc2/command/SubsystemBase.h>
#include <networktables/BooleanTopic.h>
#include <networktables/StringTopic.h>

/**
 * Voice command receiver. Reads "<seq>:<COMMAND>" from NetworkTables table
 * "VoiceControl" and runs whatever you bound to COMMAND.
 */
class VoiceControl : public frc2::SubsystemBase {
 public:
  VoiceControl();

  void Periodic() override;

  /// Run `action` immediately when `name` is heard.
  void Bind(std::string name, std::function<void()> action);

  /// Schedule `command` when `name` is heard.
  void BindCommand(std::string name, frc2::CommandPtr command);

  /// Console verbosity, printed as "[CMD] ...":
  ///   0 = silent
  ///   1 = one line per command outcome (executed / stale / unbound / blocked)
  ///   2 = also log every received value and every binding
  void SetVerbosity(int level) { m_verbosity = level; }

 private:
  struct Parsed {
    int64_t seq;
    std::string name;
  };

  static std::optional<Parsed> Parse(const std::string& raw);
  static bool IsAllowed(const std::string& name);
  void Log(int level, const std::string& message) const;
  void Report(const std::string& name, const std::string& status) const;

  nt::StringSubscriber m_commandSub;
  nt::BooleanSubscriber m_armedSub;
  std::unordered_map<std::string, std::function<void()>> m_actions;
  std::optional<int64_t> m_lastSeq;
  int m_verbosity = 1;
};