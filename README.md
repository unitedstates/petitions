# Petitions

This Python script retrieves every open petition on the [We The People](https://petitions.whitehouse.gov/petitions).

## Quick setup

It's recommended to make a virtualenv, then run:

```bash
pip install -r requirements.txt
```

## Running

Options:

--max: maximum number of petitions to retrieve, in the order the appear on the White House site. Default is all of them

--start: Which page to beginning collecting from. Petitions are paginated 20 to a page. Useful if the script is interrupted. Default is 1

Example:

```bash
./scripts/petitions.py --max=10 --start=2
```

## Coming soon

* Search Twitter for petitions that have not yet reached the 150-signature threshold