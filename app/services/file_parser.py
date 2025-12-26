"""File parsing service with streaming support for large files"""
import csv
import json
import io
from typing import AsyncGenerator, Dict, Any, List
from fastapi import UploadFile
import aiofiles


class FileParserService:
    """Service for parsing CSV and JSON files efficiently"""
    
    CHUNK_SIZE = 1000  # Process records in chunks of 1000
    
    @staticmethod
    async def detect_file_type(filename: str) -> str:
        """Detect file type from filename"""
        if filename.lower().endswith('.csv'):
            return 'csv'
        elif filename.lower().endswith('.json'):
            return 'json'
        else:
            raise ValueError("Unsupported file type. Only CSV and JSON are supported.")
    
    @staticmethod
    async def parse_csv_streaming(file: UploadFile) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Parse CSV file in streaming mode to avoid loading entire file in memory.
        Yields records one by one.
        """
        # Read file content
        content = await file.read()
        # Reset file pointer
        await file.seek(0)
        
        # Decode content
        text_content = content.decode('utf-8')
        
        # Use StringIO to create a file-like object
        csv_file = io.StringIO(text_content)
        
        # Create CSV reader
        reader = csv.DictReader(csv_file)
        
        for row in reader:
            # Clean up row data - remove empty strings and strip whitespace
            cleaned_row = {
                k.strip(): v.strip() if v else None 
                for k, v in row.items()
            }
            yield cleaned_row
    
    @staticmethod
    async def parse_json_streaming(file: UploadFile) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Parse JSON file in streaming mode.
        Supports both array of objects and newline-delimited JSON (NDJSON).
        """
        content = await file.read()
        await file.seek(0)
        
        text_content = content.decode('utf-8').strip()
        
        # Try to parse as JSON array first
        try:
            data = json.loads(text_content)
            
            if isinstance(data, list):
                # Array of objects
                for item in data:
                    yield item
            elif isinstance(data, dict):
                # Single object - yield as is
                yield data
            else:
                raise ValueError("JSON must be an array of objects or a single object")
        except json.JSONDecodeError:
            # Try parsing as NDJSON (newline-delimited JSON)
            lines = text_content.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON line: {line[:50]}... Error: {str(e)}")
    
    @staticmethod
    async def parse_file(file: UploadFile) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Parse file based on its type.
        Returns async generator of records.
        """
        file_type = await FileParserService.detect_file_type(file.filename)
        
        if file_type == 'csv':
            async for record in FileParserService.parse_csv_streaming(file):
                yield record
        elif file_type == 'json':
            async for record in FileParserService.parse_json_streaming(file):
                yield record
    
    @staticmethod
    async def chunk_records(records: AsyncGenerator[Dict[str, Any], None], chunk_size: int = CHUNK_SIZE) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        Batch records into chunks for efficient database insertion.
        """
        chunk = []
        async for record in records:
            chunk.append(record)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        
        # Yield remaining records
        if chunk:
            yield chunk
