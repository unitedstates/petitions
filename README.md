# Petitions

These Python scripts retrieve open petitions on the [We The People](https://petitions.whitehouse.gov/petitions) and scan Twitter for mentions of petitions not yet on the site.

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