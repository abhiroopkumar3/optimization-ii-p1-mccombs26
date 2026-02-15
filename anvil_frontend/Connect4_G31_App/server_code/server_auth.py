import anvil.server
from anvil.tables import app_tables

# ---- CONFIG ----
COL_USER = "email"
COL_PASSWORD = "password_hash"
COL_SEC_Q = "security_question"
COL_SEC_A = "security_answer"

COL_HISTORY = "password_history"           # list of previous passwords (most recent first)
COL_REMEMBERED = "remembered_logins"       # list of previous passwords (most recent first)

PROTECTED_USER_1 = "dan"
PROTECTED_USER_2 = "external"

HISTORY_CHECK_COUNT = 3
HISTORY_MAX_STORE = 10


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
  return hist if isinstance(hist, list) else list(hist)

def _get_remembered_list(user_row):
  try:
    hist = user_row[COL_REMEMBERED]
  except Exception:
    hist = None

  if hist is None:
    return []
  return hist if isinstance(hist, list) else list(hist)

def _push_history(user_row, old_password: str):
  # ---- password_history ----
  hist = _get_history_list(user_row)
  if old_password:
    hist.insert(0, old_password)

  seen = set()
  deduped = []
  for p in hist:
    if p not in seen:
      seen.add(p)
      deduped.append(p)

  user_row[COL_HISTORY] = deduped[:HISTORY_MAX_STORE]

  # ---- remembered_logins ----
  rem = _get_remembered_list(user_row)
  if old_password:
    rem.insert(0, old_password)

  seen2 = set()
  deduped2 = []
  for p in rem:
    if p not in seen2:
      seen2.add(p)
      deduped2.append(p)

  user_row[COL_REMEMBERED] = deduped2[:HISTORY_MAX_STORE]

  return user_row[COL_HISTORY]

def _validate_new_password(user_row, username: str, new_password: str):
  if not new_password:
    raise ValueError("Password cannot be empty.")

  # protected users
  if _norm_ci(username) == PROTECTED_USER_1.lower():
    raise ValueError("Password reset is restricted for this user.")
  if _norm_ci(username) == PROTECTED_USER_2.lower():
    raise ValueError("Password reset is restricted for this user.")

  current_pw = user_row[COL_PASSWORD] or ""
  if new_password == current_pw:
    raise ValueError("New password cannot be the same as the current password.")

  # last 3 check
  hist = _get_history_list(user_row)
  last_n = hist[:HISTORY_CHECK_COUNT]
  if new_password in last_n:
    raise ValueError(f"New password cannot match any of your last {HISTORY_CHECK_COUNT} passwords.")


# ---------------- SERVER CALLABLES ----------------

@anvil.server.callable
def fp_get_security_question(username: str):
  user_row = _get_user_row(username)
  if not user_row:
    raise ValueError("User not found.")

  if _norm_ci(username) == PROTECTED_USER_1.lower():
    raise ValueError("Password reset is disabled for this user.")
  if _norm_ci(username) == PROTECTED_USER_2.lower():
    raise ValueError("Password reset is disabled for this user.")

  q_text = _norm(user_row[COL_SEC_Q])
  if not q_text:
    raise ValueError("No security question is set for this user.")

  return {"ok": True, "question": q_text}


@anvil.server.callable
def fp_check_security_answer(username: str, answer_text: str):
  user_row = _get_user_row(username)
  if not user_row:
    raise ValueError("User not found.")

  if _norm_ci(username) == PROTECTED_USER_1.lower():
    raise ValueError("Password reset is disabled for this user.")
  if _norm_ci(username) == PROTECTED_USER_2.lower():
    raise ValueError("Password reset is disabled for this user.")

  expected = _norm(user_row[COL_SEC_A])
  if not expected:
    raise ValueError("No security answer is set for this user.")

  given = _norm(answer_text)
  return given.lower() == expected.lower()


@anvil.server.callable
def fp_get_password_for_display(username: str):
  user_row = _get_user_row(username)
  if not user_row:
    raise ValueError("User not found.")

  if _norm_ci(username) == PROTECTED_USER_1.lower():
    raise ValueError("Password reset is disabled for this user.")
  if _norm_ci(username) == PROTECTED_USER_2.lower():
    raise ValueError("Password reset is disabled for this user.")

  return {"password": user_row[COL_PASSWORD] or ""}


@anvil.server.callable
def fp_reset_password(username: str, new_password: str):
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
  user_row = _get_user_row(username)
  if not user_row:
    raise ValueError("User not found.")
  return _get_history_list(user_row)
