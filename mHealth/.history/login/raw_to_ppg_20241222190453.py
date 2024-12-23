import pandas as pd
import numpy as np
from datetime import timedelta
import os

def milliseconds_to_hhmmss(milliseconds):
    """Convert milliseconds to HH:MM:SS.MSSSS format"""
    seconds, ms = divmod(milliseconds, 1000)  # Separate seconds and milliseconds
    microseconds = ms * 1000  # Convert milliseconds to microseconds
    time_delta = timedelta(seconds=seconds, microseconds=microseconds)
    return str(time_delta)

def calculate_ppg(ir, red):
    """
    Calculate PPG value using IR and Red values
    Using the ratio of AC/DC components of the signal
    """
    if ir == 0 or red == 0:
        return 0
    
    try:
        ppg = -np.log(ir / red)
        return round(ppg, 3)
    except:
        return 0

def generate_output_filename():
    """Generate unique output filename with timestamp"""
    output_dir = "ppg_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return os.path.join(output_dir, "output_ppg.csv")

def convert_to_ppg(input_file):
    try:
        # Generate output filename
        output_file = generate_output_filename()
        
        print(f"Reading input file: {input_file}")
        
        # Read the input CSV file
        df = pd.read_csv(input_file, delim_whitespace=True)
        
        # Verify required columns exist
        required_columns = ['Time', 'IR', 'Red']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Input file must contain columns: {required_columns}")
        
        # Convert time in milliseconds to HH:MM:SS format
        df['Time'] = df['Time'].apply(lambda x: milliseconds_to_hhmmss(x * 10))
        
        # Calculate PPG values
        df['PPG'] = df.apply(lambda row: calculate_ppg(row['IR'], row['Red']), axis=1)
        
        # Create a new dataframe with specified columns
        result_df = pd.DataFrame({
            'GSR': [None] * len(df),
            'CBT(degC)': [None] * len(df),
            'PPG': df['PPG'],
            'ECG': [None] * len(df),
            'Sleep': [None] * len(df),
            'Time': df['Time']
        })
        
        # Save to output file
        result_df.to_csv(output_file, index=False)
        print(f"\nSuccessfully converted data and saved to:")
        print(f"{output_file}")
        
        return output_file
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None

if __name__ == "__main__":
    # Sample input
    input_file = "input.csv"  # Replace this with the actual path to your file
    print("\nStarting conversion process...")
    output_file = convert_to_ppg(input_file)
    
    if output_file:
        print("\nConversion completed successfully!")
    else:
        print("\nConversion failed. Please check the error messages above.")
