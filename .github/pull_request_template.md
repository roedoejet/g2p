Pull request template for adding a new language
-----------------------------------------------

*Do not use this for other types of pull requests*

* **Please check if the PR fulfills these requirements**
- [ ] Mapping files are added in `g2p/mappings/langs`
- [ ] Mapping is either added to an existing folder or a new folder has been added
- [ ] Language folder and files use appropriate [ISO 639-3 codes](https://en.wikipedia.org/wiki/List_of_ISO_639-3_codes)
- [ ] Config.yaml file includes all author names, and settings necessary
- [ ] Please add some test data in `g2p/tests/public/data`. The added file should be a csv/tsv/psv file and each row should have the format `[input_mapping_code,output_mapping_code,input_string,output_string]`
- [ ] As the last step, G2P has been updated by running `g2p update` locally and committing the change
- [ ] You agree to license your contribution under the same license as this project (see [LICENSE](https://github.com/roedoejet/g2p/blob/master/LICENSE) file).

* **Other information**:
