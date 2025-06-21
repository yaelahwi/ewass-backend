import pandas as pd
from typing import List, Dict, Any
from dto.bpr_lainnya_schema import BprLainnyaSchema
from dto.rac_schema import RACSchema


def parse_bpr_lainnya_xlsx(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse BPR Lainnya XLSX file and validate data using schema
    
    Args:
        file_path (str): Path to the XLSX file
        
    Returns:
        List[Dict[str, Any]]: List of validated BPR Lainnya data
        
    Raises:
        ValueError: If XLSX parsing or validation fails
    """
    try:
        # Read XLSX file
        df = pd.read_excel(file_path)
        
        # Convert column names to snake_case if needed
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]

        # Convert 'sandi' column to string
        if 'sandi' in df.columns:
            df['sandi'] = df['sandi'].astype(str)
        
        # Initialize schema
        schema = BprLainnyaSchema()
        validated_data = []
        
        # Process each row
        for _, row in df.iterrows():
            # Convert row to dict
            data = row.to_dict()
            
            # Clean phone number
            if 'no_telepon' in data:
                # Remove any non-digit characters
                data['no_telepon'] = ''.join(filter(str.isdigit, str(data['no_telepon'])))
            
            # Clean email
            if 'email' in data:
                data['email'] = str(data['email']).strip().lower()
            
            # Validate data against schema
            validated = schema.load(data)
            validated_data.append(validated)
            
        return validated_data
        
    except Exception as e:
        raise ValueError(f"Error parsing XLSX file: {str(e)}")

def parse_rac_xlsx(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse D entity data from XLSX file and validate using schema
    
    Args:
        file_path (str): Path to the XLSX file
        
    Returns:
        List[Dict[str, Any]]: List of validated D entity data
        
    Raises:
        ValueError: If XLSX parsing or validation fails
    """
    try:
        # Read specific sheet from XLSX file
        df = pd.read_excel(file_path, sheet_name='rac')
        
        # Convert column names to snake_case if needed
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Initialize schema
        from dto.rac_schema import RACSchema
        schema = RACSchema()
        validated_data = []
        
        # Process each row
        for _, row in df.iterrows():
            # Convert row to dict and prepare data
            data = row.to_dict()
            
            # Convert numeric values
            numeric_fields = ['npl_net', 'laba_sebelum', 'laba_sekarang', 'kap', 
                            'kpmm', 'asset', 'roa', 'bopo']
            
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
        raise ValueError(f"Error parsing XLSX file for D entity: {str(e)}")
