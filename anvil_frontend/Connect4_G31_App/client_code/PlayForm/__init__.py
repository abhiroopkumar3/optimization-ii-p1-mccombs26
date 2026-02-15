from ._anvil_designer import PlayFormTemplate
from anvil import *
import anvil.server
import anvil.js
from anvil.js.window import navigator
import random
import time

ROWS, COLS = 6, 7

class PlayForm(PlayFormTemplate):

  def __init__(self, **properties):
    self.init_components(**properties)

    # --- Block mobile devices ---
    ua = (navigator.userAgent or "").lower()
    is_mobile = any(k in ua for k in ["android", "iphone", "ipad", "ipod", "mobile"])

    if is_mobile:
      alert(
        "This game is not optimized for mobile devices.\n"
        "Please use a laptop/desktop for the best experience.",
        title="Unsupported Device",
        buttons=[("OK", True)]
      )
      time.sleep(0.5)
      open_form("LoginForm")   # force logout / send to login
      return

    # --- Stats per difficulty ---
    self.stats = {
      "easy":   {"played": 0, "won": 0, "lost": 0, "drawn": 0, "no_result": 0},
      "medium": {"played": 0, "won": 0, "lost": 0, "drawn": 0, "no_result": 0},
    "hard":   {"played": 0, "won": 0, "lost": 0, "drawn": 0, "no_result": 0},
    }

    # Dropdown labels -> internal mode ids
    self.difficulty_map = {
      "Easy (Simple Bot)": "easy",
      "Medium (Transformer)": "medium",
      "Hard (CNN)": "hard"
    }

    # Dropdown setup
    if hasattr(self, "model_dropdown") and self.model_dropdown is not None:
      self.model_dropdown.items = list(self.difficulty_map.keys())
      self.model_dropdown.selected_value = "Easy (Simple Bot)"

    # Track which difficulty the CURRENT game belongs to (set on New Game)
    self.current_mode = None

    self.game_started = False
    self.game_over = False
    self._counted_this_game = False
    self._ui_locked = False  # prevents double-clicks while bot thinks

    self.board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    self.status_label.text = "Click 'New Game' to start."

    # Collect the 6x7 labels from row0_flow ... row5_flow
    self.grid = self._collect_grid_labels()
    self._style_grid_labels()
    self.render_board()

    # Initial stats display
    self.update_stats_text()

    # Ensure UI is enabled at start
    self.set_ui_enabled(True)

  # ---------------- UI LOCK/UNLOCK ----------------

  def set_ui_enabled(self, enabled: bool):
    """
    Disable/enable all interactive components while bot is thinking.
    """
    self._ui_locked = not enabled

    # Column buttons
    for i in range(COLS):
      btn_name = f"col{i}_button"
      if hasattr(self, btn_name):
        btn = getattr(self, btn_name)
        if btn is not None:
          btn.enabled = enabled

    # Other buttons (only if they exist on your form)
    for name in ["new_game_button", "end_game_button", "back_button", "logout_button"]:
      if hasattr(self, name):
        comp = getattr(self, name)
        if comp is not None:
          comp.enabled = enabled

    # Dropdown
    if hasattr(self, "model_dropdown") and self.model_dropdown is not None:
      self.model_dropdown.enabled = enabled

  # ---------------- UI HELPERS ----------------

  def _collect_grid_labels(self):
    grid = []
    for r in range(ROWS):
      row_flow_name = f"row{r}_flow"
      row_flow = getattr(self, row_flow_name)

      row_cells = [c for c in row_flow.get_components() if isinstance(c, Label)]
      if len(row_cells) != COLS:
        raise Exception(f"{row_flow_name} must contain exactly {COLS} Labels (found {len(row_cells)})")

      grid.append(row_cells)
    return grid

  def _style_grid_labels(self):
    size = 46

    for r in range(ROWS):
      for c in range(COLS):
        cell = self.grid[r][c]
        cell.text = ""
        cell.align = "center"
        cell.width = size
        cell.spacing_above = "none"
        cell.spacing_below = "none"
        cell.role = "connect4_cell"

  def render_board(self, highlight_cells=None):
    highlight_cells = set(highlight_cells or [])

    for r in range(ROWS):
      for c in range(COLS):
        cell = self.grid[r][c]
        v = self.board[r][c]

        if v == 0:
          cell.background = "#f2f2f2"
        elif v == +1:
          cell.background = "#f1c40f"
        else:
          cell.background = "#e74c3c"

        cell.border = "2px solid #333"
        if (r, c) in highlight_cells:
          cell.border = "5px solid #00ff00"

  # ---------------- GAME HELPERS ----------------

  def find_winner_cells(self, player):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for r in range(ROWS):
      for c in range(COLS):
        if self.board[r][c] != player:
          continue
        for dr, dc in directions:
          cells = [(r, c)]
          rr, cc = r, c
          for _ in range(3):
            rr += dr
            cc += dc
            if not (0 <= rr < ROWS and 0 <= cc < COLS):
              break
            if self.board[rr][cc] != player:
              break
            cells.append((rr, cc))
          if len(cells) == 4:
            return cells
    return None

  def board_full(self):
    return all(self.board[0][c] != 0 for c in range(COLS))

  def drop_piece(self, col, player):
    for r in range(ROWS - 1, -1, -1):
      if self.board[r][col] == 0:
        self.board[r][col] = player
        return True
    return False

  def bot_move_simple(self):
    if self.board_full():
      return None
    valid_cols = [c for c in range(COLS) if self.board[0][c] == 0]
    return random.choice(valid_cols) if valid_cols else None

  def _get_selected_mode(self):
    if not hasattr(self, "model_dropdown") or self.model_dropdown is None:
      return "hard"
    return self.difficulty_map.get(self.model_dropdown.selected_value, "hard")

  def show_end_popup(self, result):
    # Normalize
    if isinstance(result, str):
      result = result.strip().lower().replace(" ", "_")

    # Determine difficulty just played
    mode = self.current_mode or self._get_selected_mode()
    if mode not in self.stats:
      mode = "hard"

    mode_title = mode.upper()  # EASY / MEDIUM / HARD
    s = self.stats[mode]

    # Custom message by result
    msg_map = {
      "win": "🎉 You won!",
      "loss": "🤖 You lost!",
      "draw": "🤝 It's a draw!",
      "no_result": "⚠️ No Result (game ended early)."
    }
    msg = msg_map.get(result, "Game finished.")

    # Popup body (message + stats)
    popup_text = (
      f"{msg}\n\n"
      f"{mode_title}\n"
      f"  Played: {s['played']}\n"
      f"  Wins: {s['won']}\n"
      f"  Losses: {s['lost']}\n"
      f"  Draws: {s['drawn']}\n"
      f"  No Result: {s['no_result']}\n"
    )

    alert(popup_text, title="Game Result", buttons=[("OK", True)])

  # ---------------- STATS ----------------

  def update_stats_text(self):
    if hasattr(self, "stats_text_easy") and self.stats_text_easy is not None:
      s = self.stats["easy"]
      self.stats_text_easy.text = (
        f"  Played: {s['played']}  \n"
        f"  Wins: {s['won']}  \n"
        f"  Losses: {s['lost']}  \n"
        f"  Draws: {s['drawn']}  \n"
        f"  No Result: {s['no_result']}  \n"
      )

    if hasattr(self, "stats_text_medium") and self.stats_text_medium is not None:
      s = self.stats["medium"]
      self.stats_text_medium.text = (
        f"  Played: {s['played']}  \n"
        f"  Wins: {s['won']}  \n"
        f"  Losses: {s['lost']}  \n"
        f"  Draws: {s['drawn']}  \n"
        f"  No Result: {s['no_result']}  \n"
      )

    if hasattr(self, "stats_text_hard") and self.stats_text_hard is not None:
      s = self.stats["hard"]
      self.stats_text_hard.text = (
        f"  Played: {s['played']}  \n"
        f"  Wins: {s['won']}  \n"
        f"  Losses: {s['lost']}  \n"
        f"  Draws: {s['drawn']}  \n"
        f"  No Result: {s['no_result']}  \n"
      )

  def end_game(self, result):
    if isinstance(result, str):
      result = result.strip().lower().replace(" ", "_")

    if getattr(self, "_counted_this_game", False):
      return

    mode = self.current_mode or self._get_selected_mode()
    if mode not in self.stats:
      mode = "hard"

    self._counted_this_game = True
    self.game_over = True

    self.stats[mode]["played"] += 1
    if result == "win":
      self.stats[mode]["won"] += 1
    elif result == "loss":
      self.stats[mode]["lost"] += 1
    elif result == "draw":
      self.stats[mode]["drawn"] += 1
    elif result == "no_result":
      self.stats[mode]["no_result"] += 1

    self.update_stats_text()

  # ---------------- MAIN GAME LOOP ----------------

  def play_col(self, col):
    if self._ui_locked:
      return

    if not self.game_started:
      self.status_label.text = "Click 'New Game' first."
      return

    if self.game_over:
      self.status_label.text = "Game over. Click 'New Game' to start again."
      return

    if self.board[0][col] != 0:
      self.status_label.text = "That column is full."
      return

    # Human move
    self.drop_piece(col, +1)
    self.render_board()

    win_cells = self.find_winner_cells(+1)
    if win_cells:
      self.render_board(highlight_cells=win_cells)
      self.status_label.text = "🎉 You win! Click 'New Game' to play again."
      self.end_game("win")
      self.show_end_popup("win")
      return

    if self.board_full():
      self.status_label.text = "🤝 Draw! Click 'New Game' to play again."
      self.end_game("draw")
      return

    # Bot move
    mode = self.current_mode or self._get_selected_mode()
    self.status_label.text = "🤖 Bot thinking..."
    # Disable UI while waiting for bot response
    self.set_ui_enabled(False)
    time.sleep(0.5)

    try:
      if mode == "easy":
        bot_col = self.bot_move_simple()
      elif mode == "medium":
        bot_col = anvil.server.call("bot_move_tx", self.board, col) # ✅ pass human col 
      else:
        bot_col = anvil.server.call("bot_move", "CNN", self.board, col) # ✅ pass human col
    finally:
      # Always re-enable UI even if bot call errors
      self.set_ui_enabled(True)

    if bot_col is None:
      self.status_label.text = "🤝 Draw! Click 'New Game' to play again."
      self.end_game("draw")
      return

    if not (0 <= int(bot_col) < COLS) or self.board[0][int(bot_col)] != 0:
      self.status_label.text = "⚠️ Bot returned an invalid move. Ending game as No Result."
      self.end_game("no_result")
      return

    bot_col = int(bot_col)

    self.drop_piece(bot_col, -1)
    self.render_board()

    win_cells = self.find_winner_cells(-1)
    if win_cells:
      self.render_board(highlight_cells=win_cells)
      self.status_label.text = f"🤖 Bot wins (played {bot_col}). Click 'New Game' to try again."
      self.end_game("loss")
      self.show_end_popup("loss")
      return

    if self.board_full():
      self.status_label.text = "🤝 Draw! Click 'New Game' to play again."
      self.end_game("draw")
      self.show_end_popup("draw")
      return

    self.status_label.text = f"You played {col}. Bot played {bot_col}. Your turn!"

  # ---------------- BUTTON HANDLERS ----------------

  @handle("new_game_button", "click")
  def new_game_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    text = (
      "• Click a numbered column to drop your piece\n"
      "• Yellow pieces are yours, red are the bot’s\n"
      "• First to connect four wins the game\n"
      "• Connections can be horizontal, vertical, or diagonal\n"
      "• Results are visible at the bottom of the screen\n"
    )
    alert(text, title="How to Play", buttons=[("Begin", True)], large=False)

    # Empty value validation
    if not hasattr(self, "model_dropdown") or not self.model_dropdown.selected_value:
      self.status_label.text = "⚠️ Please select a difficulty before starting the game."
      return

    # Store selected mode normally
    self.current_mode = self._get_selected_mode()

    self.board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    self.game_started = True
    self.game_over = False
    self._counted_this_game = False

    self.status_label.text = "Game started. Your turn!"
    self.render_board()
    self.set_ui_enabled(True)

  @handle("col0_button", "click")
  def col0_button_click(self, **event_args): self.play_col(0)

  @handle("col1_button", "click")
  def col1_button_click(self, **event_args): self.play_col(1)

  @handle("col2_button", "click")
  def col2_button_click(self, **event_args): self.play_col(2)

  @handle("col3_button", "click")
  def col3_button_click(self, **event_args): self.play_col(3)

  @handle("col4_button", "click")
  def col4_button_click(self, **event_args): self.play_col(4)

  @handle("col5_button", "click")
  def col5_button_click(self, **event_args): self.play_col(5)

  @handle("col6_button", "click")
  def col6_button_click(self, **event_args): self.play_col(6)

  @handle("back_button", "click")
  def back_button_click(self, **event_args):
    time.sleep(0.5)
    open_form("DashboardForm")

  @handle("logout_button", "click")
  def logout_button_click(self, **event_args):
    time.sleep(0.5)
    open_form("LoginForm")
    alert("You have successfully logged out!", title="Logout", buttons=[("OK", True)])

  @handle("end_game_button", "click")
  def end_game_button_click(self, **event_args):
    if self._ui_locked:
      return

    if not self.game_started or self.game_over:
      self.status_label.text = "No active game to end."
      return

    self.status_label.text = "Game ended with no result. Click 'New Game' to start again."
    self.end_game("no_result")
    self.show_end_popup("no_result")

  @handle("dpdwn_options_icon", "click")
  def dpdwn_options_icon_click(self, **event_args):
    text = (
      "Easy (Simple Bot)\n"
      "• Picks random valid column each turn\n"
      "• No strategy, easy to beat\n"
      "• Great for learning basic gameplay\n\n"
      "Medium (Transformer)\n"
      "• Uses Transformer model for predictions\n"
      "• Strong pattern recognition, fewer mistakes\n"
      "• Balanced challenge for most players\n\n"
      "Hard (CNN)\n"
      "• Uses CNN model trained aggressively\n"
      "• Spots threats fast, blocks your plans\n"
      "• Best for serious competitive practice"
    )
    Notification(text, title="Difficulty Guide", style="info", timeout=0).show()

  @handle("gameplay_instructions_button", "click")
  def gameplay_instructions_button_click(self, **event_args):
    """This method is called when the link is clicked"""
    time.sleep(0.5)
    open_form("InstructionsForm")

