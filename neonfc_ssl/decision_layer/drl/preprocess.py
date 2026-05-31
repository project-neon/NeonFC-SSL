from typing import Optional, TYPE_CHECKING
import torch

from .transformations import get, available

if TYPE_CHECKING:
    from neonfc_ssl.tracking_layer.tracking_data import MatchData


class PreProcess:
    PERSISTENCE_KEY = "PERSISTENCE"

    def __init__(self, output_transformation: str, persistence_transformation: Optional[str] = None):
        self.__active_scripts = set()
        self.__script_model_index: dict[str, str] = {}
        self.__persistence_transformation = None

        self.__output_fn = get(output_transformation)
        if persistence_transformation:
            self.__persistence_transformation = get(persistence_transformation)
            self.__active_scripts.add(self.__persistence_transformation)

    def bind_model(self, model: str, script_name: str):
        """Associate a model with a transformation script."""
        script = get(script_name)
        self.__active_scripts.add(script)
        self.__script_model_index[model] = script

    def process(self, data: "MatchData") -> dict[str, torch.Tensor]:
        """Run every active script exactly once, broadcast to bound models,
        and snapshot persistence outputs."""
        processed: dict[str, torch.Tensor] = {}

        processed_raw = {}
        for script in self.__active_scripts:
            processed_raw[script] = script(data)

        for model, script in self.__script_model_index.items():
            processed[model] = processed_raw[script]

        if self.__persistence_transformation:
            processed[self.PERSISTENCE_KEY] = processed_raw[self.__persistence_transformation]

        return processed

    def get_persistence_outputs(self, data):
        if not self.__persistence_transformation:
            return

        return data[self.PERSISTENCE_KEY]

    def apply_output_transformation(self, actions: dict[str, torch.Tensor], match_data):
        if self.__output_fn is None:
            raise RuntimeError("No output transformation is configured.")
        return self.__output_fn(actions, match_data)
