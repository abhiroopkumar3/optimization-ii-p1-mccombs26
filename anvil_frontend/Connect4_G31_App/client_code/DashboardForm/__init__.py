from ._anvil_designer import DashboardFormTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import time

class DashboardForm(DashboardFormTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  @handle("logout_button", "click")
  def logout_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    time.sleep(0.5)
    open_form("LoginForm")
    alert("You have successfully logged out!", title="Logout", buttons=[("OK", True)])

  @handle("writeup_button", "click")
  def writeup_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    time.sleep(0.5)
    open_form("WriteupForm")

  @handle("play_button", "click")
  def play_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    time.sleep(0.5)
    open_form("PlayForm")
