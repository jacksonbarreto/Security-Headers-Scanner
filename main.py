import os
from src.scanner.scanner import run_scan

def main():
    input_directory = os.path.join('.', 'src', 'data', 'source')
    files = [f for f in os.listdir(input_directory) if f.endswith('.csv')]
    print(f"Found {len(files)} files to scan.")

    if not files:
        print(f"No CSV files found in '{input_directory}'. Please ensure the files are in the correct directory.")
        return

    for file in files:
        file_path = os.path.join(input_directory, file)
        print(f"Scanning file: {file}")
        try:
            run_scan(file_path)
        except Exception as e:
            print(f"Error scanning {file}: {e}")

if __name__ == "__main__":
    main()
