import pandas as pd
import os
import time

def process_local_csv_pandas(input_path, output_path):
    """
    Cleans a heavy CSV by keeping only 'Date' and 'Review' columns.
    Optimized for Pandas by loading ONLY required columns.
    """
    print(f"🚀 Starting Pandas process for: {input_path}")
    start_time = time.time()

    if not os.path.exists(input_path):
        print(f"❌ Error: File '{input_path}' not found.")
        return

    try:
        # Optimization: usecols ensures we don't load the other 998+ columns into RAM
        # low_memory=False prevents DtypeWarnings on massive files
        df = pd.read_csv(
            input_path, 
            usecols=["Date", "Review"], 
            low_memory=False
        )

        # Basic cleaning: remove empty feedback rows
        df.dropna(subset=["Review"], inplace=True)

        # Save to local file
        df.to_csv(output_path, index=False)
        
        duration = time.time() - start_time
        print(f"✅ Success! Cleaned file saved to: {output_path}")
        print(f"⏱️ Time taken: {duration:.2f} seconds")
        print(f"📊 Final row count: {len(df)}")

    except ValueError as e:
        print(f"❌ Column Error: {e}")
        print("Tip: Make sure the columns are exactly 'Date' and 'Review'.")
    except Exception as e:
        print(f"❌ Processing failed: {e}")

if __name__ == "__main__":
    MY_FILE = "final.csv"
    OUTPUT_FILE = "cleaned_standard_format_pandas.csv"
    
    process_local_csv_pandas(MY_FILE, OUTPUT_FILE)