# Server Module: server_auth.py
# ------------------------------------------------------------
# Uses Users table columns:
#   - email (text)
#   - password_hash (text)          (NOTE: you are storing plain text currently)
#   - security_question (text)
#   - security_answer (text)        (plain text answer)
#   - password_history (simpleObject / list)   OPTIONAL but recommended
#
# If your column names differ, update the constants below.
# ------------------------------------------------------------

import anvil.server
from anvil.tables import app_tables

# ---- CONFIG: change these if your table column names differ ----
COL_USER = "email"                 # username column
COL_PASSWORD = "password_hash"     # password column (plain text for now)
COL_SEC_Q = "security_question"    # security question column (text)
COL_SEC_A = "security_answer"      # security answer column (text)

COL_HISTORY = "password_history"   # list of previous passwords (most recent first)
PROTECTED_USER = "dan"             # cannot reset this user
MIN_PASSWORD_LEN = 6
HISTORY_CHECK_COUNT = 3            # last N passwords cannot be reused
HISTORY_MAX_STORE = 10             # keep up to N old passwords (optional)


# ---------------- HELPERS ----------------

def _norm(s: str) -> str:
  return (s or "").strip()

def _norm_ci(s: str) -> str:
  return _norm(s).lower()

def _get_user_row(username: str):
  username = _norm(username)
  if not username:
    return None
  return app_tables.users.get(**{COL_USER: username})

def _get_history_list(user_row):
  try:
    hist = user_row[COL_HISTORY]
  except Exception:
    hist = None

  if hist is None:
    return []
  if isinstance(hist, list):
    return hist
  return list(hist)

def _push_history(user_row, old_password: str):
  hist = _get_history_list(user_row)

  if old_password:
    hist.insert(0, old_password)

  # de-dupe preserving order
  seen = set()
  deduped = []
  for p in hist:
    if p not in seen:
      seen.add(p)
      deduped.append(p)

  user_row[COL_HISTORY] = deduped[:HISTORY_MAX_STORE]
  return user_row[COL_HISTORY]

def _validate_new_password(user_row, username: str, new_password: str):
  if not new_password:
    raise ValueError("Password cannot be empty.")

  if len(new_password) < MIN_PASSWORD_LEN:
    raise ValueError(f"Password must be at least {MIN_PASSWORD_LEN} characters.")

  if _norm_ci(username) == PROTECTED_USER.lower():
    raise ValueError("Password reset is restricted for this user.")

  current_pw = user_row[COL_PASSWORD] or ""

  if new_password == current_pw:
    raise ValueError("New password cannot be the same as the current password.")

  hist = _get_history_list(user_row)
  last_n = hist[:HISTORY_CHECK_COUNT]
  if new_password in last_n:
    raise ValueError(f"New password cannot match any of your last {HISTORY_CHECK_COUNT} passwords.")


# ---------------- SERVER CALLABLES ----------------

@anvil.server.callable
def fp_get_security_question(username: str):
  """
  Called when user clicks 'Retrieve Password'.
  Returns:
    {"ok": True, "question": "<from Users.security_question>"}
  """
  user_row = _get_user_row(username)
  if not user_row:
    raise ValueError("User not found.")

  if _norm_ci(username) == PROTECTED_USER.lower():
    raise ValueError("Password recovery is disabled for this user.")

  q_text = _norm(user_row[COL_SEC_Q])
  if not q_text:
    raise ValueError("No security question is set for this user.")

  return {"ok": True, "question": q_text}


@anvil.server.callable
def fp_check_security_answer(username: str, answer_text: str):
  """
  Called when user clicks 'Submit' on the security question.
  Returns True/False.
  """
  user_row = _get_user_row(username)
  if not user_row:
    raise ValueError("User not found.")

  if _norm_ci(username) == PROTECTED_USER.lower():
    raise ValueError("Password recovery is disabled for this user.")

  expected = _norm(user_row[COL_SEC_A])
  if not expected:
    raise ValueError("No security answer is set for this user.")

  given = _norm(answer_text)

  # If you want case-insensitive match, use lower() on both:
  return given.lower() == expected.lower()


@anvil.server.callable
def fp_get_password_for_display(username: str):
  """
  OPTIONAL: Use only if you still want to *display* the existing password
  after a correct security answer. (Not recommended for real apps.)
  """
  user_row = _get_user_row(username)
  if not user_row:
    raise ValueError("User not found.")

  if _norm_ci(username) == PROTECTED_USER.lower():
    raise ValueError("Password recovery is disabled for this user.")

  return {"password": user_row[COL_PASSWORD] or ""}


@anvil.server.callable
def fp_reset_password(username: str, new_password: str):
  """
  Resets password after user is verified on the client side.
  Enforces:
    1) >= 6 characters
    2) not same as current
    3) not same as last 3 old passwords (password_history)
    4) cannot reset protected user 'dan'
  Updates:
    - pushes old password into password_history
    - sets password_hash to new_password
  """
  user_row = _get_user_row(username)
  if not user_row:
    raise ValueError("User not found.")

  _validate_new_password(user_row, username, new_password)

  old_pw = user_row[COL_PASSWORD] or ""
  _push_history(user_row, old_pw)
  user_row[COL_PASSWORD] = new_password

  return {"ok": True}


@anvil.server.callable
def fp_get_password_history(username: str):
  """
  OPTIONAL debug helper.
  """
  user_row = _get_user_row(username)
  if not user_row:
    raise ValueError("User not found.")
  return _get_history_list(user_row)
