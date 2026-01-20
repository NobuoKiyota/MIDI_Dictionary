import os
import pandas as pd
import platform
import glob

class DataManager:
    def __init__(self, db_path_ignored, root_dir):
        # db_path is now mostly ignored or used as base pattern?
        # We will use root_dir to find library_*.xlsx
        self.root_dir = root_dir
        
        # Determine Local DB Name
        hostname = platform.node()
        self.local_db_name = f"library_{hostname}.xlsx"
        self.local_db_path = os.path.join(self.root_dir, self.local_db_name)
        
        self.columns = [
            "FileName", "FilePath", "Category", "Instruments", 
            "TimeSignature", "Measure", "Bar", "Chord",
            "Root", "Group", "Comment"
        ]
        
        self.df = self.load_db()

    def load_db(self):
        # Scan for all 'library_*.xlsx' in root_dir
        pattern = os.path.join(self.root_dir, "library_*.xlsx")
        files = glob.glob(pattern)
        
        # Also include legacy 'library.xlsx' if it exists and migrate?
        # Or just read it.
        legacy_path = os.path.join(self.root_dir, "library.xlsx")
        if os.path.exists(legacy_path):
            files.append(legacy_path)
            
        if not files:
            # Init empty local DB if nothing exists
            return pd.DataFrame(columns=self.columns)
            
        dfs = []
        for f in files:
            try:
                d = pd.read_excel(f)
                # Normalize cols
                for col in self.columns:
                    if col not in d.columns:
                        d[col] = ""
                d = d.fillna("")
                
                # Track Source
                d["_SourceFile"] = os.path.basename(f)
                dfs.append(d)
            except Exception as e:
                print(f"Error loading {f}: {e}")
                
        if not dfs:
            return pd.DataFrame(columns=self.columns)
            
        combined_df = pd.concat(dfs, ignore_index=True)
        return combined_df

    def save_db(self):
        # Group by _SourceFile and save
        if self.df.empty:
            return

        # Ensure _SourceFile exists (for new rows)
        if "_SourceFile" not in self.df.columns:
            self.df["_SourceFile"] = self.local_db_name
            
        # Fill NaN source with local
        self.df["_SourceFile"] = self.df["_SourceFile"].replace("", self.local_db_name)
        self.df["_SourceFile"] = self.df["_SourceFile"].fillna(self.local_db_name)
        
        grouped = self.df.groupby("_SourceFile")
        
        for source_file, group_df in grouped:
            # content columns only
            save_df = group_df[self.columns]
            
            save_path = os.path.join(self.root_dir, source_file)
            try:
                save_df.to_excel(save_path, index=False)
            except Exception as e:
                print(f"Error saving {save_path}: {e}")

    def add_entry(self, metadata):
        # Ensure new entry has all columns
        row = {col: metadata.get(col, "") for col in self.columns}
        
        # Assign Source = Local DB
        row["_SourceFile"] = self.local_db_name
        
        # Handle RelPath
        abs_path = metadata.get("FilePath")
        if abs_path and os.path.isabs(abs_path):
            try:
                rel_path = os.path.relpath(abs_path, self.root_dir)
                row["FilePath"] = rel_path
            except ValueError:
                row["FilePath"] = abs_path
        
        new_row_df = pd.DataFrame([row])
        self.df = pd.concat([self.df, new_row_df], ignore_index=True)
        self.save_db()

    def get_filtered_data(self, filters):
        # Return a Filtered VIEW of the DF
        # We don't modify self.df here
        if self.df.empty:
            return self.df
            
        result = self.df.copy()
        
        for key, value in filters.items():
            if value and value != "No" and value != "None":
                # Assuming exact match for now, or use str.contains?
                # Using exact match for Radio buttons usually.
                # Ensure column exists
                if key in result.columns:
                    # Filter
                    result = result[result[key].astype(str) == value]
        
        return result
