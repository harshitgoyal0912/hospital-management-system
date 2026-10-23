"""Guarded agent layer for the hospital management system.

The LLM produces language and plans. It does not decide what is permitted and it
does not reach the database. Every operational action passes through this package:
typed schemas, a deterministic policy engine, and an audited execution path.
"""
__all__ = ["policy", "schemas"]
