"""
CLI test harness for the Multi-Agent Impact Story pipeline.

Run with:
    cd backend
    python -m tests.test_ai_pipeline

Prerequisites:
    1. GCP_PROJECT_ID and GCP_LOCATION set in backend/.env
    2. gcloud auth application-default login
    3. Vertex AI API enabled on the project
"""

import asyncio
import textwrap
from datetime import datetime

from app.service.ai_service import generate_impact_story


async def _main() -> None:
    test_org    = "Canadian Red Cross"
    test_prompt = (
        "A donor from Vancouver recently contributed $100 to the Canadian Red Cross. "
        "Focus specifically on recent efforts in Canada or British Columbia. "
        "Combine verified financial metrics from their annual reports with recent news "
        "to close the feedback loop for the donor."
    )

    bar = "=" * 67
    print(f"\n{bar}")
    print("  Benevity — Impact Story Generator  (MVP Demo)")
    print(bar)
    print(f"  Org    : {test_org}")
    print(f"  Prompt : {test_prompt}")
    print(f"  Time   : {datetime.now().strftime('%H:%M:%S')}")
    print(f"{bar}\n")

    print("  Running pipeline (Research → Synthesis → Validation)...", end="", flush=True)
    result = await generate_impact_story(test_org, test_prompt)
    print(f" done ({result.get('total_elapsed', '?')}s)\n")

    print(f"\n{bar}")
    print(f"  FINAL STATUS : {result['status']}")
    print(f"  FACTS USED   : {result['facts_summary']}")
    print(bar)
    print("\n  ── IMPACT STORY ──────────────────────────────────────────────\n")
    for line in textwrap.wrap(result["story"], width=65):
        print(f"  {line}")

    if result["factual_errors"]:
        print("\n  ── FACTUAL ERRORS ────────────────────────────────────────────")
        for err in result["factual_errors"]:
            print(f"  ✗  {err}")

    if result["writing_issues"]:
        print("\n  ── WRITING ISSUES ────────────────────────────────────────────")
        for issue in result["writing_issues"]:
            print(f"  ✎  {issue}")

    print(f"\n{bar}\n")


if __name__ == "__main__":
    asyncio.run(_main())
