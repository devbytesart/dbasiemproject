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

## [01.001.001] - 2026-xx-xx

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

This is the first official stable release (Production Ready) of the application!

### Added

**Beta version** of DBASP

### Changed

**None yet**

### Fixed

**None yet**

### Security

**None yet**

---