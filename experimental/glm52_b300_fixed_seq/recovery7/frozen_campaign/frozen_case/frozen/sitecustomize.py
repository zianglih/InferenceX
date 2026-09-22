"""Inherited by spawned ranks only when explicitly selected by a future adapter."""
import os
if os.environ.get('MEGAMOE_R7_NATIVE_PROOF_LOCK'):
    from natural_proof import install
    install()
