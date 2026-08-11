"""Seed all demo workflows in one command.

Run:
    python -m scripts.seed_all_demos

Original 3 workflows (demo@payment.com):
    1. Payment Workflow              — decision gateway + retry loop
    2. Order Delivery Workflow       — conditional branching on inventory check
    3. Document Approval Workflow    — review/revise loop

New 8 workflows (same demo user):
    4. E-Commerce Order Processing   — long graph with fraud-gate + cancel branch
    5. Banking Transaction Workflow  — fail-fast + compensating rollback
    6. CI/CD Deployment Pipeline     — quality gates (test/security/build)
    7. Hospital Patient Processing   — critical sequential + insurance gate
    8. AI Data Processing Pipeline   — retrain loop on failed accuracy evaluation
    9. Video Streaming Processing    — media pipeline + virus quarantine branch
   10. Failure & Retry Demonstration — self-retry loop (MAX_LOOP_ITERATIONS)
   11. BUG-02 Demonstration          — legacy sequential, shows BUG-02 fix

All seeds are idempotent (safe to re-run without creating duplicates).
"""
from scripts.seed_payment_workflow  import seed as seed_payment
from scripts.seed_order_delivery    import seed as seed_order
from scripts.seed_document_approval import seed as seed_document
from scripts.seed_ecommerce_order   import seed as seed_ecommerce
from scripts.seed_banking_transaction import seed as seed_banking
from scripts.seed_cicd_pipeline     import seed as seed_cicd
from scripts.seed_hospital_patient  import seed as seed_hospital
from scripts.seed_ai_pipeline       import seed as seed_ai
from scripts.seed_video_processing  import seed as seed_video
from scripts.seed_failure_demo      import seed as seed_failure
from scripts.seed_bug02_demo        import seed as seed_bug02


def main() -> None:
    print("=== Seeding all demo workflows ===\n")

    print("-- Original workflows --")
    seed_payment()
    seed_order()
    seed_document()

    print("\n-- Enterprise / real-world scenarios --")
    seed_ecommerce()
    seed_banking()
    seed_hospital()
    seed_video()

    print("\n-- Engineering / technical workflows --")
    seed_cicd()
    seed_ai()

    print("\n-- Engine demonstration workflows --")
    seed_failure()
    seed_bug02()

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
