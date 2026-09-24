from voicelink import config


def test_command_ids_are_unique():
    ids = list(config.COMMANDS.values())
    assert len(ids) == len(set(ids))


def test_phrases_are_lowercase():
    phrases = [*config.COMMANDS, config.ARM_PHRASE, config.DISARM_PHRASE]
    assert all(p == p.lower() for p in phrases)


def test_always_allowed_ids_exist():
    assert config.ALWAYS_ALLOWED <= set(config.COMMANDS.values())


def test_grammar_covers_every_phrase_and_unknown():
    grammar = config.grammar()
    assert "[unk]" in grammar
    for phrase in (*config.COMMANDS, config.ARM_PHRASE, config.DISARM_PHRASE):
        assert phrase in grammar


def test_control_phrases_do_not_collide_with_commands():
    assert config.ARM_PHRASE not in config.COMMANDS
    assert config.DISARM_PHRASE not in config.COMMANDS
