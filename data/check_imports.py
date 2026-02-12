import sys
import traceback
import os

sys.path.append(os.getcwd())

print("Attempting to import modules.mte_shared...")
try:
    from modules import mte_shared
    print("mte_shared imported successfully.")
except:
    traceback.print_exc()

print("Attempting to import modules.online_client...")
try:
    from modules import online_client
    print("online_client imported successfully.")
except:
    traceback.print_exc()

print("Attempting to import main...")
try:
    import main
    print("main imported successfully.")
except:
    traceback.print_exc()
