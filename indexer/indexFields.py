from azure.search.documents.indexes.models import (
    SimpleField,
    SearchableField,
    ComplexField
)

def getfields():
    fields = [
        SimpleField(name="id", type="Edm.String", key=True, filterable=True, searchable=False),
        SimpleField(name="patient_id", type="Edm.String", filterable=True, facetable=True, sortable=True, searchable=True),
        SimpleField(name="department_name", type="Edm.String", filterable=True, facetable=True, sortable=True, searchable=True),
        SearchableField(name="department_value", type="Edm.String", searchable=True)
    ]
    return fields
