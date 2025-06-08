import os

output_file = "all_scripts.txt"

with open(output_file, "w", encoding="utf-8") as out:
    for root, dirs, files in os.walk("."):
        if ".conda" in dirs:
            dirs.remove(".conda")
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as py_file:
                    out.write(f"# {filepath}\n\n")
                    out.write(py_file.read())
                    out.write("\n\n")

print(f"Python scripts merged into {output_file}")