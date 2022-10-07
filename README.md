# GPPC (Gold Piece Price Checker) 

Check OSRS Grand Exchange prices from the command line. 
Includes limited module functionality.

# Usage

Installation
```bash
$ pip install gppc
```
Get the price and recent 24h change of many different Grand Exchange items.
```bash
$ gppc 'gold bar' coal
$ gppc gold_bar coal
```
![Image](https://raw.githubusercontent.com/moxxos/gppc/main/gppc_example.jpg)

Import as a module
```bash
$ import gppc
$ gppc.search('coal')
```

# Updates
## [CHANGELOG](https://raw.githubusercontent.com/moxxos/gppc/main/CHANGELOG.md)

### TODO
- [ ] Add option for a full version showing all item data
- [ ] Add option to disable images
- [ ] Add compact version with no images and smaller vertical display
- [ ] Add some caching for images and other static item data
- [ ] Add tests and documentation