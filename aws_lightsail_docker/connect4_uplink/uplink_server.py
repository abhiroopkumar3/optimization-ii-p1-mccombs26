import os
import anvil.server
import numpy as np

from connect4 import CNNPlayer

MODEL_DIR = os.getenv("MODEL_DIR", "/models")
CNN_PATH = os.path.join(MODEL_DIR, "CNN_v2_deep_best.h5")

cnn_player = None

def get_player():
  global cnn_player
  if cnn_player is None:
    cnn_player = CNNPlayer(CNN_PATH)
  return cnn_player

@anvil.server.callable
def bot_move(model_type, board, human_col=None):
  # model_type is ignored here (CNN container only)

  if human_col is not None:
    print(f"Human played {int(human_col)}")

  player = get_player()
  board_np = np.array(board, dtype=np.float32)
  col = player.get_move(board_np, color="minus")

  if col is None:
    print("CNN Bot played None")
    return None

  print(f"CNN Bot played {int(col)}")
  return int(col)

def main():
  key = os.getenv("ANVIL_UPLINK_KEY")
  if not key:
    raise RuntimeError("Missing ANVIL_UPLINK_KEY env var")

  anvil.server.connect(key)
  print("✅ CNN uplink connected. Waiting for calls...")
  anvil.server.wait_forever()

if __name__ == "__main__":
  main()
