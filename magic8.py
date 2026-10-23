import random
class Magic8Ball:
  responses_sarcastic = [
    "You wish.",
    "As if!",
    "You call that a question?",
    "Good luck with that.",
    "You've got to be kidding.",
    "Ask me if I care.",
    "🤷 try chatgpt",
    "You don't want to know, trust me.",
    "42.",
    "Sorry, this feature is only available to Pro subscribers.",
  ]
  responses_normal = [
    "It is certain.",
    "Without a doubt.",
    "You may rely on it.",
    "Yes definitely.",
    "It is decidedly so.",
    "As I see it, yes.",
    "Most likely.",
    "Yes.",
    "Outlook good.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Better not tell you now.",
    "Ask again later.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don’t count on it.",
    "Outlook not so good.",
    "My sources say no.",
    "Very doubtful.",
    "My reply is no.",
  ]
  def rando(self):
    return random.choice(self.responses_sarcastic)
