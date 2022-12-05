# GPPC (Gold Piece Price Checker) 

Check OSRS Grand Exchange prices from the command line. 
Includes module functionality.

# Usage

### Installation

```bash
$ pip install gppc
```

```bash 
$ git clone https://github.com/moxxos/gppc.git
$ cd gppc
$ pip install .
```

### Get the price and recent 24h change of many different Grand Exchange items.

```bash
$ gppc 'gold bar' coal
$ gppc gold_bar coal
```
![Image](https://raw.githubusercontent.com/moxxos/gppc/main/gppc_example.jpg)

### Import as a module

```python
>>> import gppc
>>> gppc.search('coal')
```

## New Feature
### Create item instances to check item recent history.


```python
>>> from gppc import Item
>>> coal = Item('coal')
>>> coal.recent_historical
           Price Average    Volume
Date           
2022-06-09   161     160  46780917
2022-06-10   164     160  13746833
2022-06-11   164     160  44698810
...          ...     ...       ...
2022-12-02   171     163  24461683
2022-12-03   174     163  43027137
2022-12-04   173     163  25469205
[179 rows x 3 columns]
```
### Save multiple item histories for future use.
```python
>>> coal.save_historical()
SAVED ITEM: Coal, id: 453
179 NEW DATES CREATED
179 RECORDS UPDATED

>>> bond.save_historical()
SAVED ITEM: Old school bond, id: 13190
179 RECORDS UPDATED
```
### Check item full history at a later date if past history is saved.
```python
>>> coal.full_historical
           Price Average    Volume
Date           
2022-06-09   161     160  46780917
2022-06-10   164     160  13746833
2022-06-11   164     160  44698810
...          ...     ...       ...
2023-12-02   171     163  24461683
2023-12-03   174     163  43027137
2023-12-04   173     163  25469205
[544 rows x 3 columns]
```

# Updates

## [CHANGELOG](https://github.com/moxxos/gppc/blob/main/CHANGELOG.md)

#### TODO
- [ ] Finish command line display
- [ ] Add tests and documentation