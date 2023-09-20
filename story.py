import copy
import os
import random
import re
import sys

NODUPS = False

class Story:
  token_re = re.compile("<[^>]*>")

  def __init__(self, filename=None) -> None:
    if not filename:
      filename = os.path.join(sys.path[0], "badjoke.txt")
    self.masterGrammar = self.readGrammar(filename)

  def tell(self, rule=None):
    self.grammar = copy.deepcopy(self.masterGrammar)
    if not rule:
      rule = "start"
    return self.expand(rule)

  def readGrammar(self, filename):
    """read file, return as dict of arrays"""
    rule = "(trash-bin)"
    grammar = {}  #dict of ary
    
    with open(filename) as fil:
      for lin in fil:
        lin = lin.strip().encode('utf-8', 'namereplace').decode('unicode_escape')
        if lin.endswith(":"):
          rule = lin[0:-1]
          grammar[rule] = []
        elif len(lin) > 0:
          grammar[rule].append(lin)
    return grammar
    
  def pick(self, rule, nodups=False):
    """return random string from a rule, optionally delete from grammar to prevent duplicates"""
    opts = self.grammar[rule]
    ix = random.randrange(0, len(opts))
    text = opts[ix]
    
    if nodups:
      del opts[ix]
    return text
  
  def expand(self, rule):
    """pick random string from rule, then parse and replace all <tokens>"""
    toupper = False
    if rule[0] == '^':
      toupper = True
      rule = rule[1:]
    
    inp = self.pick(rule, NODUPS)
    outp = ""
    last_end = 0
    for m in self.token_re.finditer(inp):
      outp += inp[last_end:m.start()]
      outp += self.expand(m[0][1:-1])
      last_end = m.end()
    outp += inp[last_end:]
  
    if toupper:
      outp = outp[0].upper() + outp[1:]
    return outp
  

if __name__ == "__main__":
  s = Story()
  print(s.tell())
