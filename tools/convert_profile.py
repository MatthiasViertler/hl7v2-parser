from hl7apy import load_xml_profile
import pickle
import sys

xml_path = sys.argv[1]
pkl_path = sys.argv[2]

profile = load_xml_profile(xml_path)

with open(pkl_path, "wb") as f:
    pickle.dump(profile, f)

print("Profile converted:", pkl_path)