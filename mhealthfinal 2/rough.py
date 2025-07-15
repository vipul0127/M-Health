import pandas as pd
import os
import numpy as np
from datetime import datetime
from scipy import signal

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

def calculate_ppg_metrics(ir_values, red_values, sampling_rate=30):
    """
    Calculate PPG metrics using IR and Red values with signal processing.
    """
    try:
        # Apply bandpass filter (0.5 - 4 Hz for heart rate range 30-240 BPM)
        nyquist = sampling_rate / 2
        low = 0.5 / nyquist
        high = 4.0 / nyquist
        b, a = signal.butter(2, [low, high], btype='band')
        
        # Filter signals
        ir_filtered = signal.filtfilt(b, a, ir_values)
        red_filtered = signal.filtfilt(b, a, red_values)
        
        # Calculate AC and DC components
        ir_ac = ir_filtered
        ir_dc = np.mean(ir_values)
        red_ac = red_filtered
        red_dc = np.mean(red_values)
        
        # Calculate R value (ratio of ratios)
        r_value = (np.std(red_ac)/red_dc) / (np.std(ir_ac)/ir_dc)
        
        # Calculate SpO2 (approximate formula)
        spo2 = 110 - 25 * r_value
        spo2 = np.clip(spo2, 0, 100)
        
        # Calculate standard PPG ratio
        ppg_ratio = ir_filtered / red_filtered
        
        return ppg_ratio, spo2, r_value
        
    except Exception as e:
        print(f"Error in PPG calculation: {e}")
        return np.zeros_like(ir_values), 0, 0

def generate_output_filename(input_file):
    """Generate unique output filename with timestamp."""
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "ppg_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return os.path.join(output_dir, f"{base_name}_PPG_{timestamp}.csv")

def process_ppg_data(input_file):
    try:
        output_file = generate_output_filename(input_file)
        print(f"Reading input file: {input_file}")
        
        # Read input data
        df = pd.read_csv(input_file)
        
        required_columns = ['Hour', 'Minute', 'Second', 'IR', 'Red']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Input file must contain columns: {required_columns}")
        
        
        # Calculate continuous time
        df['Time'] = df.apply(lambda row: calculate_continuous_time(row), axis=1)
        
        # Process signals in windows
        window_size = 30  # samples (1 second at 30 Hz)
        n_windows = len(df) // window_size
        
        results = []
        
        for i in range(n_windows):
            start_idx = i * window_size
            end_idx = (i + 1) * window_size
            
            window_data = df.iloc[start_idx:end_idx]
            
            # Calculate PPG metrics for the window
            ppg_values, spo2, r_value = calculate_ppg_metrics(
                window_data['IR'].values,
                window_data['Red'].values
            )
            
            # Store results with corresponding timestamps
            for j, ppg in enumerate(ppg_values):
                results.append({
                    'Time': window_data['Time'].iloc[j],
                    'PPG': round(float(ppg), 3),
                    'SpO2': round(float(spo2), 1),
                    'R_Value': round(float(r_value), 3)
                })
        
        # Create result DataFrame
        result_df = pd.DataFrame(results)
        
        print(f"Result DataFrame (first 5 rows):\n{result_df.head()}")
        print(f"Saving output to: {output_file}")
        
        # Save results
        result_df.to_csv(output_file, index=False)
        print(f"File saved successfully: {output_file}")
        
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
    output_file = process_ppg_data(input_file)
    
    if output_file:
        print("\nConversion completed successfully!")
    else:
        print("\nConversion failed. Please check the error messages above.")