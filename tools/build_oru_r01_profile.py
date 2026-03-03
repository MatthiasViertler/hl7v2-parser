#!/usr/bin/env python3
import pickle
from hl7apy.core import MessageProfile, MessageProfileElement

# ------------------------------------------------------------
# Build HL7 v2.3 ORU_R01 profile programmatically
# ------------------------------------------------------------

profile = MessageProfile(
    name="ORU_R01",
    version="2.3",
    message_type="ORU",
    event="R01",
    description="HL7 v2.3 ORU_R01 Observation Result"
)

# MSH
profile.add_child(MessageProfileElement(
    name="MSH",
    usage="R",
    min_occurs=1,
    max_occurs=1,
    element_type="SEGMENT"
))

# PATIENT_RESULT group
patient_result = MessageProfileElement(
    name="PATIENT_RESULT",
    usage="R",
    min_occurs=1,
    max_occurs=1,
    element_type="GROUP"
)
profile.add_child(patient_result)

# PATIENT group
patient = MessageProfileElement(
    name="PATIENT",
    usage="R",
    min_occurs=1,
    max_occurs=1,
    element_type="GROUP"
)
patient_result.add_child(patient)

# PID
patient.add_child(MessageProfileElement(
    name="PID",
    usage="R",
    min_occurs=1,
    max_occurs=1,
    element_type="SEGMENT"
))

# ORDER_OBSERVATION group
order_obs = MessageProfileElement(
    name="ORDER_OBSERVATION",
    usage="R",
    min_occurs=1,
    max_occurs="*",
    element_type="GROUP"
)
patient_result.add_child(order_obs)

# OBR
order_obs.add_child(MessageProfileElement(
    name="OBR",
    usage="R",
    min_occurs=1,
    max_occurs=1,
    element_type="SEGMENT"
))

# OBSERVATION group
observation = MessageProfileElement(
    name="OBSERVATION",
    usage="R",
    min_occurs=1,
    max_occurs="*",
    element_type="GROUP"
)
order_obs.add_child(observation)

# OBX
observation.add_child(MessageProfileElement(
    name="OBX",
    usage="R",
    min_occurs=1,
    max_occurs=1,
    element_type="SEGMENT"
))

# ------------------------------------------------------------
# Save as pickle
# ------------------------------------------------------------
with open("hl7engine/profiles/HL7v2.3/ORU_R01.pkl", "wb") as f:
    pickle.dump(profile, f)

print("Generated ORU_R01.pkl successfully.")