import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow import keras
import os, json
import h5py

##################################### CNN Model `batch_shape` to `batch_input_shape` Helper Function #####################################

def _replace_batch_shape(obj):
  """Recursively replace 'batch_shape' -> 'batch_input_shape' in a nested dict/list."""
  if isinstance(obj, dict):
    new = {}
    for k, v in obj.items():
      nk = "batch_input_shape" if k == "batch_shape" else k
      new[nk] = _replace_batch_shape(v)
    return new
  if isinstance(obj, list):
    return [_replace_batch_shape(x) for x in obj]
  return obj

def patch_h5_batch_shape(in_path):
  """
  Creates a patched copy of an H5 model where InputLayer config key
  'batch_shape' is replaced with 'batch_input_shape'.
  Returns the patched path (or original if no patch needed).
  """
  # `connect4.py` patch function output path
  os.makedirs("/app/model_cache", exist_ok=True)
  base = os.path.basename(in_path).replace(".h5", "_patched.h5")
  out_path = os.path.join("/app/model_cache", base)

  if os.path.exists(out_path):
    return out_path

  with h5py.File(in_path, "r") as f:
    if "model_config" not in f.attrs:
      return in_path
    raw = f.attrs["model_config"]
    if isinstance(raw, bytes):
      raw = raw.decode("utf-8")
    cfg = json.loads(raw)

  # Patch config
  cfg2 = _replace_batch_shape(cfg)

  # If nothing changed, don't write a new file
  if json.dumps(cfg, sort_keys=True) == json.dumps(cfg2, sort_keys=True):
    return in_path

  # Copy file then update model_config attr
  import shutil
  shutil.copy2(in_path, out_path)

  with h5py.File(out_path, "r+") as f:
    f.attrs["model_config"] = json.dumps(cfg2).encode("utf-8")

  return out_path


##################################### Define Game Logic #####################################

def find_legal(board):
    """Find legal moves"""
    legal = [i for i in range(7) if abs(board[0,i]) < 0.1]
    return legal

##################################### Player Types Class ###################################

class PatchedBatchNormalization(tf.keras.layers.BatchNormalization):
    def __init__(self, *args, **kwargs):
        # Older TF/Keras doesn't know this arg
        kwargs.pop("synchronized", None)
        super().__init__(*args, **kwargs)

class CNNPlayer:
    """Your CNN model player"""

    def __init__(self, model_path):
        print(f"Loading CNN model from {model_path}...")

        # Ensure we don't use mixed precision when loading/running inference
        tf.keras.mixed_precision.set_global_policy("float32")

        patched_path = patch_h5_batch_shape(model_path)

        self.model = keras.models.load_model(
            patched_path,
            compile=False,
            custom_objects={
                "DTypePolicy": tf.keras.mixed_precision.Policy,
                "BatchNormalization": PatchedBatchNormalization
            }
        )


        print("✓ CNN loaded!")

    def board_to_input(self, board, player='plus'):
        """Convert board to CNN input format"""
        if player == 'minus':
            board = -board

        board_input = np.zeros((1, 6, 7, 2), dtype=np.float32)
        board_input[0, :, :, 0] = (board == 1).astype(np.float32)
        board_input[0, :, :, 1] = (board == -1).astype(np.float32)

        return board_input

    def get_move(self, board, color='plus'):
        """Get CNN's recommended move"""
        legal = find_legal(board)
        if len(legal) == 0:
            return None

        board_input = self.board_to_input(board, color)
        predictions = self.model.predict(board_input, verbose=0)[0]

        masked_predictions = np.full(7, -np.inf)
        masked_predictions[legal] = predictions[legal]

        return int(np.argmax(masked_predictions))