#!/usr/bin/env python3
"""
CSV Schema Extractor for AI Processing
Outputs clean, structured schema data for machine processing
"""

import pandas as pd
import sys
import os
import re
import json
from pathlib import Path

def extract_table_name(filename):
    """Extract table name from CSV filename, removing timestamps and extensions"""
    base_name = Path(filename).stem
    # Remove timestamp patterns like _202507062323
    table_name = re.sub(r'_\d{8,}.*$', '', base_name)
    return table_name

def clean_column_name(col_name):
    """Clean column name for SQL compatibility"""
    # Replace special characters with underscores
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', str(col_name))
    # Remove multiple consecutive underscores
    clean_name = re.sub(r'_+', '_', clean_name)
    # Remove leading/trailing underscores
    clean_name = clean_name.strip('_')
    return clean_name

def infer_sqlite_type(pandas_dtype, sample_values):
    """Convert pandas dtype to SQLite type"""
    dtype_str = str(pandas_dtype).lower()
    
    if 'int' in dtype_str:
        return 'INTEGER'
    elif 'float' in dtype_str:
        return 'REAL'
    elif 'bool' in dtype_str:
        return 'INTEGER'
    elif 'datetime' in dtype_str or 'timestamp' in dtype_str:
        return 'TEXT'
    elif dtype_str == 'object':
        # Check if numeric values stored as text
        numeric_count = 0
        total_count = 0
        for val in sample_values:
            if pd.notna(val) and str(val).strip():
                total_count += 1
                try:
                    float(str(val))
                    numeric_count += 1
                except:
                    pass
                if total_count >= 10:  # Sample first 10 valid values
                    break
        
        if total_count > 0 and numeric_count / total_count > 0.8:
            return 'REAL'
    
    return 'TEXT'

def analyze_csv_schema(csv_file):
    """Analyze CSV and return clean schema data"""
    try:
        df = pd.read_csv(csv_file)
        
        table_name = extract_table_name(csv_file)
        
        columns = []
        for col in df.columns:
            columns.append({
                'original_name': col,
                'clean_name': clean_column_name(col),
                'data_type': infer_sqlite_type(df[col].dtype, df[col].head(10)),
                'null_count': int(df[col].isnull().sum()),
                'unique_count': int(df[col].nunique()),
                'sample_values': [str(v) for v in df[col].dropna().head(5).tolist()]
            })
        
        return {
            'table_name': table_name,
            'file_name': os.path.basename(csv_file),
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': columns
        }
        
    except Exception as e:
        return {'error': str(e)}

def generate_outputs(schema_data):
    """Generate different output formats"""
    if 'error' in schema_data:
        return {'error': schema_data['error']}
    
    # JSON format
    json_output = json.dumps(schema_data, indent=2)
    
    # SQL CREATE TABLE statement
    sql_columns = []
    for col in schema_data['columns']:
        sql_columns.append(f"    {col['clean_name']} {col['data_type']}")
    
    create_table_sql = f"CREATE TABLE {schema_data['table_name']} (\n" + ",\n".join(sql_columns) + "\n);"
    
    # CSV summary format
    csv_summary = "column_name,data_type,null_count,unique_count\n"
    for col in schema_data['columns']:
        csv_summary += f"{col['clean_name']},{col['data_type']},{col['null_count']},{col['unique_count']}\n"
    
    return {
        'json': json_output,
        'sql': create_table_sql,
        'csv_summary': csv_summary,
        'schema_data': schema_data
    }

def process_folder(folder_path, output_format='json'):
    """Process all CSV files in a folder"""
    csv_files = []
    
    # Find all CSV files in the folder
    for file_path in Path(folder_path).glob("*.csv"):
        csv_files.append(str(file_path))
    
    if not csv_files:
        print(json.dumps({'error': 'No CSV files found in folder'}))
        return
    
    all_schemas = []
    
    for csv_file in sorted(csv_files):
        schema_data = analyze_csv_schema(csv_file)
        if 'error' not in schema_data:
            all_schemas.append(schema_data)
        else:
            print(f"Error processing {csv_file}: {schema_data['error']}", file=sys.stderr)
    
    # Output all schemas
    if output_format == 'json':
        print(json.dumps(all_schemas, indent=2))
    elif output_format == 'sql':
        for schema in all_schemas:
            outputs = generate_outputs(schema)
            print(outputs['sql'])
            print()  # Empty line between tables
    elif output_format == 'csv':
        print("table_name,column_name,data_type,null_count,unique_count")
        for schema in all_schemas:
            for col in schema['columns']:
                print(f"{schema['table_name']},{col['clean_name']},{col['data_type']},{col['null_count']},{col['unique_count']}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file: python csv_analyzer.py <csv_file> [--format json|sql|csv|all]")
        print("  Folder:      python csv_analyzer.py --folder <folder_path> [--format json|sql|csv]")
        print("Examples:")
        print("  python csv_analyzer.py email_activity_202507062323.csv --format json")
        print("  python csv_analyzer.py --folder ./csv_files --format json")
        sys.exit(1)
    
    # Check if processing a folder
    if sys.argv[1] == '--folder':
        if len(sys.argv) < 3:
            print("Please specify folder path after --folder")
            sys.exit(1)
        
        folder_path = sys.argv[2]
        output_format = 'json'  # default
        
        if len(sys.argv) > 3 and sys.argv[3] == '--format':
            if len(sys.argv) > 4:
                output_format = sys.argv[4].lower()
        
        if not os.path.exists(folder_path):
            print(json.dumps({'error': f'Folder not found: {folder_path}'}))
            sys.exit(1)
        
        process_folder(folder_path, output_format)
        return
    
    # Process single file (original functionality)
    csv_file = sys.argv[1]
    output_format = 'json'  # default
    
    if len(sys.argv) > 2 and sys.argv[2] == '--format':
        if len(sys.argv) > 3:
            output_format = sys.argv[3].lower()
    
    if not os.path.exists(csv_file):
        print(json.dumps({'error': f'File not found: {csv_file}'}))
        sys.exit(1)
    
    # Analyze schema
    schema_data = analyze_csv_schema(csv_file)
    outputs = generate_outputs(schema_data)
    
    if 'error' in outputs:
        print(json.dumps(outputs))
        return
    
    # Output in requested format
    if output_format == 'json':
        print(outputs['json'])
    elif output_format == 'sql':
        print(outputs['sql'])
    elif output_format == 'csv':
        print(outputs['csv_summary'])
    elif output_format == 'all':
        print("=== JSON ===")
        print(outputs['json'])
        print("\n=== SQL ===")
        print(outputs['sql'])
        print("\n=== CSV SUMMARY ===")
        print(outputs['csv_summary'])
    else:
        print(outputs['json'])  # default to json

if __name__ == "__main__":
    main()