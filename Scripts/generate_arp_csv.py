import pandas as pd
import os

def create_initial_arp_excel():
    file_path = "arpeggio_patterns.xlsx"
    
    # Define the columns as requested
    # style_name | sequence | gate_ratios | velocity_mults | swing_amount
    
    data = [
        {
            "style_name": "LoFi_01",
            "sequence": "0,-1,1,2,-1,0,1,3,0,-1,1,2,-1,0,1,3", # 16 steps
            "gate_ratios": "1.0,0,1.2,1.2,0,1.0,1.2,1.2,1.0,0,1.2,1.2,0,1.0,1.2,1.2",
            "velocity_mults": "0.8,0,0.9,0.7,0,0.8,0.9,0.7,0.8,0,0.9,0.7,0,0.8,0.9,0.7",
            "swing_amount": 0.03 # 30ms or ratio? Let's assume seconds (30ms) or maybe fractional beat? 
                                 # User said "swing_amount... starting time slightly behind". 
                                 # Standard swing is often a ratio, but user mentioned 5ms for strum. 
                                 # Let's use seconds for now as the user mentioned "laid back timing (+30-50ms)" before.
                                 # Or better, let's stick to the user's "swing_amount" column instruction.
        },
        {
            "style_name": "Trance_Gate",
            "sequence": "0,1,2,0, 1,2,0,1, 2,0,1,2, 0,1,2,0",
            "gate_ratios": "0.6,0.6,0.6,0.6, 0.6,0.6,0.6,0.6, 0.6,0.6,0.6,0.6, 0.6,0.6,0.6,0.6",
            "velocity_mults": "1.2,0.8,1.0,0.8, 1.2,0.8,1.0,0.8, 1.2,0.8,1.0,0.8, 1.2,0.8,1.0,0.8",
            "swing_amount": 0.0
        },
        {
             "style_name": "Strum_Slow",
             "sequence": "0&1&2, -1, -1, -1, 0&1&2, -1, -1, -1, 0&1&2, -1, -1, -1, 0&1&2, -1, -1, -1",
             "gate_ratios": "2.0,0,0,0, 2.0,0,0,0, 2.0,0,0,0, 2.0,0,0,0", # Long sustain
             "velocity_mults": "1.0,0,0,0, 1.0,0,0,0, 1.0,0,0,0, 1.0,0,0,0",
             "swing_amount": 0.0
        }
    ]
    
    df = pd.DataFrame(data)
    
    # Save to Excel
    try:
        df.to_excel(file_path, index=False)
        print(f"Successfully created {file_path}")
    except Exception as e:
        print(f"Error creating Excel: {e}")

if __name__ == "__main__":
    create_initial_arp_excel()
