import inflect

class UserInventory:
  inflector = inflect.engine()

  def __init__(self):
    self.pack = set()
    self.pock = set()

  def to_data(self):
    """Return a JSON-compatible representation with stable item ordering."""
    return {"pack": sorted(self.pack), "pock": sorted(self.pock)}

  @classmethod
  def from_data(cls, data):
    """Build an inventory from saved data, rejecting malformed values."""
    if not isinstance(data, dict) or set(data) != {"pack", "pock"}:
      raise ValueError("inventory must contain exactly 'pack' and 'pock' lists")
    pack, pock = data["pack"], data["pock"]
    if (not isinstance(pack, list)
        or not all(isinstance(item, str) and item for item in pack)
        or not isinstance(pock, list)
        or not all(isinstance(item, str) and item for item in pock)):
      raise ValueError("inventory items must be non-empty strings in lists")
    if len(pack) != len(set(pack)) or len(pock) != len(set(pock)):
      raise ValueError("inventory lists cannot contain duplicate items")
    if set(pack) & set(pock):
      raise ValueError("an item cannot be both visible and pocketed")
    inventory = cls()
    inventory.pack = set(pack)
    inventory.pock = set(pock)
    return inventory

  def to_dict(self):
    """Alias for the JSON-compatible inventory representation."""
    return self.to_data()

  @classmethod
  def from_dict(cls, data):
    """Alias for loading a JSON-compatible inventory representation."""
    return cls.from_data(data)

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

  def see(self, item:str):
    """True if item is publicly visible."""
    return item in self.pack

  def has(self, item: str):
    """True if the user possesses the item."""
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
