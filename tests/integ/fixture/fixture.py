import pytest
import toml
from multiprocessing import Pipe, Queue
from multiprocessing.connection import Connection
from typing import Any

@pytest.fixture
def base_config(tmp_path=""):
    with open("tests/integ/fixture/test_config.toml", "r") as f:
        config = toml.load(f)
    return config


def instance_layer(layer_class, config) -> tuple[Any, Connection, Connection, Queue]:
    pipe_out, pipe_in = Pipe(duplex=False)
    log_q = Queue()
    layer_obj = layer_class(config[layer_class.__name__], log_q)
    layer_obj.bind_input_pipe(pipe_out)
    pipe_out = layer_obj.output_pipe

    return layer_obj, pipe_in, pipe_out, log_q
