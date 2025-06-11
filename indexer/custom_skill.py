from typing import List
from azure.search.documents.indexes.models import SearchIndexerSkillset, SearchIndexerSkill, WebApiSkill
from customskillOutputMapping import OutputMapping as outputFieldsMapping
import os
def get_custom_skillset() -> SearchIndexerSkillset:
    skillset_name = os.getenv("AZURE_SEARCH_SKILLSET_NAME")
    OutputFields = outputFieldsMapping()
    skills: List[SearchIndexerSkill] = [
        WebApiSkill(
            name="parse-xml-skill",
            description="Calls Azure Function to parse XML content",
            uri=os.getenv("CUSTOM_SKILLSET_URL"),
            http_method="POST",
            timeout="PT30S",
            batch_size=1,
            context="/document",
            inputs=[{"name": "document", "source": "/document/content"}],
        )
    ]

    skillset = SearchIndexerSkillset(
        name=skillset_name,
        description="Skillset with custom XML parsing skill",
        skills=skills,
        cognitive_services=None
    )
    return skillset
