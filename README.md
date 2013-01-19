petitions
=========

This Python scripts retrieves every open petition on the We The People site, found at https://petitions.whitehouse.gov/petitions

Options:

--max: maximum number of petitions to retrieve, in the order the appear on the White House site. Default is all of them

--start: Which page to beginning collecting from. Petitions are paginated 20 to a page. Useful if the script is interrupted. Default is 1

Example:

    python petitions.py --max=10 --start=2

Coming soon:
 * Search twitter for petitions that have not yet reached the 150-signature threshold