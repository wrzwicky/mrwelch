import inflect

class UserInventory:
  #classvariable
  inflector = inflect.engine()

  def __init__(self):
    self.pack = set()
    self.pock = set()

  def isEmpty(self):
    return not (self.pack or self.pock)

  def describeMe(self):
    """Show full private inventory."""
    s = self.describe() + f" ({joinAnd([self.inflector.a(i) for i in self.pock])})"

  def describe(self):
    """Show publicly visible inventory."""
    s = sorted(self.pack)
    s = [self.inflector.a(i) for i in s]
    if self.pock:
      if 'one ring' in (name.casefold() for name in self.pock):
        s.append("something in pocketses")
      else:
        s.append("something in pockets")
    return joinAnd(s)
  
  def add(self, item: str):
    self.pack.add(item)
    # multiples

  def see(self, item:str):
    """True if item is publicly visible"""
    return item in self.pack

  def has(self, item: str):
    """True if posesses item"""
    return item in self.pack or item in self.pock

  def pocket(self, item: str):
    if item in self.pack:
      self.pack.remove(item)
      self.pock.add(item)
  
  def remove(self, item: str):
    if item in self.pack:
      self.pack.discard(item)
    else:
      self.pock.discard(item)
    #else err "you dont have item"

def joinAnd(lst):
  """Join with commas, and include 'and' before last element."""
  if len(lst) == 0:
    return ""
  elif len(lst) == 1:
    return lst[0]
  elif len(lst) == 2:
    return " and ".join(lst)
  else:
    return ", ".join(lst[:-1]) + ", and " + lst[-1]

#plurl
  #add s or es, or en if ends with x
#singl
  #remove a/an
  #remove s, es, en

#reject -oux
# 'no French words please'
