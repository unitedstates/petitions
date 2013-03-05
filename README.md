# Petitions

These Python scripts retrieve open petitions on the [We The People](https://petitions.whitehouse.gov/petitions) and scan Twitter for mentions of petitions not yet on the site.

There are two means of retrieving the petitions: Scraping the site directly (the old way) or using the White House API (the new way, in active development).

## Quick setup

It's recommended to make a virtualenv, then run:

```bash
pip install -r requirements.txt
```

## Running

### petitions.py
Options:

`--max`: maximum number of petitions to retrieve, in the order the appear on the White House site. Default is all of them

`--start`: Which page to beginning collecting from. Petitions are paginated 20 to a page. Useful if the script is interrupted. Default is 1

Example:

```bash
./scripts/petitions.py --max=10 --start=2
```

### twitter.py
Options:

`--start`: Which page of Twitter search results to beginning collecting from. Tweets matching your query are paginated 100 to a page. Default is 1

`--max`: maximum number of pages to retrieve, default is 10. 

`--query`: phrase to submit to Twitter search. Use '+' for spaces. Default is "whitehouse+petition"

Example:

```bash
./scripts/twitter.py --query=obama+petition --start=1 --max=5 
```

### whitehouse.py
Options:

The first cli argument is the task to perform: "petitions" to get petitions from API and "signatures" to get signatures

#### petitions
Retrieves petitions from the API in the order provided from the White House

+ `--max`: maximum number of petitions to retrieve. Default is all active petitions (typically less than 500 total)
+ `--start`: The number of petitions offset from the most recent. Useful if the script is interrupted. Default is 0

#### signatures
Retrieves signatures for the petitions found in ```data/api/petitions```. It's necessary to split these steps giving the long about of time this step takes.

+ `--max`: maximum number of petitions for which to retrieve signatures. Default is all petitions in the directory
+ `--start`: The number of petitions offset from the first petition in the directory. Useful if the script is interrupted. Default is 0

Examples:

```bash
./scripts/whitehouse.py petitions --max=100 --start=50
```

```bash
./scripts/whitehouse.py signatures --max=10 --start=5
```
