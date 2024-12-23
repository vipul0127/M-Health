import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

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
    try:
        ppg = -np.log(ir/red)
        return round(ppg, 3)
    except:
        return 0

def generate_output_filename(input_file):
    """Generate unique output filename with timestamp"""
    # Get the input file name without extension
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory if it doesn't exist
    output_dir = "ppg_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate output filename
    output_file = os.path.join(output_dir, f"{base_name}_PPG_{timestamp}.csv")
    return output_file

def convert_to_ppg(input_file):
    try:
        # Generate output filename
        output_file = generate_output_filename(input_file)
        
        print(f"Reading input file: {input_file}")
        
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
        print(f"\nSuccessfully converted data and saved to:")
        print(f"{output_file}")
        
        # Print some basic statistics
        print("\nData Statistics:")
        print(f"Total number of readings: {len(result_df)}")
        print(f"Time range: {result_df['Time'].iloc[0]} to {result_df['Time'].iloc[-1]}")
        print(f"PPG value range: {result_df['PPG'].min():.3f} to {result_df['PPG'].max():.3f}")
        
        return output_file
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None

if __name__ == "__main__":
    # Get input file from user
    while True:
        input_file = input("Enter the path to your input CSV file: ").strip()
        if os.path.exists(input_file):
            break
        print("File not found. Please enter a valid file path.")
    
    print("\nStarting conversion process...")
    output_file = convert_to_ppg(input_file)
    
    if output_file:
        print("\nConversion completed successfully!")
    else:
        print("\nConversion failed. Please check the error messages above.")