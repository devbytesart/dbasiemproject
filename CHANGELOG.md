<!-- 
Copyright 2026 ttdantett DevBytesArt®

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: ttdantett
Title: SIEM PROJECT
DOCUMENT: changelog
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Format versioning 
X.X.X
Major.Minor.Patch

**Major** - Changes that have major impact on the application such as indexing, authentication methods, ... 
**Minor** - Changes that have a negligeable impact on the application such as add new features, changing configuration values...
**Patch** - Security or bug fixed on the application

---
## [01.003.002] - YYYY-MM-DD

### Added

- Layout increase/decrease menu and formular

### Changed

- Suggestions command: change color code for mandatory parameters on the suggestions commands parameters.

### Fixed

- Troubleshoot rules creations
- Langage errors
- Troubleshoot export in search page

### Security


---


## [01.002.002] - 2026-08-09

### Added

- Add limit operation on ISM
- Create Import and Export button
- SlaveCoordinator restart the docker that are deleted
- Documentation on upgrade
- Improvement of documentation for search operations

### Changed

- Modify icon for standardize buttons on all pages
- Use tagsystem on search page

### Fixed

- Display on search page and dashboard, soar tables order correctly
- Troubleshoot soar siem functions (save log, ...) due to change order of instance in the parameters of siem_search function
- Suggestions are displayed correctly in search view
- SOAR reporting display url

### Security

--- 

## [01.001.001] - 2026-07-18

Realease note version 01.001.001

### Added

- Add logs info and warnings for monitoring on components
- Add disabled buttons play, stop and replay for playbook part
- Add trademarks DevBytesArt on all pages 

### Changed

- Move Operations in another folder src/Operations/
- Vault key deletion commands added
- change method of storing context for soar (cache now)
- Change vault to get the model and complete url on the key and not in the command itself.
- Change dashboard/report way to load and save
- Set by default the technology for dashboard/edition and soar page

### Fixed

- Monitoring troubleshooted for slavecoordinator,mastercoordinator, logparser, cachesystem, userinterface, dedicatedindexsearchmotor, indexsearchmotor
- Troubleshoot error in DISM for Decimal value

### Security

- Check permissions userinterface, index and tenant to save and refresh dashboard and report
- Check permissions users right to access privileges and global configuration

---

## [01.000.000] - 2026-07-13

This is the first official stable release of the application!

### Added

**Beta version** of DBASP

### Changed

**None yet**

### Fixed

**None yet**

### Security

**None yet**

---