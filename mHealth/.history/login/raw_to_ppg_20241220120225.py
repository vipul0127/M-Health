def milliseconds_to_hhmmss(milliseconds):
    """Convert milliseconds to HH:MM:SS format"""
    seconds = int(milliseconds / 1000)  # Convert milliseconds to seconds
    return str(timedelta(seconds=seconds))

# Updated time conversion in the main function
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
        
        # Convert time in milliseconds to HH:MM:SS format
        df['Time'] = df['Time'].apply(milliseconds_to_hhmmss)
        
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
