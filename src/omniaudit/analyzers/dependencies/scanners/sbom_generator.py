"""
SBOM Generator Module

Generates Software Bill of Materials in SPDX and CycloneDX formats.
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from xml.etree import ElementTree as ET
from xml.dom import minidom

from ..types import Dependency, SBOM, SBOMFormat


class SBOMGenerator:
    """
    Generates Software Bill of Materials (SBOM).

    Supports:
    - SPDX 2.3 (JSON and XML)
    - CycloneDX 1.4 (JSON and XML)
    """

    def __init__(self, project_name: str, project_version: str = "1.0.0"):
        """
        Initialize SBOM generator.

        Args:
            project_name: Name of the project
            project_version: Version of the project
        """
        self.project_name = project_name
        self.project_version = project_version

    def generate(
        self, dependencies: List[Dependency], format: SBOMFormat = SBOMFormat.SPDX_JSON
    ) -> SBOM:
        """
        Generate SBOM in specified format.

        Args:
            dependencies: List of dependencies
            format: SBOM format to generate

        Returns:
            SBOM object
        """
        if format == SBOMFormat.SPDX_JSON:
            components = self._generate_spdx_json(dependencies)
            spec_version = "SPDX-2.3"
        elif format == SBOMFormat.SPDX_XML:
            components = self._generate_spdx_xml(dependencies)
            spec_version = "SPDX-2.3"
        elif format == SBOMFormat.CYCLONEDX_JSON:
            components = self._generate_cyclonedx_json(dependencies)
            spec_version = "1.4"
        elif format == SBOMFormat.CYCLONEDX_XML:
            components = self._generate_cyclonedx_xml(dependencies)
            spec_version = "1.4"
        else:
            raise ValueError(f"Unsupported SBOM format: {format}")

        return SBOM(
            format=format,
            spec_version=spec_version,
            created=datetime.utcnow(),
            creator="OmniAudit",
            components=components,
            metadata={
                "project_name": self.project_name,
                "project_version": self.project_version,
                "total_dependencies": len(dependencies),
            },
        )

    def _generate_spdx_json(self, dependencies: List[Dependency]) -> List[Dict[str, Any]]:
        """Generate SPDX 2.3 JSON format."""
        packages = []

        for dep in dependencies:
            package = {
                "SPDXID": f"SPDXRef-Package-{dep.name}-{dep.version}",
                "name": dep.name,
                "versionInfo": dep.version,
                "downloadLocation": dep.repository or "NOASSERTION",
                "filesAnalyzed": False,
                "homepage": dep.homepage or "NOASSERTION",
                "licenseConcluded": dep.license or "NOASSERTION",
                "licenseDeclared": dep.license or "NOASSERTION",
                "copyrightText": "NOASSERTION",
                "summary": dep.description or "",
                "externalRefs": [],
            }

            # Add package manager reference
            package["externalRefs"].append(
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": dep.package_manager.value,
                    "referenceLocator": f"{dep.name}@{dep.version}",
                }
            )

            packages.append(package)

        return packages

    def _generate_spdx_xml(self, dependencies: List[Dependency]) -> List[Dict[str, Any]]:
        """Generate SPDX 2.3 XML format."""
        # For XML, we return a structure that can be serialized
        # Similar to JSON but will be converted to XML
        return self._generate_spdx_json(dependencies)

    def _generate_cyclonedx_json(self, dependencies: List[Dependency]) -> List[Dict[str, Any]]:
        """Generate CycloneDX 1.4 JSON format."""
        components = []

        for dep in dependencies:
            component = {
                "type": "library",
                "bom-ref": f"{dep.package_manager.value}//{dep.name}@{dep.version}",
                "name": dep.name,
                "version": dep.version,
                "description": dep.description or "",
                "scope": "optional" if dep.is_dev else "required",
                "licenses": [],
                "purl": self._generate_purl(dep),
                "externalReferences": [],
            }

            # Add license
            if dep.license:
                component["licenses"].append({"license": {"id": dep.license}})

            # Add external references
            if dep.homepage:
                component["externalReferences"].append(
                    {"type": "website", "url": dep.homepage}
                )

            if dep.repository:
                component["externalReferences"].append({"type": "vcs", "url": dep.repository})

            components.append(component)

        return components

    def _generate_cyclonedx_xml(self, dependencies: List[Dependency]) -> List[Dict[str, Any]]:
        """Generate CycloneDX 1.4 XML format."""
        # Similar to JSON, return structure that can be serialized
        return self._generate_cyclonedx_json(dependencies)

    def _generate_purl(self, dependency: Dependency) -> str:
        """
        Generate Package URL (purl) for dependency.

        Args:
            dependency: Dependency object

        Returns:
            Package URL string
        """
        # Map package manager to purl type
        purl_types = {
            "npm": "npm",
            "yarn": "npm",
            "pnpm": "npm",
            "pip": "pypi",
            "poetry": "pypi",
            "cargo": "cargo",
            "go": "golang",
            "maven": "maven",
            "gradle": "maven",
            "composer": "composer",
            "bundler": "gem",
        }

        purl_type = purl_types.get(dependency.package_manager.value, "generic")

        # Basic purl format: pkg:type/name@version
        return f"pkg:{purl_type}/{dependency.name}@{dependency.version}"

    def export_spdx_json(self, sbom: SBOM) -> str:
        """
        Export SBOM as SPDX JSON string.

        Args:
            sbom: SBOM object

        Returns:
            JSON string
        """
        document = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": self.project_name,
            "documentNamespace": f"https://sbom.omniaudit.dev/{self.project_name}-{uuid.uuid4()}",
            "creationInfo": {
                "created": sbom.created.isoformat() + "Z",
                "creators": [f"Tool: {sbom.creator}"],
                "licenseListVersion": "3.21",
            },
            "packages": sbom.components,
        }

        return json.dumps(document, indent=2)

    def export_cyclonedx_json(self, sbom: SBOM) -> str:
        """
        Export SBOM as CycloneDX JSON string.

        Args:
            sbom: SBOM object

        Returns:
            JSON string
        """
        document = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": sbom.created.isoformat() + "Z",
                "tools": [{"vendor": "OmniAudit", "name": sbom.creator, "version": "1.0.0"}],
                "component": {
                    "type": "application",
                    "name": self.project_name,
                    "version": self.project_version,
                },
            },
            "components": sbom.components,
        }

        return json.dumps(document, indent=2)

    def export_spdx_xml(self, sbom: SBOM) -> str:
        """
        Export SBOM as SPDX XML string.

        Args:
            sbom: SBOM object

        Returns:
            XML string
        """
        root = ET.Element("Document", xmlns="http://spdx.org/rdf/terms#")

        # Add creation info
        creation_info = ET.SubElement(root, "creationInfo")
        ET.SubElement(creation_info, "created").text = sbom.created.isoformat() + "Z"
        ET.SubElement(creation_info, "creators").text = f"Tool: {sbom.creator}"

        # Add packages
        for package in sbom.components:
            pkg_elem = ET.SubElement(root, "Package")
            ET.SubElement(pkg_elem, "name").text = package["name"]
            ET.SubElement(pkg_elem, "versionInfo").text = package["versionInfo"]
            ET.SubElement(pkg_elem, "licenseConcluded").text = package.get(
                "licenseConcluded", "NOASSERTION"
            )

        # Pretty print
        xml_str = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")

    def export_cyclonedx_xml(self, sbom: SBOM) -> str:
        """
        Export SBOM as CycloneDX XML string.

        Args:
            sbom: SBOM object

        Returns:
            XML string
        """
        root = ET.Element(
            "bom",
            xmlns="http://cyclonedx.org/schema/bom/1.4",
            serialNumber=f"urn:uuid:{uuid.uuid4()}",
            version="1",
        )

        # Add metadata
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "timestamp").text = sbom.created.isoformat() + "Z"

        # Add components
        components_elem = ET.SubElement(root, "components")
        for component in sbom.components:
            comp_elem = ET.SubElement(components_elem, "component", type="library")
            ET.SubElement(comp_elem, "name").text = component["name"]
            ET.SubElement(comp_elem, "version").text = component["version"]
            if component.get("description"):
                ET.SubElement(comp_elem, "description").text = component["description"]

        # Pretty print
        xml_str = ET.tostring(root, encoding="unicode")
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")
