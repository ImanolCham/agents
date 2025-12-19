#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime

from perfume_picker.crew import PerfumePicker

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the research crew.
    """
    inputs = {
        "user": input("Nombre de usuario: ").strip() or "User",
        "query": input("¿Qué perfume buscas? (texto libre): ").strip(),
        "current_date": datetime.now().astimezone().isoformat(),
    }

    result = PerfumePicker().crew().kickoff(inputs=inputs)

    #Print the result
    print("\n\n=== FINAL DECISION ===\n\n")
    print(result.raw)

if __name__ == "__main__":
    run()

