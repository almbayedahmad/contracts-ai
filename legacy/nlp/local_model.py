
"""Local NLP stub (no cloud).
- If a HF/ONNX model exists at `model_dir`, you can implement `predict_roles(texts)`.
- If not, we fall back to regex/keyword heuristics.
"""
import re
from typing import List, Dict, Any

class LocalClassifier:
    def __init__(self, model_dir: str | None = None):
        self.model_dir = model_dir
        # TODO: Load local model weights if available (HF/ONNX).

    def predict_roles(self, party_blocks: List[str]) -> List[str]:
        """Return roles per block: customer/provider/auftraggeber/auftragnehmer/kunde/lieferant/unknown"""
        roles = []
        for txt in party_blocks:
            t = (txt or '').lower()
            if any(w in t for w in ['auftraggeber','kunde','customer']):
                roles.append('customer')
            elif any(w in t for w in ['auftragnehmer','lieferant','provider','lieferer']):
                roles.append('provider')
            else:
                roles.append('unknown')
        return roles
