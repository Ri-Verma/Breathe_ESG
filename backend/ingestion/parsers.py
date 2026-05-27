"""
Production-ready data parsers for ESG ingestion.
Handles three enterprise data sources: SAP, Utility Portal, and Travel API.
"""
import csv
import json
import logging
from io import StringIO
from datetime import datetime
from dateutil import parser as date_parser
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# ============================================================================
# UNIT CONVERSION MATRIX
# ============================================================================

UNIT_CONVERSIONS = {
    # Fuel conversions (all to Liters)
    'GAL': 3.78541,      # US Gallon to Liters
    'L': 1.0,             # Already in Liters
    'LITER': 1.0,         # Variant
    'LITRE': 1.0,         # British spelling
    # Could expand to: barrel oil, MWh, therms, etc.
}

# ============================================================================
# AIRPORT DISTANCE LOOKUP (Mock for Scope 3 calculations)
# ============================================================================

AIRPORT_DISTANCES = {
    # Transatlantic
    ('JFK', 'LHR'): 5570,
    ('LHR', 'JFK'): 5570,
    ('LAX', 'LHR'): 8616,
    ('LHR', 'LAX'): 8616,
    
    # US Domestic
    ('SFO', 'SEA'): 680,
    ('SEA', 'SFO'): 680,
    ('LAX', 'ORD'): 2015,
    ('ORD', 'LAX'): 2015,
    ('JFK', 'MIA'): 1280,
    ('MIA', 'JFK'): 1280,
    ('ATL', 'MIA'): 661,
    ('MIA', 'ATL'): 661,
    
    # International
    ('BOS', 'DUB'): 3149,
    ('DUB', 'BOS'): 3149,
    ('ORD', 'FRA'): 4391,
    ('FRA', 'ORD'): 4391,
    ('LHR', 'DXB'): 5247,
    ('DXB', 'LHR'): 5247,
    ('SYD', 'AKL'): 2159,
    ('AKL', 'SYD'): 2159,
}

# ============================================================================
# SAP CSV PARSER
# ============================================================================

def parse_sap_csv(file_content: str, tenant_id: int) -> Tuple[List[Dict], List[Dict]]:
    """
    Parse SAP flat file CSV export with messy German headers and mixed date formats.
    
    Expected headers: DOCNUM, DATUM, WERKS, MATNR, MAKTX, MENGE, MEINS
    
    Args:
        file_content: Raw file content as string
        tenant_id: The Tenant ID to associate records with
        
    Returns:
        Tuple of (successful_records, flagged_records) where each record is a dict
        ready to instantiate an EmissionRecord and RawIngestionLog
    """
    successful_records = []
    flagged_records = []
    
    try:
        # Parse CSV with flexible whitespace handling
        reader = csv.DictReader(StringIO(file_content))
        rows = list(reader)
        
        if not rows:
            logger.warning("SAP CSV file is empty")
            return [], []
        
        for row_idx, row in enumerate(rows, start=2):  # Start at 2 (skip header)
            try:
                # Extract fields
                doc_num = row.get('DOCNUM', '').strip()
                datum_str = row.get('DATUM', '').strip()
                werks = row.get('WERKS', '').strip()
                matnr = row.get('MATNR', '').strip()
                maktx = row.get('MAKTX', '').strip()
                menge_str = row.get('MENGE', '').strip()
                meins = row.get('MEINS', '').strip().upper()
                
                # Validation flags
                issues = []
                
                # Parse messy date
                if not datum_str:
                    issues.append("Missing DATUM (date)")
                    activity_date = None
                else:
                    try:
                        activity_date = date_parser.parse(datum_str).date()
                    except Exception as e:
                        issues.append(f"Invalid date format: {datum_str} ({str(e)})")
                        activity_date = None
                
                # Parse quantity
                if not menge_str:
                    issues.append("Missing MENGE (quantity)")
                    original_value = None
                else:
                    try:
                        original_value = float(menge_str)
                    except ValueError:
                        issues.append(f"Invalid quantity: {menge_str}")
                        original_value = None
                
                # Validate unit
                if not meins:
                    issues.append("Missing MEINS (unit)")
                    original_unit = None
                elif meins not in UNIT_CONVERSIONS:
                    issues.append(f"Unrecognized unit: {meins}")
                    original_unit = meins
                else:
                    original_unit = meins
                
                # Normalize value
                normalized_value = None
                if original_value is not None and original_unit and original_unit in UNIT_CONVERSIONS:
                    normalized_value = original_value * UNIT_CONVERSIONS[original_unit]
                
                # Map to Scope 1 (Direct Fuel)
                scope = 1
                category = _infer_fuel_category(maktx)
                
                record = {
                    'tenant_id': tenant_id,
                    'scope': scope,
                    'category': category,
                    'activity_date': activity_date,
                    'original_value': original_value,
                    'original_unit': original_unit,
                    'normalized_value': normalized_value,
                    'normalized_unit': 'L',  # All fuel normalized to Liters
                    'status': 'FLAGGED' if issues else 'PENDING',
                    'raw_payload': {
                        'DOCNUM': doc_num,
                        'DATUM': datum_str,
                        'WERKS': werks,
                        'MATNR': matnr,
                        'MAKTX': maktx,
                        'MENGE': menge_str,
                        'MEINS': meins,
                    },
                    'issues': issues,
                }
                
                if issues:
                    flagged_records.append(record)
                else:
                    successful_records.append(record)
                    
            except Exception as e:
                logger.error(f"SAP CSV row {row_idx} parsing error: {str(e)}")
                flagged_records.append({
                    'tenant_id': tenant_id,
                    'raw_payload': dict(row),
                    'status': 'FLAGGED',
                    'issues': [f"Critical parsing error: {str(e)}"],
                })
    
    except Exception as e:
        logger.error(f"SAP CSV file parsing failed: {str(e)}")
        raise
    
    return successful_records, flagged_records


# ============================================================================
# UTILITY BILL CSV PARSER
# ============================================================================

def parse_utility_csv(file_content: str, tenant_id: int) -> Tuple[List[Dict], List[Dict]]:
    """
    Parse utility billing CSV with missing peak kWh fields and cross-month billing periods.
    
    Expected headers: Meter_ID, Building_Code, Billing_Start_Date, Billing_End_Date, 
                      Total_kWh, Peak_kWh, OffPeak_kWh, Amount_Billed
    
    Args:
        file_content: Raw file content as string
        tenant_id: The Tenant ID to associate records with
        
    Returns:
        Tuple of (successful_records, flagged_records)
    """
    successful_records = []
    flagged_records = []
    
    try:
        reader = csv.DictReader(StringIO(file_content))
        rows = list(reader)
        
        if not rows:
            logger.warning("Utility CSV file is empty")
            return [], []
        
        for row_idx, row in enumerate(rows, start=2):
            try:
                # Extract fields
                meter_id = row.get('Meter_ID', '').strip()
                building_code = row.get('Building_Code', '').strip()
                start_date_str = row.get('Billing_Start_Date', '').strip()
                end_date_str = row.get('Billing_End_Date', '').strip()
                total_kwh_str = row.get('Total_kWh', '').strip()
                peak_kwh_str = row.get('Peak_kWh', '').strip()
                offpeak_kwh_str = row.get('OffPeak_kWh', '').strip()
                
                issues = []
                
                # Parse dates
                if not start_date_str or not end_date_str:
                    issues.append("Missing billing date range")
                    activity_date = None
                else:
                    try:
                        start_date = date_parser.parse(start_date_str).date()
                        end_date = date_parser.parse(end_date_str).date()
                        # Use end date as the activity date
                        activity_date = end_date
                    except Exception as e:
                        issues.append(f"Invalid date format: {str(e)}")
                        activity_date = None
                
                # Parse total consumption
                if not total_kwh_str:
                    issues.append("Missing Total_kWh")
                    original_value = None
                else:
                    try:
                        original_value = float(total_kwh_str)
                    except ValueError:
                        issues.append(f"Invalid Total_kWh: {total_kwh_str}")
                        original_value = None
                
                # Handle missing peak kWh (common data quality issue)
                if not peak_kwh_str:
                    logger.debug(f"Meter {meter_id} missing Peak_kWh, calculating from total")
                    peak_kwh = None  # Will flag if critical
                else:
                    try:
                        peak_kwh = float(peak_kwh_str)
                    except ValueError:
                        peak_kwh = None
                
                # Parse off-peak (often present when peak is missing)
                if not offpeak_kwh_str:
                    offpeak_kwh = None
                else:
                    try:
                        offpeak_kwh = float(offpeak_kwh_str)
                    except ValueError:
                        offpeak_kwh = None
                
                # Normalize: kWh -> kWh (no conversion needed)
                normalized_value = original_value
                
                # Scope 2 (Indirect - Electricity)
                scope = 2
                category = f"Electricity - {building_code}"
                
                record = {
                    'tenant_id': tenant_id,
                    'scope': scope,
                    'category': category,
                    'activity_date': activity_date,
                    'original_value': original_value,
                    'original_unit': 'kWh',
                    'normalized_value': normalized_value,
                    'normalized_unit': 'kWh',
                    'status': 'FLAGGED' if issues else 'PENDING',
                    'raw_payload': {
                        'Meter_ID': meter_id,
                        'Building_Code': building_code,
                        'Billing_Start_Date': start_date_str,
                        'Billing_End_Date': end_date_str,
                        'Total_kWh': total_kwh_str,
                        'Peak_kWh': peak_kwh_str,
                        'OffPeak_kWh': offpeak_kwh_str,
                    },
                    'issues': issues,
                }
                
                # Flag if missing both peak and offpeak but have total
                if original_value and not peak_kwh and not offpeak_kwh:
                    issues.append("Missing both peak and offpeak kWh; cannot disaggregate")
                    record['status'] = 'FLAGGED'
                
                if issues:
                    flagged_records.append(record)
                else:
                    successful_records.append(record)
                    
            except Exception as e:
                logger.error(f"Utility CSV row {row_idx} parsing error: {str(e)}")
                flagged_records.append({
                    'tenant_id': tenant_id,
                    'raw_payload': dict(row),
                    'status': 'FLAGGED',
                    'issues': [f"Critical parsing error: {str(e)}"],
                })
    
    except Exception as e:
        logger.error(f"Utility CSV file parsing failed: {str(e)}")
        raise
    
    return successful_records, flagged_records


# ============================================================================
# TRAVEL API JSON PARSER
# ============================================================================

def parse_travel_json(file_content: str, tenant_id: int) -> Tuple[List[Dict], List[Dict]]:
    """
    Parse Navan Travel API JSON response with airport codes and no distances.
    Calculates distances from mock AIRPORT_DISTANCES lookup.
    
    Expected structure:
    {
      "api_provider": "navan_mock",
      "export_date": "2024-01-31T00:00:00Z",
      "data": [
        {
          "trip_id": "TRP-xxxxx",
          "employee_id": "EMP-xxx",
          "status": "COMPLETED|CANCELLED",
          "segments": [
            {
              "mode": "FLIGHT|TRAIN|GROUND",
              "origin_airport": "JFK",
              "destination_airport": "LHR",
              "cabin_class": "ECONOMY|BUSINESS|PREMIUM ECONOMY",
              "departure_time": "2024-01-05T08:00:00Z"
            }
          ]
        }
      ]
    }
    
    Args:
        file_content: Raw JSON file content as string
        tenant_id: The Tenant ID to associate records with
        
    Returns:
        Tuple of (successful_records, flagged_records)
    """
    successful_records = []
    flagged_records = []
    
    try:
        payload = json.loads(file_content)
        trips = payload.get('data', [])
        
        if not trips:
            logger.warning("Travel API JSON contains no trip data")
            return [], []
        
        for trip_idx, trip in enumerate(trips):
            try:
                trip_id = trip.get('trip_id', f'UNKNOWN_{trip_idx}')
                employee_id = trip.get('employee_id', 'UNKNOWN')
                trip_status = trip.get('status', 'UNKNOWN')
                segments = trip.get('segments', [])
                
                if trip_status != 'COMPLETED':
                    logger.info(f"Skipping trip {trip_id} with status {trip_status}")
                    continue
                
                if not segments:
                    logger.warning(f"Trip {trip_id} has no segments")
                    continue
                
                for seg_idx, segment in enumerate(segments):
                    try:
                        mode = segment.get('mode', '').strip().upper()
                        origin = segment.get('origin_airport', '').strip().upper()
                        destination = segment.get('destination_airport', '').strip().upper()
                        cabin = segment.get('cabin_class', '').strip()
                        departure_str = segment.get('departure_time', '')
                        
                        issues = []
                        
                        # Parse departure date
                        if not departure_str:
                            issues.append("Missing departure_time")
                            activity_date = None
                        else:
                            try:
                                activity_date = date_parser.parse(departure_str).date()
                            except Exception as e:
                                issues.append(f"Invalid departure time: {str(e)}")
                                activity_date = None
                        
                        # Validate mode
                        if mode not in ['FLIGHT', 'TRAIN', 'GROUND']:
                            issues.append(f"Unknown transport mode: {mode}")
                        
                        # Get distance
                        distance_km = None
                        if origin and destination:
                            distance_km = AIRPORT_DISTANCES.get((origin, destination))
                            if not distance_km:
                                issues.append(f"Distance not found for {origin}-{destination}")
                        else:
                            issues.append(f"Missing origin or destination airport codes")
                        
                        # Simple emission estimate (kg CO2e per km)
                        # Flight: 0.255 kg CO2e/km (economy avg)
                        # Train: 0.041 kg CO2e/km
                        # Ground: 0.120 kg CO2e/km
                        emission_factors = {
                            'FLIGHT': 0.255,
                            'TRAIN': 0.041,
                            'GROUND': 0.120,
                        }
                        
                        original_value = distance_km  # Store original distance
                        normalized_value = None
                        
                        if distance_km and mode in emission_factors:
                            normalized_value = distance_km * emission_factors[mode]
                        
                        # Scope 3 (Value Chain - Business Travel)
                        scope = 3
                        category = f"Air Travel - {cabin}" if mode == 'FLIGHT' else f"{mode} Travel"
                        
                        record = {
                            'tenant_id': tenant_id,
                            'scope': scope,
                            'category': category,
                            'activity_date': activity_date,
                            'original_value': original_value,
                            'original_unit': 'km',
                            'normalized_value': normalized_value,
                            'normalized_unit': 'kgCO2e',
                            'status': 'FLAGGED' if issues else 'PENDING',
                            'raw_payload': {
                                'trip_id': trip_id,
                                'employee_id': employee_id,
                                'segment_index': seg_idx,
                                'mode': mode,
                                'origin_airport': origin,
                                'destination_airport': destination,
                                'cabin_class': cabin,
                                'departure_time': departure_str,
                            },
                            'issues': issues,
                        }
                        
                        if issues:
                            flagged_records.append(record)
                        else:
                            successful_records.append(record)
                    
                    except Exception as e:
                        logger.error(f"Travel segment {seg_idx} parsing error: {str(e)}")
                        flagged_records.append({
                            'tenant_id': tenant_id,
                            'raw_payload': {
                                'trip_id': trip_id,
                                'segment_index': seg_idx,
                                **segment,
                            },
                            'status': 'FLAGGED',
                            'issues': [f"Critical segment parsing error: {str(e)}"],
                        })
            
            except Exception as e:
                logger.error(f"Travel trip {trip_idx} parsing error: {str(e)}")
                flagged_records.append({
                    'tenant_id': tenant_id,
                    'raw_payload': trip,
                    'status': 'FLAGGED',
                    'issues': [f"Critical trip parsing error: {str(e)}"],
                })
    
    except json.JSONDecodeError as e:
        logger.error(f"Travel API JSON decode error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Travel API file parsing failed: {str(e)}")
        raise
    
    return successful_records, flagged_records


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _infer_fuel_category(product_name: str) -> str:
    """
    Infer fuel category from SAP product name (MAKTX).
    
    Args:
        product_name: The product name from SAP
        
    Returns:
        Categorized fuel type
    """
    product_lower = product_name.lower() if product_name else ''
    
    if 'diesel' in product_lower or 'dieselkraftstoff' in product_lower:
        return 'Diesel Fuel'
    elif 'unleaded' in product_lower or 'gas' in product_lower:
        return 'Gasoline'
    elif 'adblue' in product_lower or 'def' in product_lower:
        return 'Diesel Exhaust Fluid'
    elif 'hydraulic' in product_lower:
        return 'Hydraulic Fluid'
    elif 'compressor' in product_lower or 'oil' in product_lower:
        return 'Industrial Oil'
    elif 'brake' in product_lower:
        return 'Brake Fluid'
    else:
        return 'Fuel - Other'


# ============================================================================
# EXPORT PARSER REGISTRY
# ============================================================================

PARSER_REGISTRY = {
    'SAP': parse_sap_csv,
    'UTILITY': parse_utility_csv,
    'TRAVEL': parse_travel_json,
}
