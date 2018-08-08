import json
import os
import pprint
import subprocess
import sys

src_path = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()

print("Listing tests for " + src_path, file=sys.stderr)

all_files = []

test_files = set()
expected_files = {}
output = {}

virtual_path = os.path.join(src_path, "virtual")

with open(os.path.join(src_path, "VirtualTestSuites")) as virtual_fp:
    virtual_desc = json.load(virtual_fp)

output["virtual"] = {}
for entry in virtual_desc:
    output["virtual"].setdefault(entry["prefix"], []).append(entry["base"])
for virtual_name in output["virtual"]:
    output["virtual"][virtual_name].sort()

for dir, dirnames, filenames in os.walk(src_path):
    for file in filenames:
        file = os.path.join(dir, file)

        all_files.append(os.path.join(dir, file))

        if file.endswith(".html"):
            test_files.add(file)

        if file.endswith("-expected.txt"):
            virtual_name = "base"
            base_name = file

            if file.startswith(virtual_path):
                #print("Found virtual expectation " + file)
                relpath = os.path.relpath(file, virtual_path)
                virtual_name, base_name = relpath.split(os.path.sep, 1)
                # print("relpath {} virtual_name {} base_name {}".format(
                #    relpath, virtual_name, base_name))

            expected_files.setdefault(os.path.join(src_path, base_name), {})[
                virtual_name] = file

# pprint.pprint(expected_files)
output["results"] = {}

for test_file in test_files:
    expected_path = test_file[:-5] + "-expected.txt"
    test_file = os.path.relpath(test_file, src_path)
    if expected_path in expected_files:
        output["results"][test_file] = {}
        for virtual_name in expected_files[expected_path]:
            try:
                expected_virtual_path = expected_files[expected_path][virtual_name]
                with open(expected_virtual_path, encoding="utf-8", errors="ignore") as f:
                    lines = [s for s in f.readlines() if s.startswith("FAIL")
                             or s.startswith("PASS")]
                pass_count = sum(1 if s.startswith(
                    "PASS") else 0 for s in lines)
                output["results"][test_file][virtual_name] = {
                    "pass": pass_count,
                    "fail": len(lines) - pass_count,
                    "expected": os.path.relpath(expected_virtual_path, src_path),
                    "lines": lines,
                }
            except:
                print("Failed to read " + expected_virtual_path, file=sys.stderr)
    else:
        output["results"][test_file] = None

output["meta"] = {
    "hash": subprocess.check_output(["git", "log", "-n1", "--pretty=format:%H"], cwd=src_path).decode("utf-8"),
    "subject": subprocess.check_output(["git", "log", "-n1", "--pretty=format:%s"], cwd=src_path).decode("utf-8"),
    "date": subprocess.check_output(["git", "log", "-n1", "--pretty=format:%ci"], cwd=src_path).decode("utf-8"),
}

print("const tests = ", end="")
print(json.dumps(output, indent=2, sort_keys=True), end="")
print(";")
