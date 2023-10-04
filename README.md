# GPPC (Gold Piece Price Checker) 

Check OSRS Grand Exchange prices from the command line. Includes module functionality to check full price history of an item.
Features caching capability to save item price histories for future use.

# Usage

### Installation

```bash
$ pip install gppc
```
### or
```bash 
$ git clone https://github.com/moxxos/gppc.git
$ cd gppc
$ pip install .
```

### Get the price and recent 24h change of many different items on the OSRS Grand Exchange straight from the command line.

```bash
$ gppc 'gold bar' coal
$ gppc gold_bar coal
```
![Image](https://raw.githubusercontent.com/moxxos/gppc/main/gppc_example.jpg)

### Import as a module.

```python
>>> import gppc
>>> gppc.search('coal')
```


### Create item instances to check item price and volume history. 4 different intervals available.


```python
>>> from gppc import Item
>>> coal = Item('coal')
```
### Past 1 day history at 5-minute intervals.
```
>>> coal.history_1day
              timestamp  avgHighPrice  avgLowPrice  highPriceVolume  lowPriceVolume
0   2023-09-20 04:15:00         276.0          264            18195           31276
1   2023-09-20 04:20:00         289.0          265             7124           82582
2   2023-09-20 04:25:00         278.0          262            18889           80672
..                  ...           ...          ...              ...             ...
362 2023-09-21 11:20:00         256.0          244            26604           89559
363 2023-09-21 11:25:00         256.0          243            42930          194245
364 2023-09-21 11:30:00         256.0          244            22929           66926

[365 rows x 5 columns]
```
### Past 1 year history at 1-day intervals.
```
>>> coal.history_1year
              timestamp  avgHighPrice  avgLowPrice  highPriceVolume  lowPriceVolume
0   2022-09-20 20:00:00           144          142          7290293         8857481
1   2022-09-21 20:00:00           144          143          5821183         8728784
2   2022-09-22 20:00:00           147          145          5148730         9724897
..                  ...           ...          ...              ...             ...
362 2023-09-17 20:00:00           221          217          8200818        14460078
363 2023-09-18 20:00:00           243          236          8815340        20995587
364 2023-09-19 20:00:00           236          235          8746294        17259336

[365 rows x 5 columns]
```
### Two other intervals available for 2 week and 3 month histories.
```
>>> hist_2week = coal.history_2week
>>> hist_3month = coal.history_3month
```
### Save multiple item histories for future use depending on which histories you have accessed.
```
>>> coal_hist_1d = coal.history_1day
>>> coal_hist_2w = coal.history_2week
>>> coal_hist_3m = coal.history_3month
>>> coal_hist_1y = coal.history_1year
>>> coal.save_history()
1281 new records added for item: Coal

>>> bond_hist_1y = bond.history_1year
>>> bond.save_history()
365 new records added for item: Old school bond
```
### Check item full history if past history is saved.
```
>>> coal.full_history
               timestamp  avgHighPrice  avgLowPrice  highPriceVolume  lowPriceVolume
0    2022-09-20 20:00:00         144.0          142          7290293         8857481
1    2022-09-21 20:00:00         144.0          143          5821183         8728784
2    2022-09-22 20:00:00         147.0          145          5148730         9724897
...                  ...           ...          ...              ...             ...
1278 2023-09-21 18:20:00         253.0          245             2090           47719
1279 2023-09-21 18:25:00         252.0          245            11647           70886
1280 2023-09-21 18:30:00         246.0          244            20901           49703

[1281 rows x 5 columns]
```
### Create catalogs to easily manipulate lists of items.
```python
>>> from gppc import Catalog
>>> ores = Catalog('copper ore', 'tin ore', 'iron ore', 'gold ore', 'silver ore', 'mithril ore', 'adamantite ore', 'runite ore')
>>> ores.sort()
>>> ores
['Adamantite ore', 'Copper ore', 'Gold ore', 'Iron ore', 'Mithril ore', 'Runite ore', 'Silver ore', 'Tin ore']
>>> ores.remove('Gold ore')
>>> ores
['Adamantite ore', 'Copper ore', 'Iron ore', 'Mithril ore', 'Runite ore', 'Silver ore', 'Tin ore']
```
### Save the history of all items in your catalog.
```
>>> ores.save_history('1day')
365 new records added for item: Adamantite ore
365 new records added for item: Copper ore
365 new records added for item: Iron ore
365 new records added for item: Mithril ore
365 new records added for item: Runite ore
365 new records added for item: Silver ore
365 new records added for item: Tin ore
```
### A catalog with no arguments creates a full list of all items in the Grand Exchange.
```python
>>> all_items = Catalog()
>>> len(all_items)
4005
```

# Updates

## [CHANGELOG](https://github.com/moxxos/gppc/blob/main/CHANGELOG.md)

# TODO
- [ ] Finish command line display
- [ ] Add tests and documentation