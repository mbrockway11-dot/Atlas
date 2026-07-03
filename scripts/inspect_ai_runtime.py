from pprint import pprint

from atlas.ai import run_research_pipeline

runtime = run_research_pipeline(
    "Analyze Nikola Tesla through Atlas research intelligence."
)

print("=" * 80)
print("SUCCESS")
print(runtime.success)

print("=" * 80)
print("INTEGRATED")
pprint(runtime.integrated)

print("=" * 80)
print("STAGES")
print(runtime.stages.keys())

for name, stage in runtime.stages.items():
    print()
    print("=" * 80)
    print(name)
    print("=" * 80)

    print("status:", stage.status)
    print()

    print("payload keys:")
    pprint(stage.payload.keys())

    print()

    data = stage.payload.get("data", {})
    print("data keys:")
    pprint(data.keys())

    print()

    for key, value in data.items():
        print(f"{key}: {type(value).__name__}")

        if isinstance(value, dict):
            print("dict keys:")
            pprint(list(value.keys()))

        elif isinstance(value, list):
            print("length:", len(value))

        else:
            pprint(value)

        print()