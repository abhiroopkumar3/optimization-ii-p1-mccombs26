from ._anvil_designer import LoginFormTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import time

class LoginForm(LoginFormTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  @handle("login_button", "click")
  def login_button_click(self, **event_args):
  
    # 1) Read user input
    username = (self.username_box.text or "").strip().lower()
    password = (self.password_box.text or "")
  
    # Empty field validation
    if not username and not password:
      alert("Please enter your username and password.")
      return
    if not username:
      alert("Please enter your username.")
      return
    if not password:
      alert("Please enter your password.")
      return
  
    # 2) Look up user
    user = app_tables.users.get(email=username)
  
    # 3) Validate credentials
    if user and user['password_hash'] == password:
  
      # Block dummy user after successful validation
      if username == "resetpwd":
        alert(
          "Login is successful.\n\nUnfortunately, this is a dummy account.",
          title="Access Restricted",
          buttons=[("OK", True)]
        )
        return
  
      # Normal users
      time.sleep(0.5)
      open_form("DashboardForm")
  
    else:
      alert("Incorrect username or password.")

  @handle("guest_gameplay", "click")
  def guest_gameplay_click(self, **event_args):
    """This method is called when the link is clicked"""
    alert(
      "This feature is not available at the moment.\n\n Please try again later.",
      title="Come Back Later!",
      buttons=[("OK", True)]
    )
    # time.sleep(0.5)
    # open_form("PlayFormGuest")

  @handle("forgot_password", "click")
  def forgot_password_click(self, **event_args):
    """This method is called when the button is clicked"""
    time.sleep(0.5)
    open_form('ForgotPasswordForm')
