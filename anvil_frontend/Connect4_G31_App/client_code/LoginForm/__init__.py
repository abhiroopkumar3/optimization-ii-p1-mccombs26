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
    # 1) Read what the user typed
    username = (self.username_box.text or "").strip()
    password = (self.password_box.text or "")
  
    # 2) Look up user in Users table
    user = app_tables.users.get(email=username)
  
    # 3) Validate credentials
    if user and user['password_hash'] == password:
      time.sleep(0.5)
      open_form("DashboardForm")
    else:
      alert("Incorrect username or password.")

  @handle("forgot_password", "click")
  def forgot_password_click(self, **event_args):
    """This method is called when the link is clicked"""
    time.sleep(0.5)
    open_form("PlayFormGuest")
