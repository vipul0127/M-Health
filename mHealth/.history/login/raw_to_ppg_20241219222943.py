import pandas as pd
import numpy as np
from datetime import timedelta

def seconds_to_hhmmss(seconds):
    """Convert seconds to HH:MM:SS format"""
    return str(timedelta(seconds=int(seconds)))

def calculate_ppg(ir, red):
    """
    Calculate PPG value using IR and Red values
    Using the ratio of AC/DC components of the signal
    """
    # Ensure values are not zero to avoid division issues
    if ir == 0 or red == 0:
        return 0
        
    # Calculate AC/DC ratio
    # This is a simplified version of PPG calculation
    # PPG = -log(IR/Red) which is proportional to blood volume changes
    try:
        ppg = -np.log(ir/red)
        return round(ppg, 3)
    except:
        return 0

def convert_to_ppg(input_file, output_file):
    try:
        # Read the input CSV file
        df = pd.read_csv(input_file)
        
        # Verify required columns exist
        required_columns = ['Time', 'IR', 'Red']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Input file must contain columns: {required_columns}")
        
        # Convert time to HH:MM:SS format
        df['Time'] = df['Time'].apply(seconds_to_hhmmss)
        
        # Calculate PPG values
        df['PPG'] = df.apply(lambda row: calculate_ppg(row['IR'], row['Red']), axis=1)
        
        # Create new dataframe with only Time and PPG
        result_df = df[['Time', 'PPG']]
        
        # Save to output file
        result_df.to_csv(output_file, index=False)
        print(f"Successfully converted data and saved to {output_file}")
        
        # Print some basic statistics
        print("\nData Statistics:")
        print(f"Total number of readings: {len(result_df)}")
        print(f"Time range: {result_df['Time'].iloc[0]} to {result_df['Time'].iloc[-1]}")
        print(f"PPG value range: {result_df['PPG'].min():.3f} to {result_df['PPG'].max():.3f}")
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    # Example usage
    input_file = "input.csv"  # Your input file name
    output_file = "output.csv"  # Your output file name
    
    print("Starting conversion process...")
    convert_to_ppg(input_file, output_file)