#!/usr/bin/env python
"""
Inspect Autogen Tool Class

This script inspects the parameters of the AutogenTool class to understand the expected parameters.
"""

import inspect
from autogen.tools import Tool as AutogenTool

# Get the signature of the AutogenTool.__init__ method
signature = inspect.signature(AutogenTool.__init__)

# Print the parameters
print("AutogenTool.__init__ parameters:")
for param_name, param in signature.parameters.items():
    if param_name != 'self':  # Skip the 'self' parameter
        print(f"  {param_name}: {param.annotation}")
        if param.default is not inspect.Parameter.empty:
            print(f"    default: {param.default}")
