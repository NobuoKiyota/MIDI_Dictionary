import os
import shutil

def package():
    dist_dir = "dist_temp"
    app_dir = os.path.join(dist_dir, "MIDI_Dictionary")
    
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
        
    os.makedirs(app_dir)
    
    # Files to copy
    files = [
        "main.py", "data_manager.py", "midi_utils.py",
        "config_manager.py", "ui_constants.py", 
        "requirements.txt", "setup_and_run.bat"
    ]
    
    for f in files:
        if os.path.exists(f):
            print(f"Copying {f}...")
            shutil.copy2(f, app_dir)
        else:
            print(f"Warning: {f} not found!")
            
    # Directories to copy
    if os.path.exists("ui"):
        print("Copying ui folder...")
        shutil.copytree("ui", os.path.join(app_dir, "ui"))
        
    # Empty MIDI_Library
    print("Creating empty MIDI_Library...")
    os.makedirs(os.path.join(app_dir, "MIDI_Library"), exist_ok=True)
    
    # README
    print("Creating README.txt...")
    with open(os.path.join(app_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write("MIDI Dictionary v1.0\n\n")
        f.write("【使い方】\n")
        f.write("1. このzipを解凍してください。\n")
        f.write("2. 'setup_and_run.bat' をダブルクリックして実行してください。\n")
        f.write("   自動的に必要なライブラリ(PySide6など)がインストールされ、アプリが起動します。\n\n")
        f.write("注意: 実行にはPythonがインストールされている必要があります。\n")
    
    # Zip
    output_filename = "MIDI_Dictionary_Package"
    print(f"Zipping to {output_filename}.zip...")
    shutil.make_archive(output_filename, 'zip', root_dir=dist_dir)
    
    print("Done!")
    
    # Cleanup
    shutil.rmtree(dist_dir)

if __name__ == "__main__":
    package()
