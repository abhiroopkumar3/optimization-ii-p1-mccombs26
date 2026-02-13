import os
import anvil.server
import numpy as np
import tensorflow as tf

MODEL_DIR = os.getenv("MODEL_DIR", "/models")
TX_DIR = os.path.join(MODEL_DIR, "tx_savedmodel")

_loaded = None
_serving = None
_input_name = None
_output_name = None

def load_once():
  global _loaded, _serving, _input_name, _output_name
  if _loaded is not None:
    return

  print(f"Loading Transformer SavedModel from {TX_DIR}...")
  _loaded = tf.saved_model.load(TX_DIR)
  _serving = _loaded.signatures["serving_default"]

  # determine input/output tensor names
  _input_name = list(_serving.structured_input_signature[1].keys())[0]
  _output_name = list(_serving.structured_outputs.keys())[0]

  print("Using input:", _input_name)
  print("Using output:", _output_name)
  print("✓ Transformer SavedModel loaded!")

@anvil.server.callable
def bot_move_tx(board, human_col=None):
  load_once()

  if human_col is not None:
    print(f"Human played {int(human_col)}")

  board = np.array(board, dtype=np.float32)

  # Convert board -> (1,6,7,2)
  x = np.zeros((1, 6, 7, 2), dtype=np.float32)
  x[0, :, :, 0] = (board == 1).astype(np.float32)
  x[0, :, :, 1] = (board == -1).astype(np.float32)

  valid_cols = [c for c in range(7) if board[0, c] == 0]
  if not valid_cols:
    print("Transformer Bot played None")
    return None

  out = _serving(**{_input_name: tf.constant(x)})
  y = out[_output_name].numpy()[0]

  masked = np.full(7, -1e9, dtype=np.float32)
  masked[valid_cols] = y[valid_cols]
  bot_col = int(np.argmax(masked))

  print(f"Transformer Bot played {bot_col}")
  return bot_col

def main():
  key = os.getenv("ANVIL_UPLINK_KEY")
  if not key:
    raise RuntimeError("Missing ANVIL_UPLINK_KEY env var")

  anvil.server.connect(key)
  print("✅ TX uplink connected. Waiting for calls...")
  anvil.server.wait_forever()

if __name__ == "__main__":
  main()
