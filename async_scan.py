import asyncio
import aiohttp
from aiohttp import ClientSession
from Wappalyzer import Wappalyzer, WebPage
import pandas as pd
from bs4 import BeautifulSoup

async def fetch_technologies(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                webpage = WebPage.new_from_url(url)
                wappalyzer = Wappalyzer.latest()
                technologies = wappalyzer.analyze_with_versions_and_categories(webpage)              
                version = ", ".join(f"{tech}: {version}" for tech, version in technologies.items())
                soup = BeautifulSoup(html, "html.parser")
                title = soup.title.string if soup.title else ""
                # Retrieve content length and server name from response headers
                content_length = response.headers.get('Content-Length')
                server_name = response.headers.get('Server')
                return response.status, title, content_length, server_name, version
            else:
                return response.status, "", "", "", ""  # Add default values for missing elements
    except aiohttp.ClientError:
        return None, "", "", "", ""  # Add default values for missing elements

async def process_domains(domains):
    async with ClientSession() as session:
        tasks = []
        for domain in domains:
            url = f"http://{domain}"
            task = asyncio.ensure_future(fetch_technologies(session, url))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results

def main():
    # Read domains from Excel file
    excel_file = "domains.xlsx"
    df = pd.read_excel(excel_file)
    domains = df["Domain"].tolist()

    # Perform web technology detection
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(process_domains(domains))

    # Write results to an output Excel file
    status_codes, titles, content_length, server_name, version = zip(*results)
    output_df = pd.DataFrame({
        "Domain": domains,
        "Status Code": status_codes,
        "Title": titles,
        # "Technologies": [", ".join(tech) for tech in technologies],
        "Content-Length" : content_length,
        "Server" : server_name,
        "Technology and Versions" : version,
    })
    output_df.to_excel("scan_1.xlsx", index=False)

if __name__ == "__main__":
    main()