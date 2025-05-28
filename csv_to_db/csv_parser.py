import pandas as pd
from datetime import datetime
from dto.bpr_scrapping_schema import BprScrappingSchema
from typing import List, Dict, Any

def parse_bpr_scrapping_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse BPR Scrapping CSV file and validate data using schema
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        List[Dict[str, Any]]: List of validated BPR Scrapping data
        
    Raises:
        ValueError: If CSV parsing or validation fails
    """
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Convert column names to snake_case if needed
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Initialize schema
        schema = BprScrappingSchema()
        validated_data = []
        
        # Process each row
        for _, row in df.iterrows():
            # Convert row to dict and prepare data
            data = row.to_dict()
            
            # Add waktu_diambil if not present
            if 'waktu_diambil' not in data:
                data['waktu_diambil'] = datetime.utcnow()
                
            # Convert numeric values
            numeric_fields = ['asset', 'kyd', 'total_hutang', 'laba_tahun_lalu', 
                            'laba_saat_ini', 'npl_net', 'kpmm', 'ldr', 'roa', 
                            'kap', 'ppap', 'bopo', 'cr']
            
            for field in numeric_fields:
                if field in data:
                    # Remove any currency symbols and commas
                    if isinstance(data[field], str):
                        data[field] = data[field].replace('Rp', '').replace(',', '')
                    # Convert to float
                    try:
                        data[field] = float(data[field])
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid numeric value in field {field}")
            
            # Validate data against schema
            validated = schema.load(data)
            validated_data.append(validated)
            
        return validated_data
        
    except Exception as e:
        raise ValueError(f"Error parsing CSV file: {str(e)}")
