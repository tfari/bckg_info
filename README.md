### bckg_info.py 

Following background research recommendations on Richard Lawson's book ["Web Scraping with Python"](https://www.amazon.com/Scraping-Community-Experience-Distilled-English-ebook/dp/B00YSIL1XK), 
this script generates an .html report on any given domain, and then automatically opens it on the default browser.

![](https://github.com/tfari/bckg_info/blob/master/screenshot.jpg)

**Collects the following information**:
* URL
* IP
* TITLE
* ESTIMATED SIZE
* POTENTIAL API
* LINK TO LATEST NEWS
* WHOIS INFORMATION
* WHOIS-DATA BASED GOOGLE MAPS IMAGE AND LINK
* GEOLOCATION INFORMATION
* GEOLOCATION-DATA BASED GOOGLE MAPS IMAGE AND LINK
* BUILTWITH INFORMATION
* ROBOTS.TXT INFORMATION
* SITEMAP
* WIKIPAGE

**Usage:**
```
    python bckg_info.py URL | FILEPATH
```
The FILEPATH optional parameter is passed to determine a specific path we want to save the .html report to.
It defaults to ./output.

**Example:**

```
    python bckg_info.py example.org
    python bckg_info.py example.org My/Prefered/Path

```
 
