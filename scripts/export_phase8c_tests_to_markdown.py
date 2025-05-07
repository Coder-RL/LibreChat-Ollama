import os

TEST_FILES = [
    "test_inference_controller_phase8c_batch1.py",
    "test_inference_controller_phase8c_batch2.py",
    "test_inference_controller_phase8c_batch3.py",
    "test_inference_controller_phase8c_batch4.py",
    "test_inference_controller_phase8c_batch5.py",
]

TESTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests"))
OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Phase8C_Test_Review.md"))

def collect_test_sources():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("# ✅ Phase 8C Test File Review\n\n")
        for filename in TEST_FILES:
            path = os.path.join(TESTS_DIR, filename)
            out.write(f"## `{filename}`\n\n")
            if not os.path.isfile(path):
                out.write("⚠️ File not found.\n\n")
                continue
            out.write("```python\n")
            with open(path, "r", encoding="utf-8") as f:
                out.write(f.read())
            out.write("\n```\n\n")
    print(f"✅ Markdown export complete: {OUTPUT_FILE}")

if __name__ == "__main__":
    collect_test_sources()
