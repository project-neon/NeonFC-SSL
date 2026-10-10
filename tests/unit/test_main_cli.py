"""CLI overrides have to land on the keys the layers actually read.

`--color` used to write config["Tracking"]["Color"] while Tracking
looks up "color", so the flag silently did nothing.
"""

import argparse

from neonfc_ssl.main import apply_cli_overrides


def _args(color=None, side=None):
    return argparse.Namespace(color=color, side=side)


def _config():
    return {"Tracking": {"color": "yellow"}, "InputLayer": {"side": "left"}}


def test_color_override_reaches_the_key_tracking_reads():
    config = apply_cli_overrides(_config(), _args(color="blue"))

    assert config["Tracking"]["color"] == "blue"


def test_side_override_reaches_input_layer():
    config = apply_cli_overrides(_config(), _args(side="right"))

    assert config["InputLayer"]["side"] == "right"


def test_no_flags_leaves_the_profile_untouched():
    config = apply_cli_overrides(_config(), _args())

    assert config["Tracking"]["color"] == "yellow"
    assert config["InputLayer"]["side"] == "left"
