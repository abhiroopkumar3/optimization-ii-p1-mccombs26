from ._anvil_designer import InstructionsFormGuestTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import time


class InstructionsFormGuest(InstructionsFormGuestTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  @handle("back_button", "click")
  def back_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    time.sleep(0.5)
    open_form("PlayFormGuest")

  @handle("exit_button", "click")
  def exit_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    time.sleep(0.5)
    open_form("LoginForm")
    alert("You have successfully exited the game!", title="Exit", buttons=[("OK", True)])
