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
        'user': 'John Pork',
        'current_date': str(datetime.now())
    }

    result = PerfumePicker().crew().kickoff(inputs=inputs)

    #Print the result
    print("\n\n=== FINAL DECISION ===\n\n")
    print(result.raw)

if __name__ == "__main__":
    run()

