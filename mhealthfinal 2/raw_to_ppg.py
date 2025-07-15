import pandas as pd
import os
from datetime import datetime

def calculate_continuous_time(row):
    """Calculate time in HH:MM:SS.MMM format using Hour, Minute, Second, and Millisecond."""
    try:
        hour = int(row['Hour'])
        minute = int(row['Minute'])
        second = int(row['Second'])
        millisecond = int(row['Millisecond'])

        # Format time in HH:MM:SS.MMM (24-hour format with three-digit milliseconds)
        return f"{hour:02}:{minute:02}:{second:02}.{millisecond:03}"
    except Exception as e:
        raise ValueError(f"Error in time calculation: {e}")

def calculate_ppg(ir, red):
    """Calculate PPG value using IR and Red values."""
    if ir == 0 or red == 0:
        return 0
    try:
        ppg = red/ir
        return round(ppg, 3)
    except Exception as e:
        return 0

def generate_output_filename(input_file):
    """Generate unique output filename with timestamp."""
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "ppg_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file = os.path.join(output_dir, f"{base_name}_PPG_{timestamp}.csv")
    return output_file

def convert_to_ppg(input_file):
    try:
        output_file = generate_output_filename(input_file)
        print(f"Reading input file: {input_file}")

        df = pd.read_csv(input_file)

        required_columns = ['Hour', 'Minute', 'Second', 'Millisecond', 'IR', 'Red']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Input file must contain columns: {required_columns}")

        df['Time'] = df.apply(calculate_continuous_time, axis=1)
        df['PPG'] = df.apply(lambda row: calculate_ppg(row['IR'], row['Red']), axis=1)

        result_df = df[['Time', 'PPG']]

        print(f"Result DataFrame (first 5 rows):\n{result_df.head()}")
        print(f"Saving output to: {output_file}")

        try:
            result_df.to_csv(output_file, index=False)
            print(f"File saved successfully: {output_file}")
        except Exception as e:
            print(f"Error while saving file: {e}")

        return output_file

    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None

if __name__ == "__main__":
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