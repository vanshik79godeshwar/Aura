import os, sys
print("Starting...")
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _PROJECT_ROOT)
print("Importing orchestrator...")
from src.agents.orchestrator import app as aura_graph
print("Importing DBEngine...")
from src.core.db_engine import DBEngine
print("Importing Registry...")
from src.core.registry import ContextRegistry

print("Connecting to DBEngine...")
DBEngine()
print("Building Registry...")
registry = ContextRegistry()
registry.build_registry()
print("Done Fast Test!")
