import os
import glob
import pandas as pd
import sys

def merge_databases(root_dir):
    pattern = os.path.join(root_dir, "library_*.xlsx")
    files = glob.glob(pattern)
    legacy = os.path.join(root_dir, "library.xlsx")
    if os.path.exists(legacy):
        files.append(legacy)
        
    print(f"Found {len(files)} database files.")
    
    dfs = []
    for f in files:
        try:
            print(f"Loading {f}...")
            df = pd.read_excel(f)
            dfs.append(df)
        except Exception as e:
            print(f"Error loading {f}: {e}")
            
    if not dfs:
        print("No data found.")
        return
        
    merged = pd.concat(dfs, ignore_index=True)
    
    # Remove duplicates?
    # merged = merged.drop_duplicates(subset=['FilePath'])
    
    output_path = os.path.join(root_dir, "library_merged.xlsx")
    merged.to_excel(output_path, index=False)
    print(f"Successfully merged into {output_path}")

if __name__ == "__main__":
    # Default to current dir or arg
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    merge_databases(target_dir)
