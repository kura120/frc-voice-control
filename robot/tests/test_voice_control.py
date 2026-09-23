import unittest
from unittest.mock import MagicMock, patch
from subsystems.voice_control import VoiceControlSubsystem

class TestVoiceControl(unittest.TestCase):
    @patch('ntcore.NetworkTableInstance.getDefault')
    def setUp(self, mock_nt_instance):
        """Sets up a voice control subsystem with mocked NetworkTables."""
        # Stub out NetworkTables interactions
        self.mock_table = MagicMock()
        mock_nt_instance.return_value.getTable.return_value = self.mock_table
        
        # Instantiate subsystem
        self.voice_subsystem = VoiceControlSubsystem()
        
        # Tracks if our mock action gets called
        self.action_called = False

    def sample_callback(self):
        """A dummy action to bind to a voice command."""
        self.action_called = True

    def test_command_registration(self):
        """Verifies that phrases are correctly normalized and registered."""
        self.voice_subsystem.register_command("  Intake Cube  ", self.sample_callback)
        
        # Core check: It should lowercase and trim the key automatically
        self.assertIn("intake cube", self.voice_subsystem.command_registry)

    def test_periodic_trigger_on_heartbeat_change(self):
        """Ensures that changing the heartbeat fires the command exactly once."""
        self.voice_subsystem.register_command("stop", self.sample_callback)
        
        # Simulate NetworkTables pushing a new heartbeat index and command string
        self.voice_subsystem.heartbeat_subscriber.get = MagicMock(return_value=1)
        self.voice_subsystem.asr_subscriber.get = MagicMock(return_value="stop")
        
        # Call periodic loop execution
        self.voice_subsystem.periodic()
        
        # Verify the command handler executed our method successfully
        self.assertTrue(self.action_called)
        self.assertEqual(self.voice_subsystem.last_heartbeat, 1)

if __name__ == '__main__':
    unittest.main()
