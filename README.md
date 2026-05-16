# TSKG
Change `TOKEN_AUTH` in `matomo_ontology_status.py` to be able to extract data from matomo. Configure matomo statistics data with further parameters in the file.
Choose the ontologies based on their minimum number of actions by the command line parameter `matomo_ontology_status.py --min_actions`

Run the application by `docker compose up -d`

Run the UI of the SPARQL endpoint from: http://localhost:8176/TS
