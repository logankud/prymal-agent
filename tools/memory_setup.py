# memory_setup.py

from langchain.memory import ConversationBufferMemory
import os
import json


class AgentMemory:
  def __init__(self, filename="agent_memory.json"):
      self.filename = filename
      self.store = self._load()

  def _load(self):
      if os.path.exists(self.filename):
          try:
              with open(self.filename, "r") as f:
                  return json.load(f)
          except json.JSONDecodeError:
              return {}
      return {}

  def _save(self):
      with open(self.filename, "w") as f:
          json.dump(self.store, f)

  def remember(self, key, value):
      self.store[key] = value
      self._save()

  def recall(self, key):
      return self.store.get(key)

  def forget(self, key):
      if key in self.store:
          del self.store[key]
          self._save()

# --- Singleton Interface ---
_memory_instance = None

def get_agent_memory() -> AgentMemory:
  global _memory_instance

  # If memory doesn't exist, create it
  if _memory_instance is None:
      _memory_instance = AgentMemory()
  return _memory_instance
