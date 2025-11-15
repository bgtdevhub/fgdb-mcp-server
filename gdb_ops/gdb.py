from __future__ import annotations
from collections.abc import Iterator
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import os
try:
    import arcpy  # type: ignore
    ARCPY_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    ARCPY_AVAILABLE = False


@dataclass
class FileGDBBackend:
    gdb_path: str
    def __init__(self,gdb_path):
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for GDB operations in this build")
        self.gdb_path = gdb_path

    def _set_workspace(self) -> None:
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for GDB operations in this build")
        arcpy.env.workspace = self.gdb_path

    def list_all_feature_classes(self) -> List[str]:
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for GDB listing in this build")
        self._set_workspace()
        walk = arcpy.da.Walk(self.gdb_path, datatype="FeatureClass")
        fc_list = [
            os.path.join(root, feature_class)
            for root, data_sets, feature_classes in walk
            for feature_class in feature_classes
        ] 
        return [fc.split(".gdb")[1][1:] for fc in fc_list or []]
   
        
    def describe(self, dataset: str) -> Dict[str, Any]:
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for describe in this build")
        self._set_workspace()
        desc = arcpy.Describe(dataset)
        fields = []
        for f in arcpy.ListFields(dataset) or []:
            fields.append({
                "name": f.name,
                "type": f.type,
                "length": getattr(f, "length", None),
                "nullable": getattr(f, "isNullable", None),
            })
        return {
            "name": getattr(desc, "name", dataset),
            "datasetType": getattr(desc, "datasetType", None),
            "shapeType": getattr(desc, "shapeType", None),
            "spatialReference": getattr(getattr(desc, "spatialReference", None), "name", None),
            "fields": fields,
        }

    def select(self, dataset: str, where = None, fields =[], limit=50000) -> Dict[Dict[str, Any]]:
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for select in this build")
        self._set_workspace()
        total_count = self.count(dataset)
        if total_count < limit:
            limit = total_count
        fields_list = [f.name for f in arcpy.ListFields(dataset)]
        if len(fields):
            valid_fields = set(fields).intersection(set(fields_list))
            if len(fields) > len(valid_fields):
                invalid = set(fields) - valid_fields
                raise ValueError(f"Invalid fields: {invalid}. Available fields: {fields_list}")
            fields_list = list(valid_fields)
        result = []
        limiter = 0
        with arcpy.da.SearchCursor(dataset, fields_list, where_clause=where) as cursor:
            for row in cursor:
                limiter +=1;
                # yield dict(zip(fields_list, row))
                if limiter > limit:
                    break
                result.append(dict(zip(fields_list,row)))
        hasMore = False
        if total_count > limiter:
            hasMore = True
        return {"data":result,"hasMore":hasMore}
    
    def select_by_geometry(self, dataset: str, overlap_type: str, selection_type: str, output_layer: str = None) -> int:
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for select_by_geometry in this build")
        self._set_workspace()
        datalayer = f"memory\\datasetLayer_{str(uuid.uuid4()).replace('-', '')[0:5]}"
        arcpy.management.MakeFeatureLayer(dataset, datalayer)
        # Select by location
        result = arcpy.management.SelectLayerByLocation(
            in_layer=datalayer,
            overlap_type=f"{overlap_type}",
            select_features=f"{dataset}",
            selection_type=f"{selection_type}"
        ).getOutput(0)
        # See how many features were selected
        count = int(arcpy.management.GetCount(result)[0])
        #Save them
        if output_layer is not None:
            part = arcpy.management.CopyFeatures(result, output_layer)[0]
        if arcpy.Exists(datalayer):
            arcpy.management.Delete(datalayer)
        return count


    def count(self, dataset: str, where: Optional[str] = None) -> int:
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for count in this build")
        self._set_workspace()
        return int(arcpy.management.GetCount(dataset)[0])

    def insert(self, dataset: str, rows:int, fields:list[str], values:list[str]) -> int:
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for insert in this build")
        self._set_workspace()
        field_list = [f.name for f in arcpy.ListFields(dataset) if f.type not in {"OID"}]
        
        # Get field information for type conversion and required fields
        all_fields = {f.name: f for f in arcpy.ListFields(dataset)}
        
        # Check if this is a feature class
        desc = arcpy.Describe(dataset)
        is_feature_class = hasattr(desc, "shapeType") and desc.shapeType is not None
        
        # Build complete field list with required fields and Shape if needed
        fields_dict = dict(zip(fields, values))
        complete_fields = []
        complete_values = []
        
        # Add Shape field first if it's a feature class and not already included
        if is_feature_class and "Shape" in field_list:
            if "Shape" not in fields_dict:
                complete_fields.append("Shape")
                complete_values.append(None)  # Will create geometry later
            else:
                complete_fields.append("Shape")
                complete_values.append(fields_dict["Shape"])
        
        # Add user-specified fields
        for field_name in fields:
            if field_name == "Shape":
                continue  # Already handled above
            if field_name in field_list:
                complete_fields.append(field_name)
                complete_values.append(fields_dict[field_name])
        
        # Add required fields that are missing
        for field_name in field_list:
            if field_name == "Shape":
                continue  # Already handled above
            if field_name not in complete_fields:
                field = all_fields[field_name]
                if not getattr(field, "isNullable", True):
                    # Required field not provided - add dummy value
                    complete_fields.append(field_name)
                    if field.type in ["Integer", "SmallInteger", "OID"]:
                        complete_values.append(0)
                    elif field.type in ["Double", "Single", "Float"]:
                        complete_values.append(0.0)
                    elif field.type == "String":
                        complete_values.append("")
                    elif field.type == "Date":
                        complete_values.append(None)
                    else:
                        complete_values.append(None)
        
        # Convert values to appropriate types and create geometry
        converted_values = []
        for i, field_name in enumerate(complete_fields):
            if field_name not in all_fields:
                converted_values.append(None)
                continue
                
            field = all_fields[field_name]
            val = complete_values[i]
            
            # Handle Shape/Geometry field
            if field.type == "Geometry" or field_name == "Shape":
                if val is None or val == "":
                    # Create a simple dummy polygon
                    array = arcpy.Array([
                        arcpy.Point(0.0, 0.0),
                        arcpy.Point(0.001, 0.0),
                        arcpy.Point(0.001, 0.001),
                        arcpy.Point(0.0, 0.001),
                        arcpy.Point(0.0, 0.0)  # Close polygon
                    ])
                    converted_values.append(arcpy.Polygon(array))
                else:
                    converted_values.append(val)
            # Handle numeric types
            elif field.type in ["Integer", "SmallInteger", "OID"]:
                try:
                    converted_values.append(int(val) if val is not None and str(val).lower() not in ["null", ""] else None)
                except (ValueError, TypeError):
                    converted_values.append(0 if not getattr(field, "isNullable", True) else None)
            elif field.type in ["Double", "Single", "Float"]:
                try:
                    converted_values.append(float(val) if val is not None and str(val).lower() not in ["null", ""] else None)
                except (ValueError, TypeError):
                    converted_values.append(0.0 if not getattr(field, "isNullable", True) else None)
            # Handle date types
            elif field.type == "Date":
                converted_values.append(val)  # Keep as-is, arcpy will handle conversion
            # Handle string types
            else:
                converted_values.append(str(val) if val is not None and str(val).lower() != "null" else ("" if not getattr(field, "isNullable", True) else None))
        
        if set(complete_fields).intersection(set(field_list)):
            with arcpy.da.InsertCursor(dataset, complete_fields) as cursor:
                count = 0
                while rows > count:
                    cursor.insertRow(converted_values)
                    count += 1
        return count

    def update(self, dataset: str, updates: Dict[str, Any], where: Optional[str] = None) -> int:
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for update in this build")
        self._set_workspace()
        fields = list(updates.keys())
        oid_field = arcpy.Describe(dataset).OIDFieldName
        with arcpy.da.UpdateCursor(dataset, fields + [oid_field], where_clause=where) as cursor:
            count = 0
            for row in cursor:
                for i, f in enumerate(fields):
                    row[i] = updates[f]
                cursor.updateRow(row)
                count += 1
        return count

    def delete(self, dataset: str, where: Optional[str] = None) -> int:
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for delete in this build")
        self._set_workspace()
        oid_field = arcpy.Describe(dataset).OIDFieldName
        with arcpy.da.UpdateCursor(dataset, [oid_field], where_clause=where) as cursor:
            count = 0
            for _ in cursor:
                cursor.deleteRow()
                count += 1
        return count

    def add_field(self, dataset: str, name: str, field_type: str, length: Optional[int] = None) -> None:
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for add_field in this build")
        self._set_workspace()
        arcpy.management.AddField(dataset, name, field_type, field_length=length)

    def delete_field(self, dataset: str, name: str) -> None:
        if not ARCPY_AVAILABLE:
            raise RuntimeError("ArcPy is required for delete_field in this build")
        self._set_workspace()
        arcpy.management.DeleteField(dataset, name)
