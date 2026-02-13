from ._anvil_designer import ForgotPasswordFormTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import time

class ForgotPasswordForm(ForgotPasswordFormTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

    # internal state
    self._user_row = None
    self._question_answer = None  # numeric expected answer

    # initial UI state
    self.security_panel.visible = False
    self.reset_panel.visible = False
    self.change_user_button.visible = False
    self.user_box.enabled = True

  # ---------------- helpers ----------------

  def _reset_ui(self):
    """Return UI to initial state."""
    self._user_row = None
    self._question_answer = None

    self.user_box.enabled = True
    self.security_panel.visible = False
    self.reset_panel.visible = False
    self.change_user_button.visible = False

    self.security_question_label.text = ""
    self.answer_box.text = ""
    self.new_password_box.text = ""
    self.confirm_password_box.text = ""

  def _show_security_question(self):
    # Optimization question with numeric answer
    self.security_question_label.text = (
      "In a 0–1 knapsack, item weights are [2, 3, 4] and capacity is 5.\n"
      "What is the maximum number of items you can pick?"
    )
    self._question_answer = 2

    # show panel and lock user field
    self.security_panel.visible = True
    self.user_box.enabled = False
    self.change_user_button.visible = True

  # ---------------- button handlers ----------------

  @handle("retrieve_button", "click")
  def retrieve_button_click(self, **event_args):
    email = (self.user_box.text or "").strip().lower()
  
    if not email:
      alert("Enter your email first.")
      return
  
    try:
      resp = anvil.server.call("fp_get_security_question", email)
    except Exception as e:
      alert(str(e))
      return
  
    # Server returns: {"ok": True, "question": "..."}
    question = resp.get("question")
  
    self.security_question_label.text = question
    self.security_panel.visible = True
    self.reset_panel.visible = False
  
    self.user_box.enabled = False
    self.change_user_button.visible = True

  @handle("submit_button", "click")
  def submit_button_click(self, **event_args):
    email = (self.user_box.text or "").strip().lower()
    ans = (self.answer_box.text or "").strip()
  
    if not ans:
      alert("Please enter your answer.")
      return
  
    try:
      ok = anvil.server.call("fp_check_security_answer", email, ans)
    except Exception as e:
      alert(str(e))
      return
  
    if not ok:
      alert("Incorrect answer. Please try again.")
      return
  
    # Answer correct → swap panels
    self.security_panel.visible = False
    self.reset_panel.visible = True
  
    alert(
      "Correct answer! Please set a new password.",
      title="Verified",
      buttons=[("OK", True)]
    )

  @handle("reset_password_button", "click")
  def reset_password_button_click(self, **event_args):
    email = (self.user_box.text or "").strip().lower()
    new_pw = (self.new_password_box.text or "")
    confirm_pw = (self.confirm_password_box.text or "")
  
    # 1️⃣ Empty validation
    if not new_pw or not confirm_pw:
      alert("Please fill in both password fields.")
      return
  
    # 2️⃣ Match validation
    if new_pw != confirm_pw:
      alert("Passwords do not match. Please try again.")
      return
  
    try:
      ok = anvil.server.call("fp_reset_password", email, new_pw)
    except Exception as e:
      alert(str(e))
      return
  
    if ok:
      alert("Password updated successfully!", title="Success")
      open_form("LoginForm")
    else:
      alert("Could not update password.")

  @handle("change_user_button", "click")
  def change_user_button_click(self, **event_args):
    self.user_box.enabled = True
    self.user_box.text = ""
    self.answer_box.text = ""
    self.new_password_box.text = ""
  
    self.security_panel.visible = False
    self.reset_panel.visible = False
    self.change_user_button.visible = False

  @handle("back_button", "click")
  def back_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    time.sleep(0.5)
    open_form('LoginForm')

  @handle("info_icon_button", "click")
  def info_icon_button_click(self, **event_args):
    text = (
      "• Enter the registered username\n"
      "• Click 'Retrieve Password' to view your security question\n"
      "• Answer the question correctly to reset your password\n"
      "• Your new password must be at least 6 characters\n"
      "• You cannot reuse any of your last 3 passwords\n\n"
      "Try dummy user 'resetpwd' to test this functionality\n"
    )
    Notification(text, title="Forgot Password Help", style="info", timeout=0).show()

  @handle("pwd_criteria_icon_button", "click")
  def pwd_criteria_icon_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    text = (
      "• Your new password must be at least 6 characters\n"
      "• You cannot reuse any of your last 3 passwords\n"
      "• After successfully reseting your password, login again with your new password\n"
    )
    Notification(text, title="New Password Criteria", style="info", timeout=0).show()


