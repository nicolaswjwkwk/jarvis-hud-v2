import sys
from pathlib import Path

# Garante que o pacote `server` seja importável a partir da raiz do repo
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
