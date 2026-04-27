"""TestQL — Multi-DSL Test Platform.

Adapters for TestTOON / NL / SQL / Proto / GraphQL all produce the same
Unified IR (`testql.ir.TestPlan`); generators (`testql.generators`) convert
external artifacts into IR; meta-testing (`testql.meta`) analyses the
generated plans for coverage, confidence and mutation resilience.
"""

__version__ = "1.2.36"
