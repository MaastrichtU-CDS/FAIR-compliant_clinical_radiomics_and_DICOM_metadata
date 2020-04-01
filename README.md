# FAIR Compliant Clinical Radiomics And DICOM Metadata

This code repository accompanies a Medicaal Physics Dataset Article titled
"FAIR-compliant clinical, radiomics and DICOM metadata of public collections
on The Cancer Imaging Archive (TCIA)" (doi to follow, link to follow).

## Purpose
One of the most frequently cited radiomics investigations showed that
features automatically extracted from routine clinical images could be used in
prognostic modelling. These images have been made publicly accessible via The
Cancer Imaging Archive (TCIA). There have been numerous requests for additional
explanatory metadata on the following datasets – RIDER, Interobserver, Lung1
and Head-Neck1. To support repeatability, reproducibility, generalizability and
transparency in radiomics research, we publish the subjects’ clinical data,
extracted radiomics features and Digital Imaging and Communications in Medicine
(DICOM) headers of these four datasets with descriptive metadata, in order to
be more compliant with findable, accessible, interoperable and re-usable (FAIR)
data management principles.


## Acquisition and validation methods
Overall survival time intervals were updated using a national citizens registry
after internal ethics board approval. Spatial offsets of the Primary Gross Tumor
Volume (GTV) regions of interest (ROIs) associated with the Lung1 CT series were
improved on the TCIA. GTV radiomics features were extracted using the open-source
ontology-guided radiomics workflow (O-RAW). We reshaped the output of O-RAW to
map features and extraction settings to the latest version of Radiomics Ontology,
so as to be consistent with the Image Biomarker Standardization Initiative (IBSI).
DICOM metadata was extracted using a research version of Semantic DICOM
(SOHARD, GmbH, Fuerth; Germany). Subjects’ clinical data was described with
metadata using the Radiation Oncology Ontology. All of the above were published
in Resource Descriptor Format (RDF), i.e. triples. Example SPARQL queries are
shared with the reader to use on the online triples archive, which are intended
to illustrate how to exploit this data submission.

## Data format
The accumulated RDF data is publicly accessible through a SPARQL endpoint where
the triples are archived. The endpoint is remotely queried through a graph
database web application at http://sparql.cancerdata.org. SPARQL queries are
intrinsically federated, such that we can efficiently cross-reference clinical,
DICOM and radiomics data within a single query, while being agnostic to the
original data format and coding system. The federated queries work in the same
way even if the RDF data were partitioned across multiple servers and dispersed
physical locations. Potential applications: The public availability of these
data resources is intended to support radiomics features replication,
repeatability and reproducibility studies by the academic community. The
example SPARQL queries may be freely used and modified by readers depending
on their research question. Data interoperability and reusability is supported
by referencing existing public ontologies. The RDF data is readily findable and
accessible through the aforementioned link. Scripts used to create the RDF are
made available through this repository.

## Contents of this repository

### Clinical data mappings folder
Our proposed mappings for the clinical data elements, e.g. age, gender, survival
time etc., to the Radiation Oncology Ontology (ROO) are provided in this folder.
Usage is as described in the manuscript text; the mapping file (.ttl) needs to be
processed in an RDF serialization application, e.g. R2RML (https://www.w3.org/TR/r2rml/)
to produce the triples.

### Radiomics folder
In this folder, 
